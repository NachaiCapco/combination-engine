from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.services.combination_service import build_combination_excel
import io

router = APIRouter(prefix="/api/v1", tags=["combination"])

@router.post("/combination-test-case")
async def combination_test_case(file: UploadFile = File(...)):
    """
    Generate all parameter combinations from CSV or Excel file.
    
    **Supported formats:**
    - `.csv` — Comma-separated values
    - `.xlsx` / `.xls` — Excel (first sheet only)
    
    **Requirements:**
    - All columns must have the same number of values
    - No empty column headers
    
    **Returns:**
    - Excel file with two sheets:
        1. `combination` — All parameter combinations
        2. `note` — Instructions for filling expected results
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    try:
        data = build_combination_excel(content, file.filename or "input.xlsx")
    except ValueError as e:
        # Validation errors (file format, unequal columns, etc.)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation failed",
                "message": str(e),
                "hint": "Ensure all columns have equal number of values and use supported formats (.csv, .xlsx, .xls)"
            }
        )
    except Exception as e:
        # Unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Processing failed",
                "message": str(e)
            }
        )
    
    headers = {"Content-Disposition": 'attachment; filename="combination_testcases.xlsx"'}
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
