"""
VPMS (Prudential API) Services Package

This package contains services specifically configured for the Prudential VPMS API.
All configuration is hardcoded for the VPMS environment.

Modules:
    - vpms_auth_service: Handles OAuth token retrieval with hardcoded VPMS headers
    - vpms_compile_service: Generates Robot Framework tests with VPMS authentication
"""

from app.services.vpms.vpms_auth_service import (
    get_auth_token,
    get_auth_header,
    clear_token_cache
)

__all__ = [
    'get_auth_token',
    'get_auth_header',
    'clear_token_cache'
]
