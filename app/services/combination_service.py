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

def expand_array_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand columns with [] notation into indexed columns [0], [1], [2], etc.

    Example:
        Input column: [Request][Body]data.clientProfiles[].age
        Input value: "25,30,35"
        Output columns:
            - [Request][Body]data.clientProfiles[0].age = 25
            - [Request][Body]data.clientProfiles[1].age = 30
            - [Request][Body]data.clientProfiles[2].age = 35
    """
    # Find columns with [] notation
    array_columns = {}  # {base_path: [col_names]}

    for col in df.columns:
        if '[]' in col:
            # Extract the base path (everything before [])
            base = col.split('[]')[0] + '[]'
            if base not in array_columns:
                array_columns[base] = []
            array_columns[base].append(col)

    if not array_columns:
        # No array columns, return as-is
        return df

    # Determine max array size by inspecting all values
    max_array_size = 0
    for col in df.columns:
        if '[]' in col:
            for val in df[col]:
                if pd.notna(val) and val != "":
                    # Split by comma to count array elements
                    parts = str(val).split(',')
                    max_array_size = max(max_array_size, len(parts))

    if max_array_size == 0:
        # No data to expand
        return df

    # Create new dataframe with expanded columns
    new_columns = []
    new_data = []

    # Process each column
    for col in df.columns:
        if '[]' not in col:
            # Non-array column - keep as-is
            new_columns.append(col)
        else:
            # Array column - expand into [0], [1], [2], etc.
            for idx in range(max_array_size):
                expanded_col = col.replace('[]', f'[{idx}]')
                new_columns.append(expanded_col)

    # Process each row
    for _, row in df.iterrows():
        new_row = []
        for col in df.columns:
            if '[]' not in col:
                # Non-array column - copy value as-is
                new_row.append(row[col])
            else:
                # Array column - split and distribute values
                val = row[col]
                if pd.notna(val) and val != "":
                    # Split by comma
                    parts = [p.strip() for p in str(val).split(',')]
                    # Pad with empty strings if needed
                    while len(parts) < max_array_size:
                        parts.append("")
                    new_row.extend(parts[:max_array_size])
                else:
                    # Empty value - fill with empty strings
                    new_row.extend([""] * max_array_size)

        new_data.append(new_row)

    # Create new dataframe
    new_df = pd.DataFrame(new_data, columns=new_columns)
    return new_df

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

    # Expand array notation: columns with [] get expanded to [0], [1], [2], etc.
    out_df = expand_array_columns(out_df)
    
    # Use centralized note data
    note_df = pd.DataFrame(get_note_data())

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        out_df.to_excel(writer, index=False, sheet_name="combination")
        note_df.to_excel(writer, index=False, sheet_name="note")
    buf.seek(0)
    return buf.getvalue()
