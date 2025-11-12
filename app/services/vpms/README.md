# VPMS Services Package

This package contains specialized services for the Prudential VPMS (Vulnerable Population Management System) API.

## Overview

The VPMS services use hardcoded configuration for the Prudential API endpoint and headers. **Configuration must be added before use.**

## ⚠️ Setup Required

**Before using VPMS services, you must configure the following files with your credentials:**

1. **`vpms_auth_service.py`** - Add auth endpoint, subscription key, and cookies
2. **`vpms_compile_service.py`** - Add subscription key and cookies

See "Configuration" section below for details.

## Structure

```
app/services/vpms/
├── __init__.py                 # Package initialization
├── vpms_auth_service.py        # Authentication token management
├── vpms_compile_service.py     # Robot Framework test generation
└── README.md                   # This file
```

## Components

### 1. vpms_auth_service.py

Handles OAuth token retrieval and caching for VPMS API requests.

**Configuration Required:**
- **Endpoint**: Add your VPMS auth endpoint URL
- **Headers**:
  - `Ocp-Apim-Subscription-Key`: Add your subscription key
  - `Cache-Control`: no-cache (pre-configured)
  - `Cookie`: Add your session cookie

**Features:**
- In-memory token caching with automatic expiry handling
- Returns Bearer tokens for Authorization headers
- Automatically refreshes tokens when expired (60-second safety buffer)

**Functions:**
```python
get_auth_token(force_refresh=False) -> str
    # Get valid authentication token (cached or fresh)

get_auth_header() -> Dict[str, str]
    # Get authorization header: {"Authorization": "Bearer <token>"}

clear_token_cache()
    # Clear cached token (useful for testing)
```

### 2. vpms_compile_service.py

Generates Robot Framework test cases from Excel files with VPMS-specific authentication.

**Configuration Required (added to all requests):**
- `Ocp-Apim-Subscription-Key`: Add your subscription key
- `Content-Type`: application/json (pre-configured)
- `Cookie`: Add your session cookie
- `Authorization`: Bearer <token from vpms_auth_service>

**Functions:**
```python
generate_robot_cases_from_excel(excel_path: Path, gen_dir: Path)
    # Generate Robot Framework test cases with VPMS authentication
```

## Usage

### Basic Usage

```python
from app.services.vpms import get_auth_token, get_auth_header
from app.services.vpms.vpms_compile_service import generate_robot_cases_from_excel
from pathlib import Path

# Get auth token (cached automatically)
token = get_auth_token()
print(f"Token: {token[:50]}...")

# Get authorization header
auth_header = get_auth_header()
print(f"Header: {auth_header}")
# Output: {"Authorization": "Bearer eyJ0eXAiOi..."}

# Generate test cases with VPMS authentication
excel_file = Path("data/single-life-example.xlsx")
output_dir = Path("workspace/generated")
generate_robot_cases_from_excel(excel_file, output_dir)
```

### Token Caching

The auth service automatically caches tokens in memory:

```python
from app.services.vpms import get_auth_token, clear_token_cache

# First call - fetches from API
token1 = get_auth_token()

# Second call - uses cached token
token2 = get_auth_token()  # Same as token1

# Force refresh
clear_token_cache()
token3 = get_auth_token(force_refresh=True)  # New token
```

## Network Requirements

The VPMS services require access to the Prudential internal network:
- Must be connected to Prudential VPN or internal network
- Endpoint: `pacs-api-internal-nprd.prudential.com.sg`

Running from outside the network will result in DNS resolution errors (expected behavior).

## Configuration

All configuration is **hardcoded** in this package. You must manually add your credentials to the following files:

### Step 1: Configure `vpms_auth_service.py`

Edit the `VPMS_AUTH_CONFIG` dictionary:

```python
VPMS_AUTH_CONFIG = {
    "enabled": True,
    "endpoint": "YOUR_AUTH_ENDPOINT_HERE",  # e.g., "https://pacs-api-internal-nprd.prudential.com.sg/inituat/vpmsd2c-api/oauth/token"
    "token_type": "Bearer",
    "headers": {
        "Ocp-Apim-Subscription-Key": "YOUR_SUBSCRIPTION_KEY_HERE",
        "Cache-Control": "no-cache",
        "Cookie": "YOUR_SESSION_COOKIE_HERE"
    }
}
```

### Step 2: Configure `vpms_compile_service.py`

Edit the `vpms_headers` dictionary (around line 304):

```python
vpms_headers = {
    "Ocp-Apim-Subscription-Key": "YOUR_SUBSCRIPTION_KEY_HERE",
    "Content-Type": "application/json",
    "Cookie": "YOUR_SESSION_COOKIE_HERE"
}
```

### Configuration Values Needed

| Setting | Where to Add | Example |
|---------|-------------|---------|
| Auth Endpoint | `vpms_auth_service.py` | `https://your-api.com/oauth/token` |
| Subscription Key | Both files | Your API subscription key |
| Session Cookie | Both files | Your browser session cookie |
| Token Type | `vpms_auth_service.py` | `Bearer` (pre-configured) |
| Content-Type | `vpms_compile_service.py` | `application/json` (pre-configured) |

⚠️ **Important**: Do not commit your credentials to version control!

## Differences from Generic Services

| Feature | Generic Services | VPMS Services |
|---------|-----------------|---------------|
| Configuration | Environment variables (.env) | Hardcoded |
| Headers | Browser-like headers | VPMS-specific headers |
| Auth Endpoint | Configurable | Fixed (Prudential VPMS) |
| Cookie | None | Hardcoded session cookie |
| Subscription Key | Configurable | Hardcoded |

## Security Note

⚠️ **IMPORTANT SECURITY WARNINGS:**

1. **Never commit credentials to version control**
   - The configuration files are set up with blank values
   - Add your credentials locally only
   - Add these files to `.gitignore` if they contain secrets

2. **Credentials are environment-specific**
   - Use only within the Prudential network
   - Do not expose publicly
   - Subscription keys and cookies are sensitive

3. **Session cookies expire**
   - Cookies will expire over time
   - Update them manually when authentication fails
   - Located in `vpms_auth_service.py` and `vpms_compile_service.py`

4. **Use .gitignore**
   - Consider adding:
     ```
     # Local VPMS configuration (if you create separate config files)
     app/services/vpms/*_local.py
     app/services/vpms/.credentials
     ```
