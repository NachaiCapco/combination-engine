from pathlib import Path
from typing import Tuple
import re
import pandas as pd
from app.core.config import STORAGE_PATH
from app.core.utils_io import normalize_cell, assign_by_path

def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", name).strip("_") or "TestForgeSuite"

def setup_workspace(test_name: str) -> Tuple[Path, Path, Path]:
    root = STORAGE_PATH / safe_name(test_name)
    gen = root / "generated"
    rep = root / "Report"
    gen.mkdir(parents=True, exist_ok=True)
    rep.mkdir(parents=True, exist_ok=True)
    return root, gen, rep

ROBOT_HEADER = """*** Settings ***
Library    RequestsLibrary
Library    JSONLibrary
Library    Collections
Library    BuiltIn
Suite Setup    Create Session    api    {base_url}

*** Test Cases ***
"""

# Assertion operators for dynamic validation
ASSERTION_OPERATORS = {
    "eq": "eq",           # Equal (default)
    "ne": "ne",           # Not equal
    "gt": "gt",           # Greater than
    "lt": "lt",           # Less than
    "contains": "contains",  # Substring present
    "regex": "regex",     # Regular expression match
    "between": "between", # Numeric range (low,high)
    # Type and structure validation
    "is_null": "is_null",         # Field is null
    "is_not_null": "is_not_null", # Field is not null
    "is_empty": "is_empty",       # String/array/object is empty
    "is_not_empty": "is_not_empty", # String/array/object is not empty
    "is_array": "is_array",       # Field is array
    "is_object": "is_object",     # Field is object
    "is_string": "is_string",     # Field is string
    "is_number": "is_number",     # Field is number
    "is_bool": "is_bool",         # Field is boolean
}

def parse_field_meta(raw: str):
    """
    Parse field with operator and type tag.
    Examples:
        "age:gt[Type:int]" -> ("age", "gt", "int")
        "score:between[Type:float]" -> ("score", "between", "float")
        "name[Type:string]" -> ("name", "eq", "string")
        "active[Type:bool]" -> ("active", "eq", "bool")
        "id" -> ("id", "eq", None)
    
    Args:
        raw: Raw field string with optional operator and type tag
    
    Returns:
        tuple: (field_name, operator, data_type)
    """
    # Extract type tag if present: [Type:int], [Type:float], etc.
    type_match = re.search(r'\[Type:([^]]+)\]\s*$', raw, flags=re.IGNORECASE)
    dtype = type_match.group(1).strip().lower() if type_match else None
    
    # Remove type tag from string
    core = re.sub(r'\[Type:[^]]+\]\s*$', '', raw, flags=re.IGNORECASE).strip()
    
    # Parse operator from remaining string
    if ":" in core:
        parts = core.rsplit(":", 1)
        field = parts[0].strip()
        op = parts[1].strip().lower()
        if op not in ASSERTION_OPERATORS:
            op = "eq"  # fallback to default
    else:
        field = core
        op = "eq"  # default operator
    
    return field, op, dtype

def cast_value(value_raw: str, dtype: str):
    """
    Cast string value to appropriate type.
    
    Args:
        value_raw: Raw string value
        dtype: Target data type (int, float, bool, string)
    
    Returns:
        Casted value or original string if conversion fails
    """
    if dtype is None or dtype == "string":
        return value_raw
    
    if dtype in ("int", "integer"):
        try:
            return int(value_raw)
        except (ValueError, TypeError):
            return value_raw
    
    if dtype in ("float", "double", "number"):
        try:
            return float(value_raw)
        except (ValueError, TypeError):
            return value_raw
    
    if dtype in ("bool", "boolean"):
        v = str(value_raw).strip().lower()
        return v in ("1", "true", "yes", "y", "t")
    
    return value_raw

def parse_assertion(field_key: str, expected_raw: str):
    """
    DEPRECATED: Use parse_field_meta instead.
    Kept for backward compatibility.
    """
    field, op, _ = parse_field_meta(field_key)
    return field, op, expected_raw

def python_repr_for_robot(value):
    """
    Convert Python value to a repr string that can be used in Robot's Evaluate keyword.
    This creates a Python expression that will be evaluated to create proper JSON.

    Args:
        value: Python value (None, bool, int, float, str, list, dict)

    Returns:
        str: Python repr string
    """
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        # Escape backslashes and quotes
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        return f'"{escaped}"'
    if isinstance(value, list):
        items = ', '.join([python_repr_for_robot(item) for item in value])
        return f'[{items}]'
    if isinstance(value, dict):
        items = ', '.join([f'"{k}": {python_repr_for_robot(v)}' for k, v in value.items()])
        return f'{{{items}}}'
    # Fallback
    return repr(value)

