"""Verify a newly exported demo PDF against the page contract and quote data."""
import argparse
import json
import re
import unicodedata
from pathlib import Path
from pypdf import PdfReader

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('pdf', type=Path)
args = parser.parse_args()
reader = PdfReader(args.pdf)
assert len(reader.pages) == 6, 'Expected exactly six pages'
texts = []
for i, page in enumerate(reader.pages, 1):
    assert abs(float(page.mediabox.width) - 960) < .2, f'Page {i}: width'
    assert abs(float(page.mediabox.height) - 540) < .2, f'Page {i}: height'
    text = page.extract_text()
    assert text.strip(), f'Page {i}: empty text'
    # PDF extractors may insert spaces between tracked letters and decompose accents.
    compact = re.sub(r'\s+', '', unicodedata.normalize('NFC', text)).casefold()
    assert 'demo' in compact, f'Page {i}: missing demo label; extracted={text[:500]!r}'
    texts.append(text)
combined = '\n'.join(texts)
compact_combined = re.sub(r'\s+', '', unicodedata.normalize('NFC', combined)).casefold()
for value in ('Lắng lại giữa nhịp đô thị', 'Sofa cong', '33.440.000', '6.200.000', '39.640.000', 'đế gỗ tông nâu sẫm'):
    expected = re.sub(r'\s+', '', unicodedata.normalize('NFC', value)).casefold()
    assert expected in compact_combined, f'Missing expected text: {value}'
print(json.dumps({'ok': True, 'page_count': 6, 'size_pt': [960, 540], 'text_and_prices': 'pass'}))
