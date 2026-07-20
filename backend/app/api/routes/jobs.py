import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.elevenlabs import ElevenLabsClient
from app.config.settings import settings
from app.db.models import JobRecord
from app.db.session import get_session
from app.models.job_spec import JobSpec
from app.services.caller import CallerService
from app.services.closer import CloserService
from app.services.document_intake import DocumentIntakeService

router = APIRouter()


class CreateJobResponse(BaseModel):
    id: str
    status: str


class VoiceIntakeRequest(BaseModel):
    transcript: str


class ConfirmSpecRequest(BaseModel):
    spec: JobSpec | None = None


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


def _save_merged_spec(job: JobRecord, spec: JobSpec) -> None:
    job.set_json_field("merged_spec_json", spec.model_dump(mode="json"))


@router.post("", response_model=CreateJobResponse)
async def create_job(session: AsyncSession = Depends(get_session)) -> CreateJobResponse:
    job_id = str(uuid.uuid4())
    job = JobRecord(id=job_id, status="draft")
    session.add(job)
    await session.commit()
    return CreateJobResponse(id=job_id, status=job.status)


@router.get("/{job_id}/voice/session")
async def get_voice_session(
    job_id: str,
    request: Request,
) -> dict:
    client = ElevenLabsClient(settings.elevenlabs_api_key)
    session_data = await client.start_intake_session(job_id)
    return session_data


@router.post("/{job_id}/voice")
async def submit_voice_intake(
    job_id: str,
    payload: VoiceIntakeRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    job = await _get_job(job_id, session)
    client = ElevenLabsClient(settings.elevenlabs_api_key)
    voice_spec = await client.parse_voice_transcript(payload.transcript)
    job.set_json_field("voice_spec_json", voice_spec.model_dump(mode="json"))
    existing = _load_spec(job) if job.get_json_field("document_spec_json") else JobSpec()
    doc_spec_data = job.get_json_field("document_spec_json")
    if doc_spec_data:
        existing = JobSpec.model_validate(doc_spec_data)
        merged = JobSpec.merge(voice_spec, existing)
    else:
        merged = voice_spec
    _save_merged_spec(job, merged)
    job.status = "intake_in_progress"
    await session.commit()
    session_data = await client.start_intake_session(job_id)
    return {"job_id": job_id, "spec": merged.model_dump(mode="json"), "session": session_data}


@router.post("/{job_id}/documents")
async def upload_document(
    job_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    file: UploadFile = File(...),
) -> dict:
    job = await _get_job(job_id, session)
    content = await file.read()
    parser = DocumentIntakeService()
    doc_spec = await parser.parse_upload(file.filename or "upload.txt", content)
    job.set_json_field("document_spec_json", doc_spec.model_dump(mode="json"))
    voice_data = job.get_json_field("voice_spec_json")
    if voice_data:
        merged = JobSpec.merge(JobSpec.model_validate(voice_data), doc_spec)
    else:
        merged = doc_spec
    _save_merged_spec(job, merged)
    job.status = "intake_in_progress"
    await session.commit()
    return {"job_id": job_id, "spec": merged.model_dump(mode="json")}


@router.get("/{job_id}/spec")
async def get_spec(
    job_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    job = await _get_job(job_id, session)
    spec = _load_spec(job)
    required = request.app.state.vertical_config.job_spec.get("required_for_binding", [])
    return {
        "job_id": job_id,
        "status": job.status,
        "spec": spec.model_dump(mode="json"),
        "binding_ready": spec.is_binding_ready(required),
        "missing_fields": spec.missing_binding_fields(required),
    }


@router.patch("/{job_id}/spec")
async def update_spec(
    job_id: str,
    spec: JobSpec,
    session: AsyncSession = Depends(get_session),
) -> dict:
    job = await _get_job(job_id, session)
    _save_merged_spec(job, spec)
    await session.commit()
    return {"job_id": job_id, "spec": spec.model_dump(mode="json")}


@router.post("/{job_id}/confirm")
async def confirm_spec(
    job_id: str,
    request: Request,
    payload: ConfirmSpecRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    job = await _get_job(job_id, session)
    spec = payload.spec if payload and payload.spec else _load_spec(job)
    required = request.app.state.vertical_config.job_spec.get("required_for_binding", [])
    if not spec.is_binding_ready(required):
        raise HTTPException(
            status_code=400,
            detail={"message": "Spec incomplete", "missing": spec.missing_binding_fields(required)},
        )
    spec.confirmed_by_user = True
    spec.confirmed_at = datetime.utcnow()
    _save_merged_spec(job, spec)
    job.status = "confirmed"
    await session.commit()
    return {"job_id": job_id, "status": job.status, "spec": spec.model_dump(mode="json")}


@router.post("/{job_id}/calls")
async def start_calls(
    job_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    job = await _get_job(job_id, session)
    spec = _load_spec(job)
    if not spec.confirmed_by_user:
        raise HTTPException(status_code=400, detail="Job spec must be confirmed before calling")
    caller = CallerService(request.app.state.vertical_config)
    quotes = await caller.gather_quotes(spec)
    job.set_json_field("quotes_json", [q.model_dump(mode="json") for q in quotes])
    job.status = "calls_complete"
    await session.commit()
    return {
        "job_id": job_id,
        "quotes": [q.model_dump(mode="json") for q in quotes],
        "call_list": caller.call_list.build_call_list(spec.origin),
    }


@router.get("/{job_id}/calls")
async def get_calls(job_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    job = await _get_job(job_id, session)
    quotes = job.get_json_field("quotes_json") or []
    return {"job_id": job_id, "status": job.status, "quotes": quotes}


@router.post("/{job_id}/negotiate")
async def run_negotiation(
    job_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    job = await _get_job(job_id, session)
    spec = _load_spec(job)
    raw_quotes = job.get_json_field("quotes_json") or []
    from app.models.job_spec import Quote

    quotes = [Quote.model_validate(q) for q in raw_quotes]
    closer = CloserService(request.app.state.vertical_config)
    final_quotes, negotiations = closer.negotiate(quotes, spec)
    job.set_json_field("quotes_json", [q.model_dump(mode="json") for q in final_quotes])
    job.set_json_field("negotiations_json", [n.model_dump(mode="json") for n in negotiations])
    job.status = "negotiated"
    await session.commit()
    return {
        "job_id": job_id,
        "quotes": [q.model_dump(mode="json") for q in final_quotes],
        "negotiations": [n.model_dump(mode="json") for n in negotiations],
    }
