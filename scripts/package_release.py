#!/usr/bin/env python3
"""Create a portable skill-only release with a SHA-256 checksum."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)
archive = args.output_dir / 'interior-proposal-pdf-v1.0.0.zip'
files = [ROOT / 'SKILL.md', ROOT / 'LICENSE']
for dirname in ('agents', 'scripts', 'references', 'assets'):
    files.extend(p for p in (ROOT / dirname).rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'
                 and p.name != 'package_release.py')
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        info = zipfile.ZipInfo(f'{ROOT.name}/{p.relative_to(ROOT).as_posix()}', (2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        z.writestr(info, p.read_bytes())
checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
(args.output_dir / 'SHA256SUMS').write_text(f'{checksum}  {archive.name}\n')
print(archive)
print(checksum)
