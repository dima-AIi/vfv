from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope
from app.core.errors import ValidationError
from app.modules.identity.deps import OrgContext, require_permission
from app.modules.search.schemas import SearchResults
from app.modules.search.service import SearchService

router = APIRouter(tags=["search"])

MIN_QUERY_LENGTH = 2


def get_service(session: AsyncSession = Depends(get_session)) -> SearchService:
    return SearchService(session)


@router.get("/search")
async def global_search(
    q: str = Query(...),
    context: OrgContext = Depends(require_permission("search.search.read")),
    service: SearchService = Depends(get_service),
) -> Envelope[SearchResults]:
    term = q.strip()
    if len(term) < MIN_QUERY_LENGTH:
        raise ValidationError(
            f"Поисковый запрос должен содержать не менее {MIN_QUERY_LENGTH} символов.",
        )
    results = await service.search(term, context.scope)
    counts = {
        "projects": len(results.projects),
        "tasks": len(results.tasks),
        "documents": len(results.documents),
        "files": len(results.files),
        "customers": len(results.customers),
    }
    meta: dict[str, Any] = {"query": term, "counts": counts}
    return Envelope(data=results, meta=meta)
