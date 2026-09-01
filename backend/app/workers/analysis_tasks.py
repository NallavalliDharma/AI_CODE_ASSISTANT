"""Static analysis Celery tasks."""

import os
import shutil

from app.db.session import SessionLocal
from app.models.analysis import Finding, TestResult
from app.models.pull_request import Patch, PullRequest
from app.models.repository import Repository
from app.services.analysis_runner import prepare_analysis_workspace, run_all_analyzers
from app.services.analysis_service import mark_completed, mark_failed, mark_running
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.analysis_tasks.run_static_analysis", bind=True, max_retries=1)
def run_static_analysis(self, analysis_run_id: int) -> dict:
    db = SessionLocal()
    workspace = None
    try:
        from app.models.analysis import AnalysisRun

        run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_run_id).first()
        if not run:
            return {"error": "Analysis run not found"}

        mark_running(db, analysis_run_id)

        repo = db.query(Repository).filter(Repository.id == run.repository_id).first()
        diff_content = None

        if run.patch_id:
            patch = db.query(Patch).filter(Patch.id == run.patch_id).first()
            if patch:
                diff_content = patch.content
        elif run.pull_request_id:
            pr = db.query(PullRequest).filter(PullRequest.id == run.pull_request_id).first()
            if pr and pr.diff_content:
                diff_content = pr.diff_content

        repo_path = repo.local_path if repo and repo.local_path and os.path.isdir(repo.local_path) else None
        if repo_path:
            workspace = prepare_analysis_workspace(repo_path, diff_content)
        elif diff_content:
            workspace = prepare_analysis_workspace(os.path.dirname(os.path.abspath(__file__)), diff_content)
        else:
            workspace = prepare_analysis_workspace(
                repo.local_path or os.path.join(os.getcwd(), "uploads", str(repo.id))
            )

        results = run_all_analyzers(workspace)

        for tool_result in results:
            test_result = TestResult(
                analysis_run_id=analysis_run_id,
                tool_name=tool_result.tool_name,
                tool_type=tool_result.tool_type,
                status=tool_result.status,
                output=tool_result.output[:10000] if tool_result.output else None,
                issue_count=len(tool_result.findings),
            )
            db.add(test_result)
            db.flush()

            for finding_data in tool_result.findings:
                finding = Finding(
                    analysis_run_id=analysis_run_id,
                    test_result_id=test_result.id,
                    severity=finding_data.severity,
                    category=finding_data.category,
                    file_path=finding_data.file_path,
                    line_number=finding_data.line_number,
                    column_number=finding_data.column_number,
                    message=finding_data.message,
                    rule_id=finding_data.rule_id,
                )
                db.add(finding)

        db.commit()
        mark_completed(db, analysis_run_id)
        return {"analysis_run_id": analysis_run_id, "status": "completed"}

    except Exception as exc:
        db.rollback()
        mark_failed(db, analysis_run_id, str(exc))
        raise self.retry(exc=exc, countdown=10) from exc
    finally:
        if workspace and os.path.isdir(workspace):
            shutil.rmtree(workspace, ignore_errors=True)
        db.close()