def generate_robot_cases_from_excel(excel_path: Path, gen_dir: Path):
    df = pd.read_excel(excel_path, sheet_name=0, dtype=str).fillna("")
    tests = []
    
    # Extract base URL from first row's endpoint
    base_url = "http://localhost"
    if len(df) > 0:
        first_endpoint = df.iloc[0].get("[API]endpoint", "")
        if first_endpoint.startswith("http"):
            # Parse base URL (e.g., http://mockoon.ariyanaragroup.com)
            parts = first_endpoint.split("/")
            if len(parts) >= 3:
                base_url = f"{parts[0]}//{parts[2]}"
    
    for i, row in df.iterrows():
        tc_name = f"TC_{i+1:03d}"
        endpoint = row.get("[API]endpoint", "")
        method = (row.get("[API]Method", "POST") or "POST").upper()
        resp_code = row.get("[Response][API]status", "")
        
        # Convert full URL to relative path if needed
        if endpoint.startswith("http"):
            endpoint = "/" + "/".join(endpoint.split("/")[3:])
        
        # Extract expected response data
        expected_body = {}
        expected_header = {}
        
        for k, v in row.items():
            if not v:
                continue
            if k.startswith("[Response][Body]"):
                raw = k.replace("[Response][Body]", "", 1)
                field_name, op, dtype = parse_field_meta(raw)
                # Store as tuple: (value, data_type)
                key = field_name + (":" + op if op != "eq" else "")
                expected_body[key] = (v, dtype)
            elif k.startswith("[Response][Header]"):
                raw = k.replace("[Response][Header]", "", 1)
                field_name, op, dtype = parse_field_meta(raw)
                key = field_name + (":" + op if op != "eq" else "")
                expected_header[key] = (v, dtype)
        
        # Extract request data with array expansion support
        # Support sentinel values: [EMPTY], [NULL], [EMPTY_ARRAY], [EMPTY_OBJECT]
        # normalize_cell() converts these to "", None, [], {}
        # Support array expansion: data.clientProfiles[].field with comma-separated values
        # Example: data.clientProfiles[].clientType = "ML,O" creates 2 array items

        # First pass: collect all body fields and detect array expansion patterns
        body_fields = {}
        array_expansion_map = {}  # Track which arrays need expansion

        for k, v in row.items():
            if k.startswith("[Request][Body]"):
                field = k.replace("[Request][Body]", "")
                # Strip type markers from field name: [Type:bool], [Type:int], etc.
                # Extract the clean field name without type information
                field_clean = re.sub(r'\[Type:[^\]]+\]', '', field)

                normalized = normalize_cell(v)

                if normalized is not None or str(v).strip().upper() == "[NULL]":
                    # Check if this field uses array expansion notation []
                    if "[]" in field_clean:
                        # Extract the array path (e.g., "data.clientProfiles")
                        array_path = field_clean.split("[]")[0].rstrip(".")
                        field_name = field_clean.split("[]")[1].lstrip(".") if "[]" in field_clean and len(field_clean.split("[]")) > 1 else ""

                        # Check if value contains comma (expansion trigger)
                        if isinstance(normalized, str) and "," in normalized:
                            # Split comma-separated values
                            values = [val.strip() for val in normalized.split(",")]
                            if array_path not in array_expansion_map:
                                array_expansion_map[array_path] = {"count": len(values), "fields": {}}
                            else:
                                # Update count if this field has more items
                                array_expansion_map[array_path]["count"] = max(
                                    array_expansion_map[array_path]["count"],
                                    len(values)
                                )
                            # Store the split values for this field
                            array_expansion_map[array_path]["fields"][field_name] = values
                        else:
                            # Single value - will be duplicated across all array items
                            if array_path not in array_expansion_map:
                                array_expansion_map[array_path] = {"count": 1, "fields": {}}
                            array_expansion_map[array_path]["fields"][field_name] = normalized
                    else:
                        # Regular field without array expansion
                        body_fields[field_clean] = normalized

        # Second pass: build the body with expanded arrays
        body = {}

        # First, process regular fields
        for field, value in body_fields.items():
            assign_by_path(body, field, value)

        # Then, process array expansions
        for array_path, expansion_info in array_expansion_map.items():
            count = expansion_info["count"]
            fields = expansion_info["fields"]

            # Create array items
            array_items = []
            for idx in range(count):
                item = {}
                for field_name, value in fields.items():
                    if isinstance(value, list):
                        # Use the corresponding value from the split list
                        item_value = value[idx] if idx < len(value) else value[-1]
                    else:
                        # Duplicate the single value across all items
                        item_value = value

                    # Build nested structure within the array item
                    if "." in field_name:
                        assign_by_path(item, field_name, item_value)
                    else:
                        item[field_name] = item_value

                array_items.append(item)

            # Assign the expanded array to the body
            assign_by_path(body, array_path, array_items)

        headers = {}
        for k, v in row.items():
            if k.startswith("[Request][Header]"):
                field = k.replace("[Request][Header]", "")
                normalized = normalize_cell(v)
                if normalized is not None or str(v).strip().upper() == "[NULL]":
                    # Keep original type (int, bool, str) for headers
                    # This preserves: 200 as int, "200" as str, true as bool
                    assign_by_path(headers, field, normalized)

        # Add default browser headers if not specified to avoid bot blocking by Cloudflare/WAF
        # Cloudflare checks multiple headers to detect bots, not just User-Agent
        default_browser_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

        # Apply default headers only if not already specified by user
        for key, value in default_browser_headers.items():
            if key not in headers:
                headers[key] = value

        params = {}
        for k, v in row.items():
            if k.startswith("[Request][Params]"):
                field = k.replace("[Request][Params]", "")
                normalized = normalize_cell(v)
                if normalized is not None or str(v).strip().upper() == "[NULL]":
                    assign_by_path(params, field, normalized)

        query = {}
        for k, v in row.items():
            if k.startswith("[Request][Query]"):
                field = k.replace("[Request][Query]", "")
                normalized = normalize_cell(v)
                if normalized is not None or str(v).strip().upper() == "[NULL]":
                    assign_by_path(query, field, normalized)


        lines = [ROBOT_HEADER.format(base_url=base_url)]
        lines.append(f"{tc_name}")

        # Add delay to prevent rate limiting and bot detection
        # This makes execution pattern look more human-like and avoids triggering Cloudflare
        lines.append(f"    Sleep    0.5s")

        # Log API request details
        lines.append(f"    Log    ========== REQUEST ==========    console=yes")
        lines.append(f"    Log    Method: {method}    console=yes")
        lines.append(f"    Log    Endpoint: {endpoint}    console=yes")
        
        # Build request parameters
        # For headers: use Create Dictionary with proper string formatting
        # HTTP headers MUST be strings per HTTP spec and urllib3 validation
        # For body: use json.dumps() for proper JSON serialization (None → null, True/False → true/false)
        if headers:
            # Build Create Dictionary line with key=value pairs
            # All values are formatted as their literal representation for Robot
            dict_items = []
            for k, v in headers.items():
                # Escape special characters in key
                key_escaped = k.replace('=', '\\=').replace(' ', '\\ ')
                # Format value as string representation
                value_str = str(v)
                dict_items.append(f"{key_escaped}={value_str}")

            lines.append(f"    ${'{'}headers{'}'}=    Create Dictionary    {'    '.join(dict_items)}")
            lines.append(f"    Log    Headers: ${'{'}headers{'}'}    console=yes")
        if params:
            py_dict = python_repr_for_robot(params)
            lines.append(f"    ${'{'}params{'}'}=    Evaluate    {py_dict}")
            lines.append(f"    Log    Params: ${'{'}params{'}'}    console=yes")
        if query:
            py_dict = python_repr_for_robot(query)
            lines.append(f"    ${'{'}query{'}'}=    Evaluate    {py_dict}")
            lines.append(f"    Log    Query: ${'{'}query{'}'}    console=yes")
        if body:
            py_dict = python_repr_for_robot(body)
            # Use json.dumps() to properly serialize Python dict to JSON string
            # This converts: True → true, False → false, None → null
            lines.append(f"    ${'{'}payload{'}'}=    Evaluate    json.dumps({py_dict})    modules=json")
            lines.append(f"    Log    Body: ${'{'}payload{'}'}    console=yes")

        # Ensure Content-Type header is set when sending JSON
        if body and headers:
            lines.append(f"    Set To Dictionary    ${'{'}headers{'}'}    Content-Type=application/json")
        elif body:
            lines.append(f"    ${'{'}headers{'}'}=    Create Dictionary    Content-Type=application/json")

        # Build API call with only the parameters that exist
        call_parts = [f"${'{'}resp{'}'}=", f"{method} On Session", "api", endpoint]
        if query:
            call_parts.append(f"params=${'{'}query{'}'}")
        if headers or body:
            call_parts.append(f"headers=${'{'}headers{'}'}")
        if body:
            # Use data= parameter with JSON string for proper serialization
            call_parts.append(f"data=${'{'}payload{'}'}")
        
        # Always add expected_status=any to prevent RequestsLibrary from raising HTTPError
        # This allows the test to validate the actual status code instead
        call_parts.append("expected_status=any")
        
        lines.append("    " + "    ".join(call_parts))
        
        # Log API response details
        lines.append(f"    Log    ========== RESPONSE ==========    console=yes")
        lines.append(f"    Log    Status Code: ${'{'}resp.status_code{'}'}    console=yes")
        lines.append(f"    Log    Response Headers: ${'{'}resp.headers{'}'}    console=yes")
        lines.append(f"    Log    Response Body: ${'{'}resp.text{'}'}    console=yes")
        
        # Validate status code
        if str(resp_code).strip():
            lines.append(f"    Should Be Equal As Integers    ${'{'}resp.status_code{'}'}    {resp_code}")
        
        # Validate response headers
        if expected_header:
            for raw_key, (header_value_raw, dtype) in expected_header.items():
                field_name, op, _ = parse_field_meta(raw_key)
                header_value = cast_value(header_value_raw, dtype)
                
                # Headers support: eq, ne, contains, regex
                if op == "ne":
                    lines.append(f"    Should Not Be Equal    ${'{'}resp.headers['{field_name}']{'}'}    {header_value}")
                elif op == "contains":
                    lines.append(f"    Should Contain    ${'{'}resp.headers['{field_name}']{'}'}    {header_value}")
                elif op == "regex":
                    lines.append(f"    Should Match Regexp    ${'{'}resp.headers['{field_name}']{'}'}    {header_value}")
                else:  # eq (default)
                    lines.append(f"    Should Be Equal    ${'{'}resp.headers['{field_name}']{'}'}    {header_value}")
        
        # Validate response body
        if expected_body:
            lines.append(f"    ${'{'}json{'}'}=    Set Variable    ${'{'}resp.json(){'}'}")
            for raw_key, (expected_value_raw, dtype) in expected_body.items():
                field_name, op, _ = parse_field_meta(raw_key)
                expected_value = cast_value(expected_value_raw, dtype)

                # Check if this uses array search notation []
                if "[]" in field_name:
                    # Array search: data.eligibleProducts[].prodCode
                    # Split into array_path and search_field
                    parts = field_name.split("[]")
                    array_path = parts[0].rstrip(".")
                    search_field = parts[1].lstrip(".") if len(parts) > 1 and parts[1] else ""

                    # Generate code to search through array
                    lines.append(f"    # Search array: {field_name}")
                    lines.append(f"    ${'{'}array{'}'}=    Get Value From Json    ${'{'}json{'}'}    $.{array_path}")
                    lines.append(f"    ${'{'}found{'}'}=    Set Variable    ${{False}}")
                    lines.append(f"    FOR    ${'{'}item{'}'}    IN    @{'{'}array[0]{'}'}")

                    if search_field:
                        # Search for specific field in array items
                        if "." in search_field:
                            # Nested field: use Evaluate to access
                            search_expr = ".".join([f"$item['{part}']" for part in search_field.split(".")])
                            lines.append(f"        ${'{'}item_value{'}'}=    Evaluate    {search_expr}")
                        else:
                            # Simple field
                            lines.append(f"        ${'{'}item_value{'}'}=    Set Variable    ${'{'}item[{repr(search_field)}]{'}'}")

                        # Check if value matches
                        # Use Robot's Run Keyword And Return Status for safe comparison
                        lines.append(f"        ${'{'}matches{'}'}=    Run Keyword And Return Status    Should Be Equal    ${'{'}item_value{'}'}    {expected_value}")
                        lines.append(f"        IF    ${'{'}matches{'}'}")
                        lines.append(f"            ${'{'}found{'}'}=    Set Variable    ${{True}}")
                        lines.append(f"            Exit For Loop")
                        lines.append(f"        END")
                    else:
                        # Search for value directly in array (no field specified)
                        # Use Robot's Run Keyword And Return Status for safe comparison
                        lines.append(f"        ${'{'}matches{'}'}=    Run Keyword And Return Status    Should Be Equal    ${'{'}item{'}'}    {expected_value}")
                        lines.append(f"        IF    ${'{'}matches{'}'}")
                        lines.append(f"            ${'{'}found{'}'}=    Set Variable    ${{True}}")
                        lines.append(f"            Exit For Loop")
                        lines.append(f"        END")

                    lines.append(f"    END")
                    lines.append(f"    Should Be True    ${'{'}found{'}'}    msg=Value '{expected_value}' not found in array {field_name}")
                    continue

                # Regular field validation (no array search)
                lines.append(f"    ${'{'}value{'}'}=    Get Value From Json    ${'{'}json{'}'}    $.{field_name}")
                
                # Type and structure validation operators
                if op == "is_null":
                    lines.append(f"    Should Be Equal    ${'{'}value[0]{'}'}    ${'{'}None{'}'}")
                elif op == "is_not_null":
                    lines.append(f"    Should Not Be Equal    ${'{'}value[0]{'}'}    ${'{'}None{'}'}")
                elif op == "is_empty":
                    # Works for strings, arrays, objects
                    lines.append(f"    Should Be Empty    ${'{'}value[0]{'}'}")
                elif op == "is_not_empty":
                    lines.append(f"    Should Not Be Empty    ${'{'}value[0]{'}'}")
                elif op == "is_array":
                    lines.append(f"    Should Be True    isinstance(${'{'}value[0]{'}'}, list)")
                elif op == "is_object":
                    lines.append(f"    Should Be True    isinstance(${'{'}value[0]{'}'}, dict)")
                elif op == "is_string":
                    lines.append(f"    Should Be True    isinstance(${'{'}value[0]{'}'}, str)")
                elif op == "is_number":
                    lines.append(f"    Should Be True    isinstance(${'{'}value[0]{'}'}, (int, float))")
                elif op == "is_bool":
                    lines.append(f"    Should Be True    isinstance(${'{'}value[0]{'}'}, bool)")
                # Numeric comparison operators
                elif op in ("gt", "lt", "between"):
                    lines.append(f"    ${'{'}num{'}'}=    Convert To Number    ${'{'}value[0]{'}'}")
                    if op == "gt":
                        lines.append(f"    Should Be True    ${'{'}num{'}'} > {expected_value}")
                    elif op == "lt":
                        lines.append(f"    Should Be True    ${'{'}num{'}'} < {expected_value}")
                    elif op == "between":
                        # Expected format: "low,high" or "low:high" or "low;high"
                        bounds = [b.strip() for b in re.split(r'[,;:]', str(expected_value_raw)) if b.strip()]
                        low = cast_value(bounds[0], dtype) if len(bounds) > 0 else 0
                        high = cast_value(bounds[1], dtype) if len(bounds) > 1 else low
                        lines.append(f"    Should Be True    ${'{'}num{'}'} >= {low} and ${'{'}num{'}'} <= {high}")
                # Value comparison operators
                elif op == "eq":
                    if dtype in ("int", "integer"):
                        lines.append(f"    Should Be Equal As Integers    ${'{'}value[0]{'}'}    {expected_value}")
                    elif dtype in ("float", "double", "number"):
                        lines.append(f"    Should Be Equal As Numbers    ${'{'}value[0]{'}'}    {expected_value}")
                    elif dtype in ("bool", "boolean"):
                        # Use Robot Framework's built-in boolean variables ${True} and ${False}
                        bool_var = "${True}" if expected_value else "${False}"
                        lines.append(f"    Should Be Equal    ${'{'}value[0]{'}'}    {bool_var}")
                    else:
                        lines.append(f"    Should Be Equal    ${'{'}value[0]{'}'}    {expected_value}")
                elif op == "ne":
                    lines.append(f"    Should Not Be Equal    ${'{'}value[0]{'}'}    {expected_value}")
                elif op == "contains":
                    lines.append(f"    Should Contain    ${'{'}value[0]{'}'}    {expected_value}")
                elif op == "regex":
                    lines.append(f"    Should Match Regexp    ${'{'}value[0]{'}'}    {expected_value}")
                else:
                    # Fallback to equality
                    lines.append(f"    Should Be Equal    ${'{'}value[0]{'}'}    {expected_value}")

        content = "\n".join(lines) + "\n"
        (gen_dir / f"{tc_name}.robot").write_text(content, encoding="utf-8")
        tests.append(tc_name)
    return tests
