from __future__ import annotations

import json
import os
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

            previous_keys = self._get_duplicate_keys()
            prompt_text = f"{prompt_text}\n\nPrevious duplicate keys:\n{json.dumps(previous_keys, ensure_ascii=False)}\n\nDo not generate posts with the same or similar duplicate_key."

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

    def _get_duplicate_keys(self, limit: int = 500) -> List[str]:
        if not self.db_path.exists():
            return []

        with sqlite3.connect(self.db_path) as conn:
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

        return [row[0] for row in rows]

    def _persist_posts(self, posts: List[Dict[str, Any]]) -> None:
        with sqlite3.connect(self.db_path) as conn:
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
