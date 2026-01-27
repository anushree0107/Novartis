"""Reports API - Auto-generated report endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()


class ReportMetadata(BaseModel):
    report_id: str
    report_type: str
    title: str
    entity_type: str
    entity_id: str
    generated_at: str


def get_report_generator():
    from api.main import _report_generator
    if _report_generator is None:
        raise HTTPException(status_code=500, detail="ReportGenerator not initialized")
    return _report_generator


@router.get("/site/{site_id}", response_class=PlainTextResponse)
async def generate_site_report(site_id: str):
    """Generate a comprehensive site summary report."""
    import asyncio
    
    try:
        generator = get_report_generator()
        
        # Run synchronous report generation in thread pool
        try:
            report = await asyncio.wait_for(
                asyncio.to_thread(generator.generate_site_summary, site_id),
                timeout=300.0  # 5 minute timeout for report generation
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Report generation timed out after 5 minutes")
        
        return report.to_markdown()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/site/{site_id}/metadata", response_model=ReportMetadata)
async def get_site_report_metadata(site_id: str):
    """Get metadata for a site report."""
    try:
        generator = get_report_generator()
        report = generator.generate_site_summary(site_id)
        return ReportMetadata(
            report_id=report.report_id,
            report_type=report.report_type.value,
            title=report.title,
            entity_type=report.entity_type,
            entity_id=report.entity_id,
            generated_at=report.generated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/study/{study_id}", response_class=PlainTextResponse)
async def generate_study_report(study_id: str):
    """Generate a study overview report."""
    try:
        generator = get_report_generator()
        report = generator.generate_study_overview(study_id)
        return report.to_markdown()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly", response_class=PlainTextResponse)
async def generate_weekly_digest(study_id: Optional[str] = None):
    """Generate a weekly digest report."""
    try:
        generator = get_report_generator()
        report = generator.generate_weekly_digest(study_id)
        return report.to_markdown()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/site/{site_id}/json")
async def get_site_report_json(site_id: str):
    """Get site report as JSON."""
    try:
        generator = get_report_generator()
        report = generator.generate_site_summary(site_id)
        return report.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
