from typing import Any, Dict, List, Tuple
import io, re, json
import pandas as pd

def read_table(content: bytes, filename: str, allow_different_lengths: bool = False) -> pd.DataFrame:
    """
    Read CSV or Excel file and return DataFrame.
    
    Supports:
        - .csv (comma-separated values)
        - .xlsx/.xls (Excel, always reads first sheet)
    
    Auto-detects format by:
        1. Magic bytes (ZIP signature for Excel, text for CSV)
        2. Fallback to filename extension
    
    Args:
        content: File content as bytes
        filename: Original filename (for format detection)
        allow_different_lengths: If True, skip validation for equal-length columns (for combination generation)
    
    Returns:
        DataFrame with all cells as strings, empty cells as ""
    
    Raises:
        ValueError: If file format is unsupported or columns have unequal lengths
    """
    filename_lower = filename.lower()
    
    # Detect file type by magic bytes (more reliable than extension)
    is_excel = content[:4] == b'PK\x03\x04' or content[:4] == b'PK\x05\x06'  # ZIP signature
    is_csv_by_ext = filename_lower.endswith('.csv')
    
    # Read based on content type with fallback
    df = None
    last_error = None
    
    # Strategy 1: Try Excel first if magic bytes indicate ZIP
    if is_excel:
        try:
            df = pd.read_excel(
                io.BytesIO(content), 
                sheet_name=0,
                dtype=str,
                engine='openpyxl'
            )
        except Exception as e:
            last_error = f"Excel read failed: {str(e)}"
    
    # Strategy 2: Try CSV if not Excel or Excel failed
    if df is None:
        try:
            df = pd.read_csv(
                io.BytesIO(content), 
                dtype=str, 
                encoding='utf-8-sig'  # Handle BOM
            )
        except Exception as e:
            if last_error:
                # Both failed
                raise ValueError(
                    f"Failed to read {filename}. "
                    f"Excel error: {last_error}. CSV error: {str(e)}"
                )
            last_error = f"CSV read failed: {str(e)}"
    
    # If still None, neither format worked
    if df is None:
        raise ValueError(
            f"Unsupported or corrupted file: {filename}. "
            f"Error: {last_error}"
        )
    
    # Fill NaN with empty string
    df = df.fillna("")
    
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Validate: parameter columns must have same number of values
    # Metadata columns (like [API]endpoint, [API]Method) can have single value
    if not df.empty and not allow_different_lengths:
        # Identify metadata vs parameter columns
        metadata_prefixes = ('[API]endpoint', '[API]Method', '[API]method')
        
        non_empty_counts = {}
        metadata_cols = []
        parameter_cols = []
        
        for col in df.columns:
            col_str = str(col).strip()
            count = df[col].astype(str).str.strip().ne('').sum()
            non_empty_counts[col_str] = count
            
            # Check if this is a metadata column
            is_metadata = any(col_str.lower().startswith(prefix.lower()) for prefix in metadata_prefixes)
            
            if is_metadata:
                metadata_cols.append(col_str)
            else:
                parameter_cols.append(col_str)
        
        # Validate only parameter columns have equal length
        if parameter_cols:
            param_counts = [non_empty_counts[col] for col in parameter_cols]
            unique_param_counts = set(param_counts)
            
            if len(unique_param_counts) > 1:
                param_count_dict = {col: non_empty_counts[col] for col in parameter_cols}
                raise ValueError(
                    f"Parameter columns must have the same number of values. "
                    f"Found: {param_count_dict}. "
                    f"Metadata columns like [API]endpoint can have single value. "
                    f"Please ensure all parameter columns have equal-length data."
                )
        
        # Warn if metadata columns have multiple values (unusual but allowed)
        for col in metadata_cols:
            if non_empty_counts[col] > 1:
                # This is allowed but unusual - metadata will be used in combinations
                pass
    
    return df

def normalize_cell(v: Any):
    """
    Normalize cell value with support for sentinel keywords.
    
    Sentinel Keywords:
        [EMPTY] or [EMPTY_STRING] → "" (empty string)
        [NULL] → None (JSON null)
        [EMPTY_ARRAY] → [] (empty array)
        [EMPTY_OBJECT] → {} (empty object)
        (blank cell) → None (omit field)
    
    Returns:
        Normalized value or sentinel value
    """
    if v is None: 
        return None
    
    s = str(v).strip()
    
    # Sentinel values (case-insensitive)
    s_upper = s.upper()
    if s_upper in ("[EMPTY]", "[EMPTY_STRING]"):
        return ""  # Explicit empty string
    if s_upper == "[NULL]":
        return None  # JSON null
    if s_upper == "[EMPTY_ARRAY]":
        return []  # Empty array
    if s_upper == "[EMPTY_OBJECT]":
        return {}  # Empty object
    
    # Blank cell = omit field
    if s == "": 
        return None
    
    # Boolean conversion
    if s.lower() == "true": 
        return True
    if s.lower() == "false": 
        return False
    
    # Numeric conversion
    try:
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            return int(s)
        f = float(s)
        return f
    except: 
        return s

def tokenize_body_path(path: str):
    parts = []
    for m in re.finditer(r"([^[.\]]+)|\[(\d+)\]", path):
        if m.group(1): parts.append(m.group(1))
        else: parts.append(int(m.group(2)))
    return parts

def assign_by_path(target: dict, path: str, value: Any):
    import re
    def tokens(p: str):
        out = []
        for m in re.finditer(r"([^[.\]]+)|\[(\d+)\]", p):
            if m.group(1): out.append(m.group(1))
            else: out.append(int(m.group(2)))
        return out
    obj = target
    ts = tokens(path)
    for i, t in enumerate(ts):
        last = i == len(ts) - 1
        if isinstance(t, str):
            if last: obj[t] = value
            else:
                nxt = ts[i+1]
                if t not in obj or obj[t] is None:
                    obj[t] = [] if isinstance(nxt, int) else {}
                obj = obj[t]
        else:
            if not isinstance(obj, list):
                obj_idx = []
                obj = []
            while len(obj) <= t: obj.append({})
            if last: obj[t] = value
            else:
                nxt = ts[i+1]
                if obj[t] is None: obj[t] = [] if isinstance(nxt, int) else {}
                obj = obj[t]

def apply_params(path: str, params: Dict[str, Any]) -> str:
    return re.sub(r"\{([^}]+)\}", lambda m: str(params.get(m.group(1), f"{{{m.group(1)}}}")), path)

def cartesian_product(arrays: List[List[Any]]):
    out = [[]]
    for arr in arrays:
        out = [prev + [v] for prev in out for v in arr]
    return out
