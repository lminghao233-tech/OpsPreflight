from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .analyzer import Analyzer
from .brief import deterministic_brief
from .models import AnalysisContext
from .storage import Store


class AnalyzeRequest(BaseModel):
    plan: dict[str, Any]
    repository: str = "local/demo"
    commit: str = "working-tree"
    environment: str = "development"
    pull_request: int | None = None
    owners: dict[str, str] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    actor: str
    reason: str
    break_glass: bool = False


class OutcomeRequest(BaseModel):
    actor: str
    outcome: Literal["success", "rollback", "incident"]


class BriefRequest(BaseModel):
    audience: Literal["developer", "approver", "manager"] = "approver"


app = FastAPI(title="OpsPreflight", version="0.1.0")
store = Store(os.getenv("OPSPREFLIGHT_DATABASE", ":memory:"))


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("OPSPREFLIGHT_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid API key")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/analyses", dependencies=[Depends(require_api_key)])
def create_analysis(request: AnalyzeRequest) -> dict[str, Any]:
    context = AnalysisContext(
        repository=request.repository,
        commit=request.commit,
        environment=request.environment,
        pull_request=request.pull_request,
        owners=request.owners,
    )
    result = Analyzer().analyze(request.plan, context)
    store.save_analysis(result)
    return result.to_dict()


def _get_or_404(analysis_id: str) -> dict[str, Any]:
    analysis = store.get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="analysis not found")
    return analysis


@app.get("/v1/analyses/{analysis_id}", dependencies=[Depends(require_api_key)])
def get_analysis(analysis_id: str) -> dict[str, Any]:
    return _get_or_404(analysis_id)


@app.post("/v1/analyses/{analysis_id}/approvals", dependencies=[Depends(require_api_key)])
def approve(analysis_id: str, request: ApprovalRequest) -> dict[str, str]:
    _get_or_404(analysis_id)
    try:
        store.approve(
            analysis_id, request.actor, request.reason, break_glass=request.break_glass
        )
    except PermissionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"status": "recorded"}


@app.post("/v1/analyses/{analysis_id}/outcomes", dependencies=[Depends(require_api_key)])
def outcome(analysis_id: str, request: OutcomeRequest) -> dict[str, str]:
    _get_or_404(analysis_id)
    store.record_outcome(analysis_id, request.actor, request.outcome)
    return {"status": "recorded"}


@app.post("/v1/analyses/{analysis_id}/brief", dependencies=[Depends(require_api_key)])
def brief(analysis_id: str, request: BriefRequest) -> dict[str, Any]:
    return deterministic_brief(_get_or_404(analysis_id), request.audience)


@app.get("/v1/analyses/{analysis_id}/timeline", dependencies=[Depends(require_api_key)])
def timeline(analysis_id: str) -> list[dict[str, Any]]:
    _get_or_404(analysis_id)
    return store.timeline(analysis_id)

