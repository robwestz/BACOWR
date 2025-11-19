"""
Export API Routes

Handles export of BACOWR jobs to Google Sheets and Docs.

IMPORTANT: This module ONLY creates NEW endpoints.
It USES existing services (JobOrchestrator, Job model) - does NOT modify them.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

# Import database and models
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from api.app.database import get_db
from api.app.models.database import Job, User

# Import NEW export modules (no conflicts!)
from src.export import GoogleAuthManager, GoogleSheetsExporter, GoogleDocsExporter


# Pydantic models for request/response
class ExportToGoogleSheetsRequest(BaseModel):
    """Request model for exporting job to Google Sheets."""
    spreadsheet_id: Optional[str] = Field(
        None,
        description="Existing spreadsheet ID (creates new if not provided)"
    )
    share_with_email: Optional[str] = Field(
        None,
        description="Email to share spreadsheet with"
    )
    create_doc: bool = Field(
        True,
        description="Also create Google Doc with full article"
    )


class ExportToGoogleDocsRequest(BaseModel):
    """Request model for exporting job to Google Docs."""
    share_with_email: Optional[str] = Field(
        None,
        description="Email to share document with"
    )


class BatchExportToGoogleRequest(BaseModel):
    """Request model for batch export to Google."""
    batch_name: Optional[str] = Field(
        None,
        description="Name for the batch (uses batch_id if not provided)"
    )
    share_with_email: Optional[str] = Field(
        None,
        description="Email to share spreadsheet with"
    )
    create_docs: bool = Field(
        True,
        description="Create Google Docs for each article"
    )
    job_ids: Optional[List[str]] = Field(
        None,
        description="Specific job IDs to export (exports all if not provided)"
    )


class ExportResponse(BaseModel):
    """Response model for export operations."""
    success: bool
    message: str
    spreadsheet_url: Optional[str] = None
    document_url: Optional[str] = None
    jobs_exported: Optional[int] = None


# Create router
router = APIRouter(
    prefix="/export",
    tags=["export"],
    responses={404: {"description": "Not found"}}
)


@router.post("/jobs/{job_id}/google-sheets", response_model=ExportResponse)
async def export_job_to_google_sheets(
    job_id: str,
    request: ExportToGoogleSheetsRequest,
    db: Session = Depends(get_db)
):
    """
    Export a single job to Google Sheets.

    Optionally creates a Google Doc with the full article and links it in the sheet.

    Endpoint: POST /api/v1/export/jobs/{job_id}/google-sheets
    """
    # Fetch job from database (USES existing Job model - no modifications)
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job.status != "delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job must be in 'delivered' status (current: {job.status})"
        )

    try:
        # Initialize exporters (NEW code - no conflicts)
        auth_manager = GoogleAuthManager()
        sheets_exporter = GoogleSheetsExporter(auth_manager)
        docs_exporter = GoogleDocsExporter(auth_manager)

        # Convert job to dict
        job_data = {
            'id': job.id,
            'created_at': job.created_at,
            'publisher_domain': job.publisher_domain,
            'target_url': job.target_url,
            'anchor_text': job.anchor_text,
            'status': job.status,
            'article_text': job.article_text,
            'qc_report': job.qc_report,
            'actual_cost': job.actual_cost or job.estimated_cost
        }

        # Create or use existing spreadsheet
        if request.spreadsheet_id:
            spreadsheet_id = request.spreadsheet_id
            spreadsheet_url = sheets_exporter.get_spreadsheet_url(spreadsheet_id)
        else:
            # Create new spreadsheet
            sheet_info = sheets_exporter.create_spreadsheet(
                title=f"BACOWR Export - {job.publisher_domain}",
                share_with_email=request.share_with_email
            )
            spreadsheet_id = sheet_info['spreadsheet_id']
            spreadsheet_url = sheet_info['spreadsheet_url']

        # Create Google Doc if requested
        doc_url = None
        if request.create_doc and job.article_text:
            doc_info = docs_exporter.export_job_to_doc(
                job_data,
                share_with_email=request.share_with_email
            )
            doc_url = doc_info['document_url']

        # Export to sheet
        sheets_exporter.export_job(
            spreadsheet_id=spreadsheet_id,
            job_data=job_data,
            doc_url=doc_url
        )

        return ExportResponse(
            success=True,
            message=f"Job {job_id} exported to Google Sheets successfully",
            spreadsheet_url=spreadsheet_url,
            document_url=doc_url,
            jobs_exported=1
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/jobs/{job_id}/google-docs", response_model=ExportResponse)
async def export_job_to_google_docs(
    job_id: str,
    request: ExportToGoogleDocsRequest,
    db: Session = Depends(get_db)
):
    """
    Export a single job to Google Docs only.

    Endpoint: POST /api/v1/export/jobs/{job_id}/google-docs
    """
    # Fetch job from database
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if not job.article_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job does not have article text"
        )

    try:
        # Initialize exporter
        docs_exporter = GoogleDocsExporter()

        # Convert job to dict
        job_data = {
            'id': job.id,
            'created_at': job.created_at,
            'publisher_domain': job.publisher_domain,
            'target_url': job.target_url,
            'anchor_text': job.anchor_text,
            'status': job.status,
            'article_text': job.article_text,
            'qc_report': job.qc_report
        }

        # Create Google Doc
        doc_info = docs_exporter.export_job_to_doc(
            job_data,
            share_with_email=request.share_with_email
        )

        return ExportResponse(
            success=True,
            message=f"Job {job_id} exported to Google Docs successfully",
            document_url=doc_info['document_url'],
            jobs_exported=1
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/batches/{batch_id}/google-sheets", response_model=ExportResponse)
async def export_batch_to_google_sheets(
    batch_id: str,
    request: BatchExportToGoogleRequest,
    db: Session = Depends(get_db)
):
    """
    Export a batch of jobs to Google Sheets.

    Creates a new spreadsheet with:
    - Batch Summary sheet
    - BACOWR Articles sheet with all jobs
    - Optional Google Docs for each article

    Endpoint: POST /api/v1/export/batches/{batch_id}/google-sheets

    NOTE: This endpoint USES existing services to fetch batch data.
    It does NOT modify BatchReviewService or any existing backend code.
    """
    # Fetch batch jobs from database
    # (In real implementation, would use BatchReviewService if available)
    # For now, fetch jobs directly with a filter

    # Determine which jobs to export
    if request.job_ids:
        # Export specific jobs
        jobs = db.query(Job).filter(
            Job.id.in_(request.job_ids),
            Job.status == "delivered"
        ).all()
    else:
        # For batch export, we'd ideally have a batch_id field on Job
        # For now, this is a placeholder - adjust based on actual schema
        jobs = db.query(Job).filter(
            Job.status == "delivered"
        ).limit(100).all()  # Limit for safety

    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No deliverable jobs found for export"
        )

    try:
        # Initialize exporters
        auth_manager = GoogleAuthManager()
        sheets_exporter = GoogleSheetsExporter(auth_manager)
        docs_exporter = GoogleDocsExporter(auth_manager)

        # Convert jobs to dict format
        job_data_list = []
        for job in jobs:
            job_data_list.append({
                'id': job.id,
                'created_at': job.created_at,
                'publisher_domain': job.publisher_domain,
                'target_url': job.target_url,
                'anchor_text': job.anchor_text,
                'status': job.status,
                'article_text': job.article_text,
                'qc_report': job.qc_report,
                'actual_cost': job.actual_cost or job.estimated_cost
            })

        # Create Google Docs if requested
        doc_urls = {}
        if request.create_docs:
            for job_data in job_data_list:
                if job_data.get('article_text'):
                    try:
                        doc_info = docs_exporter.export_job_to_doc(
                            job_data,
                            share_with_email=request.share_with_email
                        )
                        doc_urls[job_data['id']] = doc_info['document_url']
                    except Exception as e:
                        print(f"Warning: Failed to create doc for {job_data['id']}: {e}")

        # Export batch to Google Sheets
        batch_name = request.batch_name or batch_id
        export_result = sheets_exporter.export_batch(
            batch_jobs=job_data_list,
            batch_name=batch_name,
            doc_urls=doc_urls,
            share_with_email=request.share_with_email
        )

        return ExportResponse(
            success=True,
            message=f"Batch exported successfully: {export_result['exported']}/{export_result['total_jobs']} jobs",
            spreadsheet_url=export_result['spreadsheet_url'],
            jobs_exported=export_result['exported']
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch export failed: {str(e)}"
        )


@router.get("/google/auth/status")
async def get_google_auth_status():
    """
    Check Google authentication status.

    Returns credentials info and validation results.

    Endpoint: GET /api/v1/export/google/auth/status
    """
    try:
        auth_manager = GoogleAuthManager()

        # Validate credentials file
        validation = GoogleAuthManager.validate_credentials_file(
            auth_manager.credentials_path
        )

        return {
            "credentials_path": auth_manager.credentials_path,
            "validation": validation,
            "instructions": GoogleAuthManager.create_service_account_instructions()
        }

    except Exception as e:
        return {
            "error": str(e),
            "instructions": GoogleAuthManager.create_service_account_instructions()
        }
