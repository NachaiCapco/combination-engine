#!/usr/bin/env python3
"""
Validate CSV/Excel files for TestForge combination generation.

Usage:
    python tools/validate_input.py <file.csv|file.xlsx>
    
Examples:
    python tools/validate_input.py data/input.csv
    python tools/validate_input.py data/input.xlsx
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, List

def validate_file(filepath: str) -> Dict[str, any]:
    """
    Validate input file for combination generation.
    
    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "rows": int,
            "columns": List[str],
            "non_empty_counts": Dict[str, int],
            "metadata_cols": List[str],
            "parameter_cols": List[str],
            "preview": List[Dict]
        }
    """
    path = Path(filepath)
    
    if not path.exists():
        return {
            "valid": False,
            "errors": [f"File not found: {filepath}"],
            "warnings": [],
            "rows": 0,
            "columns": [],
            "non_empty_counts": {},
            "metadata_cols": [],
            "parameter_cols": [],
            "preview": []
        }
    
    errors = []
    warnings = []
    
    # Read file based on extension
    try:
        ext = path.suffix.lower()
        if ext == '.csv':
            df = pd.read_csv(filepath, dtype=str, encoding='utf-8-sig')
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath, sheet_name=0, dtype=str, engine='openpyxl')
        else:
            return {
                "valid": False,
                "errors": [f"Unsupported format: {ext}. Use .csv, .xlsx, or .xls"],
                "warnings": [],
                "rows": 0,
                "columns": [],
                "non_empty_counts": {},
                "metadata_cols": [],
                "parameter_cols": [],
                "preview": []
            }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to read file: {str(e)}"],
            "warnings": [],
            "rows": 0,
            "columns": [],
            "non_empty_counts": {},
            "metadata_cols": [],
            "parameter_cols": [],
            "preview": []
        }
    
    # Fill NaN with empty string
    df = df.fillna("")
    
    # Get column info
    columns = df.columns.tolist()
    
    # Check for empty column names
    empty_cols = [i for i, col in enumerate(columns) if str(col).strip() == ""]
    if empty_cols:
        errors.append(f"Empty column headers at positions: {empty_cols}")
    
    # Remove completely empty rows
    df_clean = df.dropna(how='all')
    
    if df_clean.empty:
        errors.append("File contains no data (all rows are empty)")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "rows": 0,
            "columns": columns,
            "non_empty_counts": {},
            "metadata_cols": [],
            "parameter_cols": [],
            "preview": []
        }
    
    # Count non-empty values per column
    non_empty_counts = {}
    metadata_cols = []
    parameter_cols = []
    
    metadata_prefixes = ('[API]endpoint', '[API]Method', '[API]method')
    
    for col in columns:
        count = df_clean[col].astype(str).str.strip().ne('').sum()
        non_empty_counts[col] = count
        
        # Check if this is a metadata column
        is_metadata = any(str(col).lower().startswith(prefix.lower()) for prefix in metadata_prefixes)
        
        if is_metadata:
            metadata_cols.append(col)
        else:
            parameter_cols.append(col)
    
    # Check for completely empty columns
    empty_cols = [col for col, count in non_empty_counts.items() if count == 0]
    if empty_cols:
        warnings.append(f"Completely empty columns: {empty_cols}")
    
    # Validate only parameter columns have equal values
    if parameter_cols:
        param_counts = {col: non_empty_counts[col] for col in parameter_cols}
        unique_counts = set(param_counts.values())
        
        if len(unique_counts) > 1:
            errors.append(
                f"Parameter columns have unequal number of values: {param_counts}. "
                f"All parameter columns must have the same number of values."
            )
            
            # Show which columns are problematic
            max_count = max(param_counts.values())
            short_cols = [col for col, count in param_counts.items() if count < max_count]
            errors.append(
                f"Expected {max_count} values per parameter column. "
                f"Columns with fewer values: {short_cols}"
            )
    
    # Info about metadata columns
    if metadata_cols:
        for col in metadata_cols:
            count = non_empty_counts[col]
            if count > 1:
                warnings.append(
                    f"Metadata column '{col}' has {count} values. "
                    f"Normally metadata should have 1 value (will be broadcast to all combinations)."
                )
    
    # Generate preview (first 5 rows)
    preview = df_clean.head(5).to_dict('records')
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "rows": len(df_clean),
        "columns": columns,
        "non_empty_counts": non_empty_counts,
        "metadata_cols": metadata_cols,
        "parameter_cols": parameter_cols,
        "preview": preview
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    filepath = sys.argv[1]
    result = validate_file(filepath)
    
    # Print results
    print("\n" + "=" * 70)
    print("📋 TestForge Input File Validation")
    print("=" * 70)
    print(f"File: {filepath}")
    print(f"Status: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    print(f"Rows: {result['rows']}")
    print(f"Columns: {len(result['columns'])}")
    
    if result['columns']:
        print(f"\n{'Column Type':<15} {'Column Name':<40} {'Values':>10}")
        print("-" * 70)
        
        # Show metadata columns first
        for col in result.get('metadata_cols', []):
            count = result['non_empty_counts'].get(col, 0)
            status = "🔧" if count == 1 else "⚠️"
            print(f"{status} {'Metadata':<13} {col:<40} {count:>10}")
        
        # Then parameter columns
        for col in result.get('parameter_cols', []):
            count = result['non_empty_counts'].get(col, 0)
            status = "✅" if count > 0 else "❌"
            print(f"{status} {'Parameter':<13} {col:<40} {count:>10}")
    
    if result['warnings']:
        print(f"\n{'⚠️  WARNINGS':}")
        print("-" * 70)
        for warning in result['warnings']:
            print(f"  • {warning}")
    
    if result['errors']:
        print(f"\n{'❌ ERRORS':}")
        print("-" * 70)
        for error in result['errors']:
            print(f"  • {error}")
    
    if result['preview']:
        print(f"\n{'📄 Preview (first 5 rows)':}")
        print("-" * 70)
        for i, row in enumerate(result['preview'], 1):
            print(f"\nRow {i}:")
            for col, val in row.items():
                display_val = f'"{val}"' if val else "<empty>"
                print(f"  {col}: {display_val}")
    
    print("\n" + "=" * 70)
    
    if result['valid']:
        print("✅ File is ready for TestForge!")
        
        # Calculate expected combinations based on parameter columns only
        param_counts = [result['non_empty_counts'][col] for col in result.get('parameter_cols', [])]
        if param_counts and all(c > 0 for c in param_counts):
            total_combinations = 1
            for count in param_counts:
                total_combinations *= count
            print(f"   Metadata columns: {len(result.get('metadata_cols', []))} (broadcast to all rows)")
            print(f"   Parameter columns: {len(result.get('parameter_cols', []))}")
            print(f"   Expected combinations: {total_combinations}")
        else:
            print(f"   Total columns: {len(result['columns'])}")
    else:
        print("❌ Please fix errors before uploading to TestForge")
    
    print("=" * 70 + "\n")
    
    sys.exit(0 if result['valid'] else 1)


if __name__ == "__main__":
    main()
