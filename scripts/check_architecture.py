"""Kiểm tra HƯỚNG PHỤ THUỘC của Clean Architecture. Chạy trong CI.

Quy tắc vàng: phụ thuộc chỉ được đi VÀO TRONG.

    presentation  ->  application  ->  domain
    infrastructure ->  application  ->  domain

  - domain KHÔNG được import bất kỳ tầng nào khác, và không được import framework
    (fastapi, pandas, torch...). Domain phải chạy được với Python thuần.
  - application chỉ được import domain (+ chính nó). Không fastapi, không pandas.
  - infrastructure được import domain/application, KHÔNG được import presentation.
  - presentation được import tất cả, nhưng KHÔNG được import trực tiếp
    infrastructure ngoài file lắp ráp (dependencies.py) - mọi thứ khác đi qua port.

Chạy: python scripts/check_architecture.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Tầng nào được phép import tầng nào (chỉ tính import nội bộ `src.*`).
ALLOWED_LAYERS = {
    "domain": {"domain"},
    "application": {"application", "domain"},
    "infrastructure": {"infrastructure", "application", "domain"},
    "presentation": {"presentation", "application", "domain", "infrastructure"},
}

# Thư viện ngoài bị CẤM ở từng tầng - đây là thứ giữ cho domain/application test được
# nhanh và không dính framework.
FORBIDDEN_EXTERNAL = {
    "domain": {"fastapi", "starlette", "pandas", "numpy", "torch", "ultralytics",
               "pydantic", "sqlalchemy", "joblib", "cv2", "PIL", "yaml", "requests"},
    "application": {"fastapi", "starlette", "pandas", "torch", "ultralytics",
                    "sqlalchemy", "joblib", "cv2", "yaml", "requests"},
}

# Ngoại lệ CÓ CHỦ ĐÍCH: file lắp ráp được phép biết adapter cụ thể - đó là việc của nó.
COMPOSITION_ROOT = {
    "src/presentation/api/dependencies.py",
    "src/presentation/api/main.py",
}

# Tầng ai/ là script train độc lập, không nằm trong luồng request - bỏ qua.
SKIPPED = ("src/infrastructure/ai/",)

# NỢ KỸ THUẬT ĐÃ BIẾT: được phép tồn tại nhưng LUÔN được in ra, không bị giấu.
# Mỗi mục phải có lý do và điều kiện để xoá.
KNOWN_DEBT = {
    "src/presentation/api/routers/spatial.py": (
        "Tính năng floorplan/3D đang TẠM DỪNG và chỉ bật khi MOODBITE_ENABLE_SPATIAL=1. "
        "Chưa tách port vì chưa chắc còn làm tiếp. Nếu khởi động lại tính năng này, "
        "phải tạo port DepthEstimator ở application/ports trước khi viết thêm code."
    ),
}


def layer_of(path: Path) -> str | None:
    parts = path.relative_to(SRC).parts
    return parts[0] if parts else None


def imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.append(node.module)
    return modules


def check() -> tuple[list[str], list[str]]:
    """(vi phạm phải sửa, nợ kỹ thuật đã biết)."""
    violations: list[str] = []
    debt: list[str] = []

    for py in sorted(SRC.rglob("*.py")):
        rel = py.relative_to(ROOT).as_posix()
        if any(rel.startswith(s) for s in SKIPPED):
            continue

        layer = layer_of(py)
        if layer not in ALLOWED_LAYERS:
            continue

        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            violations.append(f"{rel}: lỗi cú pháp - {exc}")
            continue

        for module in imported_modules(tree):
            root_pkg = module.split(".")[0]

            # 1. Import nội bộ giữa các tầng.
            if root_pkg == "src":
                parts = module.split(".")
                if len(parts) < 2:
                    continue
                target_layer = parts[1]
                if target_layer not in ALLOWED_LAYERS[layer]:
                    violations.append(
                        f"{rel}: tầng '{layer}' KHÔNG được import tầng "
                        f"'{target_layer}' ({module})"
                    )
                elif (
                    layer == "presentation"
                    and target_layer == "infrastructure"
                    and rel not in COMPOSITION_ROOT
                ):
                    message = (
                        f"{rel}: chỉ file lắp ráp ({', '.join(sorted(COMPOSITION_ROOT))}) "
                        f"mới được import infrastructure trực tiếp. "
                        f"Router phải dùng port qua Depends(...) - gặp: {module}"
                    )
                    if rel in KNOWN_DEBT:
                        debt.append(f"{message}\n      Lý do: {KNOWN_DEBT[rel]}")
                    else:
                        violations.append(message)
                continue

            # 2. Thư viện ngoài bị cấm ở tầng trong.
            if root_pkg in FORBIDDEN_EXTERNAL.get(layer, set()):
                violations.append(
                    f"{rel}: tầng '{layer}' KHÔNG được import thư viện ngoài "
                    f"'{root_pkg}' - phải giữ thuần Python để test nhanh và đổi được hạ tầng"
                )

    return violations, debt


def main() -> int:
    violations, debt = check()

    if debt:
        print("NO KY THUAT DA BIET (khong lam CI do, nhung dung de no lan rong):\n")
        for d in debt:
            print(f"  - {d}")
        print()

    if violations:
        print("VI PHAM HUONG PHU THUOC CLEAN ARCHITECTURE:\n")
        for v in violations:
            print(f"  - {v}")
        print(
            f"\nTong: {len(violations)} vi pham. "
            "Xem quy tac o dau file scripts/check_architecture.py"
        )
        return 1

    print("Clean Architecture OK: huong phu thuoc dung, khong co import cam.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
