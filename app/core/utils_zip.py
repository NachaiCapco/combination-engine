import os, zipfile
from pathlib import Path

def make_zip_from_dir(src_dir: Path, zip_path: Path):
    src_dir = Path(src_dir)
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(src_dir):
            for f in files:
                full = Path(root) / f
                arc = full.relative_to(src_dir.parent)
                z.write(full, arcname=str(arc))
    return zip_path
