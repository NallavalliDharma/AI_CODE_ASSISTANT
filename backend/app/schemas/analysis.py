"""Analysis schemas."""

from datetime import datetime

from pydantic import BaseModel

from app.models.analysis import AnalysisStatus, FindingSeverity, ToolType


class AnalysisRunCreate(BaseModel):
    pull_request_id: int | None = None
    patch_id: int | None = None


class FindingResponse(BaseModel):
    id: int
    severity: FindingSeverity
    category: str
    file_path: str | None
    line_number: int | None
    column_number: int | None
    message: str
    rule_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TestResultResponse(BaseModel):
    id: int
    tool_name: str
    tool_type: ToolType
    status: str
    issue_count: int
    created_at: datetime
    findings: list[FindingResponse] = []

    model_config = {"from_attributes": True}


class AnalysisRunResponse(BaseModel):
    id: int
    repository_id: int
    pull_request_id: int | None
    patch_id: int | None
    status: AnalysisStatus
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    test_results: list[TestResultResponse] = []
    findings: list[FindingResponse] = []

    model_config = {"from_attributes": True}
