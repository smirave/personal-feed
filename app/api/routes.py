from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.services.generator import ContentGenerator
from app.services.prompt_manager import PromptManager

router = APIRouter()
prompt_manager = PromptManager()
generator = ContentGenerator(prompt_manager=prompt_manager)


class GenerateRequest(BaseModel):
    prompt_file: str
    extra_context: str | None = None


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/api/prompts")
def list_prompts():
    return prompt_manager.list_prompts()


@router.post("/api/generate")
def generate_post(payload: GenerateRequest):
    try:
        result = generator.generate(payload.prompt_file, payload.extra_context)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _render_page(file_name: str) -> HTMLResponse:
    page_path = Path(__file__).resolve().parents[2] / "static" / file_name
    with page_path.open(encoding="utf-8") as handle:
        return HTMLResponse(handle.read())


@router.get("/", response_class=HTMLResponse)
def index_page():
    return _render_page("app.html")


@router.get("/app", response_class=HTMLResponse)
def app_page():
    return _render_page("app.html")


@router.get("/form", response_class=HTMLResponse)
def generate_page():
    return _render_page("form.html")


@router.get("/generate", response_class=HTMLResponse)
def legacy_generate_page():
    return _render_page("form.html")
