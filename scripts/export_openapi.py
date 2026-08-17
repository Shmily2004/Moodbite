"""Xuất đặc tả OpenAPI của backend ra `frontend/openapi.json`.

    python scripts/export_openapi.py

Chạy lệnh này MỖI KHI đổi schema/endpoint ở backend, rồi chạy tiếp:

    cd frontend
    npm run gen:api
    npm run typecheck

TypeScript sẽ chỉ thẳng ra mọi chỗ frontend phải sửa. Đây là cơ chế ngăn "sửa backend,
frontend vỡ mà không ai biết".

Trước đây lệnh này nằm trong README dưới dạng `python -c "..."` dài một dòng — kiểu lệnh
đó rất dễ hỏng khi dán vào PowerShell (dấu nháy bị nuốt). Viết thành script thì chạy
giống nhau ở mọi shell.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.presentation.api.main import create_app  # noqa: E402

OUTPUT = ROOT / "frontend" / "openapi.json"


def main() -> int:
    spec = create_app().openapi()
    OUTPUT.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    paths = spec.get("paths", {})
    admin = [p for p in paths if "/admin/" in p]
    print(f"Da ghi: {OUTPUT}")
    print(f"  tong so endpoint : {len(paths)}")
    print(f"  endpoint quan tri: {len(admin)}")
    for p in sorted(admin):
        print(f"    {p}")
    print("\nBuoc tiep theo:")
    print("  cd frontend")
    print("  npm run gen:api")
    print("  npm run typecheck")
    return 0


if __name__ == "__main__":
    sys.exit(main())
