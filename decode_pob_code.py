#!/usr/bin/env python3
from __future__ import annotations
import base64
import sys
import zlib
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit(f"用法：{sys.argv[0]} INPUT_CODE_FILE OUTPUT_XML")
code = Path(sys.argv[1]).read_text().strip()
code += "=" * ((4 - len(code) % 4) % 4)
raw = base64.urlsafe_b64decode(code)
xml = zlib.decompress(raw)
if b"<PathOfBuilding" not in xml[:4096]:
    raise SystemExit("輸入不是有效的 Path of Building XML")
Path(sys.argv[2]).write_bytes(xml)
print(f"已解碼：{sys.argv[2]} ({len(xml)} bytes)")
