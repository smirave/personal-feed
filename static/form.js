
      const promptSelect = document.getElementById('promptSelect');
      const generateBtn = document.getElementById('generateBtn');
      const extraContext = document.getElementById('extraContext');
      const status = document.getElementById('status');
      const resultCard = document.getElementById('resultCard');
      const resultOutput = document.getElementById('resultOutput');
      async function loadPrompts() {
        status.className = 'status';
        status.innerHTML = '<span class="spinner"><i></i>Loading prompts…</span>';
        try {
          const response = await fetch('/api/prompts');
          if (!response.ok) throw new Error('Failed to load prompts');
          const prompts = await response.json();
          promptSelect.innerHTML = '';
          if (!prompts.length) {
            promptSelect.innerHTML = '<option value="">No prompts available</option>';
            status.textContent = 'No prompt files were found.';
            return;
          }
          prompts.forEach((prompt) => {
            const option = document.createElement('option');
            option.value = prompt.file;
            option.textContent = prompt.name;
            promptSelect.appendChild(option);
          });
          status.textContent = `Loaded ${prompts.length} prompt${prompts.length === 1 ? '' : 's'}.`;
        } catch (error) {
          status.className = 'status error';
          status.textContent = error.message;
        }
      }
      generateBtn.addEventListener('click', async () => {
        const selectedPrompt = promptSelect.value;
        if (!selectedPrompt) {
          status.className = 'status error';
          status.textContent = 'Please select a prompt before generating.';
          return;
        }
        generateBtn.disabled = true;
        status.className = 'status';
        status.innerHTML = '<span class="spinner"><i></i>Generating content…</span>';
        resultCard.style.display = 'none';
        try {
          const response = await fetch('/api/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt_file: selectedPrompt, extra_context: extraContext.value }) });
          const data = await response.json();
          if (!response.ok) throw new Error(data.detail || 'Generation failed');
          const posts = data.posts || [];
          if (!posts.length) {
            resultCard.style.display = 'block';
            resultOutput.textContent = 'No posts were returned by the model.';
            status.className = 'status success';
            status.textContent = 'The generation request completed without returning posts.';
            return;
          }
          const rendered = posts.map((post, index) => `${index + 1}. ${post.title || 'Untitled Post'}\n\n${post.text || post.summary || ''}`).join('\n\n---\n\n');
          resultOutput.textContent = rendered;
          resultCard.style.display = 'block';
          status.className = 'status success';
          status.textContent = `Generated ${posts.length} post${posts.length === 1 ? '' : 's'} successfully.`;
        } catch (error) {
          status.className = 'status error';
          status.textContent = error.message;
        } finally {
          generateBtn.disabled = false;
        }
      });
      loadPrompts();
    