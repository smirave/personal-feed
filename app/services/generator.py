from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from app.services.prompt_manager import PromptManager

load_dotenv()


class ContentGenerator:
    def __init__(self, prompt_manager: PromptManager | None = None, db_path: str | None = None):
        self.prompt_manager = prompt_manager or PromptManager()
        self.db_path = Path(db_path or "posts.db")
        self.token = os.getenv("TOKEN")
        self.model = os.getenv("MODEL", "tencent/hy3:free")
        self.base_dir = Path(__file__).resolve().parents[2]
        self.log_dir = Path(os.getenv("GENERATOR_LOG_DIR", str(self.base_dir / "logs")))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "generator.log"
        try:
            self.log_file.touch(exist_ok=True)
        except OSError:
            self.log_dir = Path.cwd() / "logs"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "generator.log"
            self.log_file.touch(exist_ok=True)
        self._write_log("Generator initialized")

    def generate(self, prompt_file: str, extra_context: str | None = None) -> Dict[str, Any]:
        self._write_log(f"Starting generation for prompt={prompt_file}")

        if not self.token:
            self._write_log("TOKEN missing in environment")
            raise RuntimeError("TOKEN not found in .env")

        try:
            prompt_text = self.prompt_manager.load_prompt(prompt_file)
            if extra_context:
                prompt_text = f"{prompt_text}\n\nAdditional context:\n{extra_context}"

            topic_keywords = self._extract_topic_keywords(prompt_file)
            prior_posts = self._get_prior_posts(topic_keywords, limit=8)
            previous_keys = self._get_duplicate_keys()
            prompt_text = (
                f"{prompt_text}\n\n"
                f"Topic keywords: {', '.join(topic_keywords)}\n\n"
                f"Relevant prior posts from the database:\n{json.dumps(prior_posts, ensure_ascii=False)}\n\n"
                f"Previous duplicate keys:\n{json.dumps(previous_keys, ensure_ascii=False)}\n\n"
                "Use these as memory. Avoid repeating the same ideas, titles, angles, keywords, or duplicate_key values."
            )

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.7,
                },
                timeout=120,
            )
            response.raise_for_status()

            data = response.json()
            try:
                text = data["choices"][0]["message"]["content"]
            except Exception as exc:  # pragma: no cover
                self._write_log(f"Invalid response structure: {json.dumps(data, indent=2)}")
                raise RuntimeError(json.dumps(data, indent=2)) from exc

            text = text.replace("```json", "").replace("```", "").strip()
            try:
                payload = json.loads(text)
            except Exception as exc:  # pragma: no cover
                self._write_log(f"Invalid model output: {text}")
                raise RuntimeError("Model output is not valid JSON") from exc

            posts = payload.get("posts", [])
            self._persist_posts(posts)
            self._write_log(f"Generated {len(posts)} posts successfully")
            return {"posts": posts, "count": len(posts)}
        except Exception as exc:
            self._write_log(f"Generation failed: {exc}")
            raise

    def _write_log(self, message: str) -> None:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.log_file.open("a", encoding="utf-8") as handle:
                handle.write(f"[{timestamp}] {message}\n")
        except OSError:
            fallback_dir = Path.cwd() / "logs"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            self.log_dir = fallback_dir
            self.log_file = self.log_dir / "generator.log"
            self.log_file.touch(exist_ok=True)
            with self.log_file.open("a", encoding="utf-8") as handle:
                handle.write(f"[{timestamp}] {message}\n")

    def _extract_topic_keywords(self, prompt_file: str) -> List[str]:
        prompt_name = Path(prompt_file).stem.lower()
        parts = [part for part in re.split(r"[^a-z0-9]+", prompt_name) if part]
        keywords = []
        for part in parts:
            if part not in {"md", "txt", "prompt"}:
                keywords.append(part)
        return keywords or [prompt_name]

    def _get_prior_posts(self, topic_keywords: List[str], limit: int = 8) -> List[Dict[str, Any]]:
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            query_terms = [term for term in topic_keywords if term]
            if not query_terms:
                return []

            placeholders = ", ".join("?" for _ in query_terms)
            rows = conn.execute(
                f"""
                SELECT id, category, title, summary, text, keywords, duplicate_key
                FROM posts
                WHERE 1=0
                """
            )
            rows.close()

            sql = """
                SELECT id, category, title, summary, text, keywords, duplicate_key
                FROM posts
                WHERE 1=1
            """
            params: List[Any] = []
            for term in query_terms:
                sql += " AND (lower(category) LIKE ? OR lower(title) LIKE ? OR lower(summary) LIKE ? OR lower(text) LIKE ? OR lower(keywords) LIKE ?)"
                like_term = f"%{term}%"
                params.extend([like_term] * 5)

            sql += " ORDER BY rowid DESC LIMIT ?"
            params.append(limit)

            db_rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()

        prior_posts: List[Dict[str, Any]] = []
        for row in db_rows:
            keywords_value = row["keywords"]
            keywords: List[str] = []
            if keywords_value:
                try:
                    keywords = json.loads(keywords_value)
                except json.JSONDecodeError:
                    keywords = []

            prior_posts.append(
                {
                    "id": row["id"],
                    "category": row["category"],
                    "title": row["title"],
                    "summary": row["summary"],
                    "text": row["text"],
                    "keywords": keywords,
                    "duplicate_key": row["duplicate_key"],
                }
            )

        return prior_posts

    def _get_duplicate_keys(self, limit: int = 500) -> List[str]:
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT duplicate_key
                FROM posts
                WHERE duplicate_key IS NOT NULL
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            conn.close()

        return [row[0] for row in rows]

    def list_posts(self) -> List[Dict[str, Any]]:
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    id,
                    category,
                    subcategory,
                    title,
                    type,
                    difficulty,
                    text,
                    code,
                    summary,
                    keywords,
                    duplicate_key,
                    novelty_score,
                    confidence,
                    reason,
                    source_suggestion
                FROM posts
                ORDER BY rowid DESC
                """
            ).fetchall()
        finally:
            conn.close()

        posts: List[Dict[str, Any]] = []
        for row in rows:
            post = {
                "id": row["id"],
                "category": row["category"],
                "subcategory": row["subcategory"],
                "title": row["title"],
                "type": row["type"],
                "difficulty": row["difficulty"],
                "text": row["text"],
                "summary": row["summary"],
                "duplicate_key": row["duplicate_key"],
                "novelty_score": row["novelty_score"],
                "confidence": row["confidence"],
                "reason": row["reason"],
                "source_suggestion": row["source_suggestion"],
            }
            code_value = row["code"]
            if code_value:
                try:
                    post["code"] = json.loads(code_value)
                except json.JSONDecodeError:
                    post["code"] = None
            else:
                post["code"] = None

            keywords_value = row["keywords"]
            if keywords_value:
                try:
                    post["keywords"] = json.loads(keywords_value)
                except json.JSONDecodeError:
                    post["keywords"] = []
            else:
                post["keywords"] = []

            posts.append(post)

        return posts

    def _persist_posts(self, posts: List[Dict[str, Any]]) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posts(
                    id TEXT PRIMARY KEY,
                    category TEXT,
                    subcategory TEXT,
                    title TEXT,
                    type TEXT,
                    difficulty TEXT,
                    text TEXT,
                    code TEXT,
                    summary TEXT,
                    keywords TEXT,
                    duplicate_key TEXT UNIQUE,
                    novelty_score INTEGER,
                    confidence INTEGER,
                    reason TEXT,
                    source_suggestion TEXT
                )
                """
            )

            conn.executemany(
                """
                INSERT OR REPLACE INTO posts(
                    id,
                    category,
                    subcategory,
                    title,
                    type,
                    difficulty,
                    text,
                    code,
                    summary,
                    keywords,
                    duplicate_key,
                    novelty_score,
                    confidence,
                    reason,
                    source_suggestion
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                [
                    (
                        post["id"],
                        post.get("category"),
                        post.get("subcategory"),
                        post.get("title"),
                        post.get("type"),
                        post.get("difficulty"),
                        post.get("text"),
                        json.dumps(post.get("code"), ensure_ascii=False),
                        post.get("summary"),
                        json.dumps(post.get("keywords", []), ensure_ascii=False),
                        post.get("duplicate_key"),
                        post.get("novelty_score"),
                        post.get("confidence"),
                        post.get("reason"),
                        post.get("source_suggestion"),
                    )
                    for post in posts
                ],
            )
            conn.commit()
        finally:
            conn.close()
