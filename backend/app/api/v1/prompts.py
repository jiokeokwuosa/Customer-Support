"""Sample prompt endpoints under /api/v1/sample-prompts."""

from fastapi import APIRouter

from app.data.sample_prompts import list_sample_prompts
from app.schemas.prompts import SamplePromptsResponse

router = APIRouter(tags=["prompts"])


@router.get("/sample-prompts", response_model=SamplePromptsResponse)
def get_sample_prompts() -> SamplePromptsResponse:
    return SamplePromptsResponse(prompts=list_sample_prompts())
