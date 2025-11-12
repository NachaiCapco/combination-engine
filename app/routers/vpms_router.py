"""
VPMS API Router

Endpoints for Prudential VPMS (Vulnerable Population Management System) API testing.
All endpoints use hardcoded VPMS authentication and headers.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Request
from app.services.vpms.vpms_compile_service import setup_workspace, generate_robot_cases_from_excel
from app.services.vpms import get_auth_token, get_auth_header, clear_token_cache

router = APIRouter(prefix="/api/v1/vpms", tags=["VPMS"])


@router.post("/compile-test-case")
async def vpms_compile_test_case(
    request: Request,
    testName: str = Body(..., embed=True),
    file: UploadFile = File(...)
):
    """
    Compile test cases for VPMS API with authentication.

    This endpoint:
    - Accepts Excel file with test case definitions
    - Generates Robot Framework test files with VPMS authentication
    - Automatically adds Bearer token and required headers

    **Hardcoded Headers:**
    - Ocp-Apim-Subscription-Key: e29f676c721a4ebb997f04f0b18e4942
    - Content-Type: application/json
    - Cookie: fpc=AtSS-2c1yG5BgaFl9lOTCVw; x-ms-gateway-slice=estsfd
    - Authorization: Bearer <token from VPMS auth API>

    **Args:**
    - testName: Name for the test suite
    - file: Excel file (.xlsx) with test definitions

    **Returns:**
    - status: Compilation status
    - testName: Name of the compiled test suite
    - cases: Number of test cases generated
    - run_url: URL to execute the test cases
    """
    try:
        root, gen, rep = setup_workspace(testName)
        raw_path = root / "rawData.xlsx"
        content = await file.read()

        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        raw_path.write_bytes(content)
        tests = generate_robot_cases_from_excel(raw_path, gen)

        # Include full base URL so clients get an absolute run URL
        run_url = f"{request.base_url}api/v1/run-test-case/{testName}/stream"

        return {
            "status": "compiled",
            "testName": testName,
            "cases": len(tests),
            "run_url": run_url,
            "message": "Test cases compiled with VPMS authentication"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"VPMS compile error: {str(e)}"
        )


@router.get("/auth/token")
async def get_vpms_auth_token(force_refresh: bool = False):
    """
    Get current VPMS authentication token.

    This endpoint fetches the OAuth Bearer token from the VPMS auth API.
    Tokens are cached in memory and automatically refreshed when expired.

    **Query Parameters:**
    - force_refresh: Force fetching a new token (default: false)

    **Returns:**
    - access_token: The Bearer token (first 50 characters shown)
    - cached: Whether the token was retrieved from cache
    - message: Status message
    """
    try:
        token = get_auth_token(force_refresh=force_refresh)

        return {
            "access_token": f"{token[:50]}...",
            "cached": not force_refresh,
            "message": "VPMS auth token retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get VPMS auth token: {str(e)}"
        )


@router.get("/auth/header")
async def get_vpms_authorization_header():
    """
    Get VPMS Authorization header.

    Returns the complete Authorization header with Bearer token
    that can be used for VPMS API requests.

    **Returns:**
    - authorization: The Authorization header value
    - format: Header format description
    """
    try:
        auth_header = get_auth_header()

        return {
            "authorization": auth_header["Authorization"][:70] + "...",
            "format": "Bearer <token>",
            "message": "VPMS authorization header generated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get VPMS auth header: {str(e)}"
        )


@router.post("/auth/clear-cache")
async def clear_vpms_token_cache():
    """
    Clear the cached VPMS authentication token.

    Forces the next token request to fetch a fresh token from the auth API.
    Useful for testing or when the token needs to be refreshed manually.

    **Returns:**
    - status: Operation status
    - message: Confirmation message
    """
    try:
        clear_token_cache()

        return {
            "status": "success",
            "message": "VPMS auth token cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear VPMS token cache: {str(e)}"
        )


@router.get("/info")
async def vpms_info():
    """
    Get VPMS service information.

    Returns configuration details about the VPMS service including
    the auth endpoint and hardcoded headers.

    **Returns:**
    - endpoint: VPMS auth API endpoint
    - headers: Hardcoded headers used for authentication
    - features: List of features provided by VPMS service
    """
    return {
        "service": "VPMS (Vulnerable Population Management System)",
        "provider": "Prudential Singapore",
        "auth_endpoint": "Not configured - Add to vpms_auth_service.py",
        "hardcoded_headers": {
            "Ocp-Apim-Subscription-Key": "Not configured",
            "Content-Type": "application/json",
            "Cookie": "Not configured"
        },
        "features": [
            "Automatic OAuth token management",
            "In-memory token caching",
            "Bearer token authentication",
            "Robot Framework test generation",
            "Hardcoded VPMS-specific headers"
        ],
        "network_requirement": "Requires Prudential VPN or internal network access",
        "setup_instructions": "Configure credentials in app/services/vpms/vpms_auth_service.py and app/services/vpms/vpms_compile_service.py"
    }
