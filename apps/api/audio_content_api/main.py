from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from audio_id.audio_io import load_wav_pcm
from audio_id.pipeline import AudioContentIdPipeline


app = FastAPI(
    title="Audio Content ID Enterprise MVP",
    version="0.1.0",
    description="Filter -> Embed -> Verify audio copyright matching API.",
)

pipeline = AudioContentIdPipeline()
detections: dict[str, dict] = {}
review_cases: dict[str, dict] = {}
STATIC_DIR = Path(__file__).resolve().parent / "static"


class DetectionResponse(BaseModel):
    detection_id: str
    status: Literal["completed"]
    matches: list[dict] = Field(default_factory=list)


class ReviewDecisionRequest(BaseModel):
    decision: Literal["approve", "reject", "escalate"]
    reviewer: str
    notes: str | None = None


app.mount("/ui/static", StaticFiles(directory=STATIC_DIR), name="ui-static")


async def _upload_to_signal(upload: UploadFile):
    suffix = Path(upload.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await upload.read())
        temp_path = Path(temp_file.name)
    try:
        return load_wav_pcm(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui")


@app.get("/ui", include_in_schema=False)
def ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/ui/", include_in_schema=False)
def ui_slash() -> RedirectResponse:
    return RedirectResponse(url="/ui")


@app.post("/v1/assets")
async def create_asset(
    file: UploadFile = File(...),
    asset_id: str = Form(...),
    title: str = Form(...),
    owner: str = Form(...),
) -> dict:
    try:
        signal = await _upload_to_signal(file)
        asset = pipeline.register_asset(
            asset_id=asset_id,
            title=title,
            owner=owner,
            signal=signal,
            metadata={"source_filename": file.filename},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "asset_id": asset.asset_id,
        "title": asset.title,
        "owner": asset.owner,
        "duration_seconds": asset.signal.duration_seconds,
        "metadata": asset.metadata,
    }


@app.get("/v1/assets")
def list_assets() -> list[dict]:
    return [
        {
            "asset_id": asset.asset_id,
            "title": asset.title,
            "owner": asset.owner,
            "duration_seconds": asset.signal.duration_seconds,
            "metadata": asset.metadata,
        }
        for asset in pipeline.references.values()
    ]


@app.post("/v1/detections", response_model=DetectionResponse)
async def create_detection(
    file: UploadFile = File(...),
    detection_id: str | None = Form(default=None),
) -> DetectionResponse:
    detection_id = detection_id or str(uuid4())
    try:
        signal = await _upload_to_signal(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    results = [
        pipeline.result_to_dict(result)
        for result in pipeline.detect(signal, detection_id=detection_id)
    ]
    response = {
        "detection_id": detection_id,
        "status": "completed",
        "matches": results,
    }
    detections[detection_id] = response

    for result in results:
        if result["action"] == "human_review":
            review_cases[detection_id] = {
                "detection_id": detection_id,
                "status": "open",
                "match": result,
                "decision": None,
            }

    return DetectionResponse(**response)


@app.get("/v1/detections")
def list_detections() -> list[dict]:
    return list(detections.values())


@app.get("/v1/detections/{detection_id}")
def get_detection(detection_id: str) -> dict:
    result = detections.get(detection_id)
    if not result:
        raise HTTPException(status_code=404, detail="detection not found")
    return result


@app.get("/v1/review-cases")
def list_review_cases(status: str = "open") -> list[dict]:
    return [case for case in review_cases.values() if case["status"] == status]


@app.post("/v1/review-cases/{detection_id}/decision")
def decide_review_case(
    detection_id: str,
    request: ReviewDecisionRequest,
) -> dict:
    case = review_cases.get(detection_id)
    if not case:
        raise HTTPException(status_code=404, detail="review case not found")

    case["status"] = "closed"
    case["decision"] = request.model_dump()
    return case
