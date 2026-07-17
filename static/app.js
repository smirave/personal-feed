
    const API = "/api/posts";
    let allPosts = [];
    let activeFilter = 'all';

    // --- View Routing ---
    function switchView(viewId, btn) {
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById(`view-${viewId}`).classList.add('active');
        
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        if(btn) btn.classList.add('active');
        
        window.scrollTo(0, 0);
    }

    // --- Settings Logic ---
    function loadSettings() {
        const color = localStorage.getItem('nx-color') || '#8b5cf6';
        const hover = localStorage.getItem('nx-hover') || '#a78bfa';
        const glow = localStorage.getItem('nx-glow') || '#8b5cf615';
        const font = localStorage.getItem('nx-font') || 'Plus Jakarta Sans';
        const size = localStorage.getItem('nx-size') || '15px';
        const density = localStorage.getItem('nx-density') || '24px';

        setThemeColor(color, hover, glow, true);
        setFont(font, null, true);
        setFontSize(size, true);
        setDensity(density, null, true);
    }

    function setThemeColor(color, hover, glow, isInit) {
        document.documentElement.style.setProperty('--accent', color);
        document.documentElement.style.setProperty('--accent-hover', hover);
        document.documentElement.style.setProperty('--accent-glow', glow);
        
        if(!isInit) {
            localStorage.setItem('nx-color', color);
            localStorage.setItem('nx-hover', hover);
            localStorage.setItem('nx-glow', glow);
        }

        // Update active swatch
        document.querySelectorAll('.swatch').forEach(s => {
            s.classList.toggle('active', s.style.background === color || rgbToHex(s.style.backgroundColor) === color);
        });
    }

    function rgbToHex(rgb) {
        if(!rgb) return "";
        const match = rgb.match(/\d+/g);
        if(!match) return rgb;
        return "#" + match.slice(0, 3).map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
    }

    function setFont(font, btn, isInit) {
        document.documentElement.style.setProperty('--font-family', `"${font}", sans-serif`);
        if(!isInit) localStorage.setItem('nx-font', font);
        
        document.querySelectorAll('#fontGroup button').forEach(b => {
            b.classList.toggle('active', b.innerText.toLowerCase().includes(font.split(' ')[0].toLowerCase()));
        });
    }

    function setFontSize(size, isInit) {
        document.documentElement.style.setProperty('--font-size-base', `${size}px`);
        if(!isInit) localStorage.setItem('nx-size', size);
        if(!isInit) document.getElementById('sizeSlider').value = size;
    }

    function setDensity(padding, btn, isInit) {
        document.documentElement.style.setProperty('--card-padding', padding);
        if(!isInit) localStorage.setItem('nx-density', padding);
        
        const isCompact = padding === '16px';
        document.getElementById('btnComfort').classList.toggle('active', !isCompact);
        document.getElementById('btnCompact').classList.toggle('active', isCompact);
    }

    // --- Filtering & Rendering ---
    function setFilter(filter, btn) {
        activeFilter = filter;
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        if(btn) btn.classList.add('active');
        applyFilters();
    }

    function applyFilters() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        const filtered = allPosts.filter(post => {
            let matchesFilter = true;
            if (activeFilter !== 'all') {
                matchesFilter = (
                    (post.category && post.category.toLowerCase().includes(activeFilter)) ||
                    (post.difficulty && post.difficulty.toLowerCase() === activeFilter) ||
                    (post.code && post.code.language && post.code.language.toLowerCase() === activeFilter)
                );
            }
            let matchesSearch = true;
            if (searchTerm) {
                const text = `${post.title} ${post.summary} ${post.text} ${(post.keywords || []).join(' ')}`.toLowerCase();
                matchesSearch = text.includes(searchTerm);
            }
            return matchesFilter && matchesSearch;
        });
        renderPosts(filtered);
    }

    function renderPosts(postsToRender) {
        const feed = document.getElementById("feed");
        feed.innerHTML = "";

        if (!postsToRender || postsToRender.length === 0) {
            feed.innerHTML = `<div class="loader">No posts found.</div>`;
            return;
        }

        postsToRender.forEach((post, index) => {
            const card = document.createElement("article");
            card.className = "card";
            card.style.animationDelay = `${index * 0.1}s`;
            
            const c1 = `hsl(${Math.random() * 360}, 70%, 50%)`;
            const c2 = `hsl(${Math.random() * 360}, 70%, 30%)`;

            let tagsHtml = '<div class="tags">';
            if (post.category) tagsHtml += `<span class="tag cat">${post.category}</span>`;
            if (post.difficulty) tagsHtml += `<span class="tag diff">${post.difficulty}</span>`;
            if (post.type) tagsHtml += `<span class="tag type">${post.type}</span>`;
            tagsHtml += '</div>';

            const codeHtml = renderCodeBlock(post.code);
            const keywordsHtml = (post.keywords || [])
                .map(x => `<a href="#" class="keyword">#${x}</a>`).join("");

            const upvotes = Math.floor(Math.random() * 500) + 10;

            card.innerHTML = `
                <div class="card-banner" style="background: linear-gradient(135deg, ${c1}, ${c2});"></div>
                <div class="card-content">
                    <div class="meta-row">
                        ${tagsHtml}
                        <div class="post-stats">
                            <span class="stat-item">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                                ${Math.floor(Math.random()*50)+10}k
                            </span>
                            <span class="stat-item">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                ${Math.ceil((post.text || post.summary || "").split(' ').length / 200)} min
                            </span>
                        </div>
                    </div>
                    <h2 class="title">${post.title ?? "Untitled"}</h2>
                    ${post.summary ? `<p class="summary">${post.summary}</p>` : ''}
                    ${post.text ? `<div class="content-text">${post.text}</div>` : ''}
                    ${codeHtml}
                    <div class="card-footer">
                        <button class="action-btn" onclick="toggleUpvote(this)">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
                            <span>${upvotes}</span>
                        </button>
                        <button class="action-btn">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                            Discuss
                        </button>
                        <div class="keywords">${keywordsHtml}</div>
                    </div>
                </div>
            `;
            feed.appendChild(card);
        });

        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    function renderCodeBlock(codeData) {
        if (!codeData) return "";
        let language = 'python', filename = 'snippet.txt', content = '';
        if (typeof codeData === 'string') { content = codeData; } 
        else {
            language = codeData.language || 'python';
            filename = codeData.filename || 'code.snippet';
            content = codeData.content || '';
        }

        const colors = { python: '#3572A5', javascript: '#f1e05a', typescript: '#3178c6', html: '#e34c26', rust: '#dea584' };
        const dotColor = colors[(language || '').toLowerCase()] || '#8b949e';

        return `
            <div class="code-container">
                <div class="code-header">
                    <div class="file-info">
                        <div class="lang-dot" style="background: ${dotColor}"></div>
                        <span>${filename}</span>
                    </div>
                    <button class="copy-btn" onclick="copyCode(this, ${JSON.stringify(content).replace(/"/g, '&quot;')})">
                        <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z"></path><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z"></path></svg>
                        Copy
                    </button>
                </div>
                <pre><code class="language-${language}">${escapeHtml(content)}</code></pre>
            </div>
        `;
    }

    function renderCategories() {
        const categories = [
            { name: "Web Development", desc: "Frontend, Backend, APIs", icon: "🌐", posts: 124, c1: "#3b82f6", c2: "#1d4ed8" },
            { name: "AI & Machine Learning", desc: "Models, Data, PyTorch", icon: "🧠", posts: 89, c1: "#8b5cf6", c2: "#6d28d9" },
            { name: "Cybersecurity", desc: "Pentesting, Crypto, Fuzzing", icon: "🛡️", posts: 56, c1: "#ef4444", c2: "#b91c1c" },
            { name: "DevOps & Cloud", desc: "Docker, K8s, AWS", icon: "☁️", posts: 73, c1: "#10b981", c2: "#047857" },
            { name: "Data Science", desc: "Pandas, SQL, Visualization", icon: "📊", posts: 102, c1: "#f59e0b", c2: "#b45309" },
            { name: "Systems Programming", desc: "Rust, C++, Go", icon: "⚙️", posts: 45, c1: "#ec4899", c2: "#be185d" }
        ];
        const grid = document.getElementById('catGrid');
        grid.innerHTML = '';
        categories.forEach((cat, i) => {
            const card = document.createElement('div');
            card.className = 'cat-card';
            card.style.animationDelay = `${i * 0.1}s`;
            card.style.setProperty('--g1', cat.c1);
            card.style.setProperty('--g2', cat.c2);
            card.innerHTML = `
                <div class="cat-content">
                    <div class="cat-icon">${cat.icon}</div>
                    <div class="cat-title">${cat.name}</div>
                    <div class="cat-desc">${cat.desc}</div>
                    <div class="cat-stat">${cat.posts} Posts</div>
                </div>
            `;
            card.onclick = () => {
                switchView('home', document.querySelector('.nav-item[data-view="home"]'));
                document.getElementById('searchInput').value = '';
                setFilter('all', document.querySelector('.filter-btn[data-filter="all"]'));
                // simulate filter by category keyword
                setTimeout(() => {
                    document.getElementById('searchInput').value = cat.name.split(' ')[0].toLowerCase();
                    applyFilters();
                }, 300);
            };
            grid.appendChild(card);
        });
    }

    // --- Interactions ---
    function toggleUpvote(btn) {
        btn.classList.toggle('upvoted');
        const countEl = btn.querySelector('span');
        let count = parseInt(countEl.innerText);
        countEl.innerText = btn.classList.contains('upvoted') ? count + 1 : count - 1;
    }

    function copyCode(btn, text) {
        navigator.clipboard.writeText(text);
        btn.classList.add('copied');
        btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.751.751 0 01.018-1.042.751.751 0 011.042-.018L6 10.94l6.72-6.72a.75.75 0 011.06 0z"></path></svg> Copied!';
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z"></path><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z"></path></svg> Copy';
        }, 2000);
    }

    function escapeHtml(str) {
        if (!str) return "";
        return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // --- Progress Bar ---
    window.addEventListener('scroll', () => {
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        const progress = (window.scrollY / scrollHeight) * 100;
        document.getElementById('progress-bar').style.width = `${progress}%`;
    });

    // --- Init ---
    async function loadPosts() {
        try {
            const res = await fetch(API);
            if (!res.ok) throw new Error("Unable to load posts.");
            allPosts = await res.json();

            renderPosts(allPosts);
            renderCategories();
            loadSettings();

        } catch (error) {
            document.getElementById("feed").innerHTML = `<div class="loader">Unable to load posts.</div>`;
        }
    }

    loadPosts();
