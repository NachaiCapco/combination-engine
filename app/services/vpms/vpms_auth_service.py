"""
VPMS Authentication Token Service

Handles OAuth token retrieval and caching for VPMS API requests.
Token is cached in-memory with automatic expiry handling.
Hardcoded configuration for VPMS endpoint.
"""

import time
import requests
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# In-memory token cache
_token_cache: Dict[str, any] = {
    "access_token": None,
    "expires_at": 0
}

# VPMS Auth API configuration (hardcoded)
# TODO: Add your VPMS configuration here before running
VPMS_AUTH_CONFIG = {
    "enabled": True,
    "endpoint": "",  
    "token_type": "Bearer",
    # Hardcoded headers for VPMS auth request
    "headers": {
        "Ocp-Apim-Subscription-Key": "",  # Add your subscription key here
        "Cache-Control": "no-cache",
        "Cookie": ""  # Add your session cookie here
    }
}


def get_auth_token(force_refresh: bool = False) -> str:
    """
    Get valid authentication token. Returns cached token if available and not expired,
    otherwise fetches a new token from the auth API.

    Args:
        force_refresh: Force fetching a new token even if cached token is valid

    Returns:
        str: Valid access token

    Raises:
        requests.RequestException: If token retrieval fails
    """
    current_time = time.time()

    # Check if we have a valid cached token
    if not force_refresh and _token_cache["access_token"] and current_time < _token_cache["expires_at"]:
        logger.info("Using cached VPMS auth token")
        return _token_cache["access_token"]

    # Fetch new token
    logger.info("Fetching new VPMS auth token from API")
    token_data = _fetch_token_from_api()

    # Cache the token
    access_token = token_data.get("access_token")
    expires_in = int(token_data.get("expires_in", 3600))  # Default to 1 hour if not provided

    # Store token with expiry time (subtract 60 seconds for safety buffer)
    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = current_time + expires_in - 60

    logger.info(f"VPMS auth token cached successfully, expires in {expires_in} seconds")
    return access_token


def _fetch_token_from_api() -> Dict:
    """
    Fetch authentication token from the VPMS OAuth API.

    Returns:
        dict: Token response containing access_token, expires_in, etc.

    Raises:
        requests.RequestException: If API request fails
    """
    # Use hardcoded headers from config
    headers = VPMS_AUTH_CONFIG["headers"]

    try:
        response = requests.post(
            VPMS_AUTH_CONFIG["endpoint"],
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        token_data = response.json()

        if "access_token" not in token_data:
            raise ValueError("Response does not contain access_token")

        return token_data

    except requests.RequestException as e:
        logger.error(f"Failed to fetch VPMS auth token: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid VPMS token response: {e}")
        raise


def get_auth_header() -> Dict[str, str]:
    """
    Get authorization header with valid Bearer token for VPMS.

    Returns:
        dict: Dictionary with Authorization header

    Example:
        {"Authorization": "Bearer eyJ0eXAiOi..."}
    """
    token = get_auth_token()
    return {"Authorization": f"{VPMS_AUTH_CONFIG['token_type']} {token}"}


def clear_token_cache():
    """
    Clear the cached VPMS token. Useful for testing or forcing token refresh.
    """
    _token_cache["access_token"] = None
    _token_cache["expires_at"] = 0
    logger.info("VPMS auth token cache cleared")
