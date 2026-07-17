from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List


class PromptManager:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(__file__).resolve().parents[2]
        self.prompts_dir = self.base_dir / "prompts"

    def list_prompts(self) -> List[Dict[str, str]]:
        if not self.prompts_dir.exists():
            return []

        prompts: List[Dict[str, str]] = []
        for path in sorted(self.prompts_dir.glob("*.md")):
            name = self._derive_name(path)
            prompts.append({"name": name, "file": path.name})
        return prompts

    def load_prompt(self, file_name: str) -> str:
        path = self.prompts_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"Prompt not found: {file_name}")
        return path.read_text(encoding="utf-8")

    def _derive_name(self, path: Path) -> str:
        stem = path.stem.replace("-", " ").replace("_", " ")
        words = re.split(r"\s+", stem.strip())
        title_words = [word.capitalize() for word in words if word]
        if not title_words:
            return path.stem
        return " ".join(title_words)
