from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobRecord
from app.db.session import get_session
from app.models.job_spec import JobSpec, Quote
from app.services.closer import CloserService

router = APIRouter()


async def _get_job(job_id: str, session: AsyncSession) -> JobRecord:
    job = await session.get(JobRecord, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _load_spec(job: JobRecord) -> JobSpec:
    merged = job.get_json_field("merged_spec_json")
    if merged:
        return JobSpec.model_validate(merged)
    voice = job.get_json_field("voice_spec_json")
    if voice:
        return JobSpec.model_validate(voice)
    return JobSpec()


@router.get("/{job_id}/report")
async def get_report(
    job_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    job = await _get_job(job_id, session)
    spec = _load_spec(job)
    raw_quotes = job.get_json_field("quotes_json") or []
    if not raw_quotes:
        raise HTTPException(status_code=400, detail="No quotes available. Run calls first.")
    quotes = [Quote.model_validate(q) for q in raw_quotes]
    negotiations_raw = job.get_json_field("negotiations_json") or []
    from app.models.job_spec import NegotiationResult

    negotiations = [NegotiationResult.model_validate(n) for n in negotiations_raw]
    closer = CloserService(request.app.state.vertical_config)
    report = closer.build_report(job_id, spec, quotes, negotiations)
    job.set_json_field("report_json", report.model_dump(mode="json"))
    job.status = "report_ready"
    await session.commit()
    return report.model_dump(mode="json")
