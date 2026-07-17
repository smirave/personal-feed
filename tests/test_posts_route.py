import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.routes as routes
from app.services.generator import ContentGenerator


def _close_db(path: Path) -> None:
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


class PostsRouteTests(unittest.TestCase):
    def test_generator_lists_persisted_posts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "posts.db"
            generator = ContentGenerator(prompt_manager=None, db_path=str(db_path))
            try:
                generator._persist_posts(
                    [
                        {
                            "id": "post-1",
                            "category": "Test",
                            "title": "Example post",
                            "type": "Guide",
                            "difficulty": "Easy",
                            "text": "Hello world",
                            "summary": "Short summary",
                            "keywords": ["test"],
                            "duplicate_key": "dup-1",
                            "novelty_score": 1,
                            "confidence": 1,
                            "reason": "",
                            "source_suggestion": "",
                        }
                    ]
                )

                posts = generator.list_posts()

                self.assertEqual(len(posts), 1)
                self.assertEqual(posts[0]["title"], "Example post")
                self.assertEqual(posts[0]["keywords"], ["test"])
            finally:
                _close_db(db_path)

    def test_posts_route_returns_all_posts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "posts.db"
            generator = ContentGenerator(prompt_manager=None, db_path=str(db_path))
            try:
                generator._persist_posts(
                    [
                        {
                            "id": "post-2",
                            "category": "Test",
                            "title": "Route post",
                            "type": "Guide",
                            "difficulty": "Easy",
                            "text": "Hello world",
                            "summary": "Short summary",
                            "keywords": ["route"],
                            "duplicate_key": "dup-2",
                            "novelty_score": 1,
                            "confidence": 1,
                            "reason": "",
                            "source_suggestion": "",
                        }
                    ]
                )

                routes.generator = generator
                app = FastAPI()
                app.include_router(routes.router)
                client = TestClient(app)

                response = client.get("/api/posts")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.json()), 1)
                self.assertEqual(response.json()[0]["title"], "Route post")
            finally:
                _close_db(db_path)

    def test_prior_posts_memory_uses_topic_keywords(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "posts.db"
            generator = ContentGenerator(prompt_manager=None, db_path=str(db_path))
            try:
                generator._persist_posts(
                    [
                        {
                            "id": "post-3",
                            "category": "Laravel",
                            "title": "Avoiding N+1 queries",
                            "type": "Guide",
                            "difficulty": "Medium",
                            "text": "Laravel eager loading helps avoid N+1 queries.",
                            "summary": "Laravel memory",
                            "keywords": ["laravel", "eloquent"],
                            "duplicate_key": "dup-3",
                            "novelty_score": 1,
                            "confidence": 1,
                            "reason": "",
                            "source_suggestion": "",
                        },
                        {
                            "id": "post-4",
                            "category": "General",
                            "title": "Unrelated topic",
                            "type": "Guide",
                            "difficulty": "Easy",
                            "text": "Something completely different.",
                            "summary": "No relevance",
                            "keywords": ["other"],
                            "duplicate_key": "dup-4",
                            "novelty_score": 1,
                            "confidence": 1,
                            "reason": "",
                            "source_suggestion": "",
                        },
                    ]
                )

                prior_posts = generator._get_prior_posts(["laravel"], limit=5)

                self.assertEqual(len(prior_posts), 1)
                self.assertEqual(prior_posts[0]["title"], "Avoiding N+1 queries")
            finally:
                _close_db(db_path)


if __name__ == "__main__":
    unittest.main()
