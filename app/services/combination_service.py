from typing import Any, Dict, List
import io
import pandas as pd
from app.core import utils_io as U
from app.services.note_data import get_note_data

EXPECTED_PREFIXES = (
    "[API]endpoint",
    "[API]Method",
    "[Request][Header]",
    "[Request][Params]",
    "[Request][Query]",
    "[Request][Body]",
)

def build_combination_excel(content: bytes, filename: str) -> bytes:
    df = U.read_table(content, filename, allow_different_lengths=True)
    headers = [str(h).strip() for h in list(df.columns)]
    rows = df.values.tolist()

    # Identify metadata vs parameter columns
    metadata_prefixes = ('[API]endpoint', '[API]Method', '[API]method')
    metadata_indices = []
    parameter_indices = []
    
    for i, h in enumerate(headers):
        is_metadata = any(h.lower().startswith(prefix.lower()) for prefix in metadata_prefixes)
        if is_metadata:
            metadata_indices.append(i)
        else:
            parameter_indices.append(i)
    
    # Collect values per column (ignore empty)
    per_col = [[] for _ in headers]
    metadata_values = {}  # Store single metadata value per column
    
    for r in rows:
        for i, _h in enumerate(headers):
            v = U.normalize_cell(r[i] if i < len(r) else None)
            if v is not None:
                if i in metadata_indices:
                    # Metadata: keep only first non-empty value
                    if i not in metadata_values:
                        metadata_values[i] = v
                else:
                    # Parameter: collect all values for combinations
                    per_col[i].append(v)
    
    # Set metadata columns to single value (will be broadcast)
    for i in metadata_indices:
        if i in metadata_values:
            per_col[i] = [metadata_values[i]]
        else:
            per_col[i] = [None]
    
    # Empty parameter column -> [None]
    for i in parameter_indices:
        if not per_col[i]:
            per_col[i] = [None]

    # Generate combinations
    combos = U.cartesian_product(per_col)
    out_rows: List[List[Any]] = []
    for combo in combos:
        out_row = []
        for i, h in enumerate(headers):
            val = combo[i]
            out_row.append("" if val is None else val)
        out_rows.append(out_row)

    out_df = pd.DataFrame(out_rows, columns=headers)
    
    # Use centralized note data
    note_df = pd.DataFrame(get_note_data())

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        out_df.to_excel(writer, index=False, sheet_name="combination")
        note_df.to_excel(writer, index=False, sheet_name="note")
    buf.seek(0)
    return buf.getvalue()
