from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from app.services.compile_service import setup_workspace
from app.services.download_service import find_report_dir
from app.services.example_service import build_example_combination_excel
from app.core.utils_zip import make_zip_from_dir
from pathlib import Path
import tempfile
import io
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["download"])

@router.get("/download/example-combination-data")
async def download_example_combination_data():
    """Download example Excel template for combination test cases with sample data and instructions"""
    
    data = build_example_combination_excel()
    
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=example-combination-data.xlsx"}
    )

@router.get("/download/{testName}/{timestamp}")
async def download_report_by_timestamp(testName: str, timestamp: str):
    """Download specific report by timestamp"""
    root, gen, rep = setup_workspace(testName)
    report_dir = find_report_dir(rep, timestamp)
    if report_dir is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Report with timestamp {timestamp} not found for {testName}"
        )
    zip_filename = f"{testName}_Report_{timestamp}.zip"
    zip_path = Path(tempfile.gettempdir()) / zip_filename
    make_zip_from_dir(report_dir, zip_path)
    return FileResponse(path=zip_path, filename=zip_filename, media_type="application/zip")

@router.get("/download/{testName}")
async def download_latest_report(testName: str):
    """Download latest report (no timestamp specified)"""
    root, gen, rep = setup_workspace(testName)
    latest = find_report_dir(rep, timestamp=None)
    if latest is None:
        raise HTTPException(
            status_code=404, 
            detail=f"No reports found for {testName}"
        )
    # Extract timestamp from directory name
    timestamp = latest.name
    zip_filename = f"{testName}_Report_{timestamp}.zip"
    zip_path = Path(tempfile.gettempdir()) / zip_filename
    make_zip_from_dir(latest, zip_path)
    return FileResponse(path=zip_path, filename=zip_filename, media_type="application/zip")
