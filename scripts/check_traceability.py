"""Kiểm MA TRẬN TRUY VẾT (`traceability.md`): mọi thứ nó trỏ tới phải THẬT SỰ TỒN TẠI.

    python scripts/check_traceability.py

VÌ SAO CÓ FILE NÀY: bản đầu của `traceability.md` ghi 10 đường dẫn thì 9 cái không tồn
tại. Bản viết lại 2026-08-19 ghi "kiểm lại bằng `python scripts/verify.py`" — nhưng
verify.py khi đó KHÔNG HỀ đọc file này, nên đến 2026-10-10 bảng đã thiếu 13/20 use case
và còn ghi Lớp 4 "chưa làm" dù đã xong từ lâu. Tài liệu chỉ đúng khi có MÁY kiểm nó.

Kiểm ba loại tham chiếu nằm trong dấu backtick:
  - đường dẫn (`src/.../x.py`, `frontend/apps/*/src/`)  -> file/thư mục phải tồn tại
  - tên test (`test_xxx`)                                -> phải có `def test_xxx` trong tests/
  - ký hiệu (`module.ham`, `Lop.thuoc_tinh`)             -> phải xuất hiện trong file đó

Dòng trích dẫn (bắt đầu bằng `>`) được BỎ QUA: đó là chỗ kể lại lịch sử, có thể nhắc tới
file cũ đã gỡ một cách có chủ đích.

Không kiểm được NGỮ NGHĨA (test có thật sự kiểm đúng yêu cầu không) — việc đó vẫn phải
đọc tay. Checker này chỉ chặn loại sai rẻ nhất và hay gặp nhất: trỏ vào thứ không có.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "traceability.md"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Đuôi file coi là "đường dẫn". Thiếu đuôi nào thì tham chiếu đó bị coi là chữ thường và
# KHÔNG được kiểm — nên liệt kê đủ những đuôi bảng thật sự dùng.
PATH_RE = re.compile(
    r"[\w.*-]+(?:/[\w.*-]+)+/?"                                   # có dấu '/'
    r"|[\w.-]+\.(?:py|md|json|jsonl|yml|yaml|ts|tsx|js|jsx|db)\b"  # tên file trần
)
TEST_RE = re.compile(r"^test_\w+$")
SYMBOL_RE = re.compile(r"^([A-Za-z_]\w*)\.([A-Za-z_]\w*)\*?$")
CODE_DIRS = ("src", "data_pipeline", "scripts")


def _python_files() -> list[Path]:
    files: list[Path] = []
    for d in CODE_DIRS:
        files += [p for p in (ROOT / d).rglob("*.py") if "__pycache__" not in p.parts]
    return files


def _test_names() -> set[str]:
    names: set[str] = set()
    for p in (ROOT / "tests").rglob("test_*.py"):
        # `\w` khớp cả chữ có dấu: nhiều test của dự án đặt tên tiếng Việt có dấu.
        names |= set(re.findall(r"^\s*def (test_\w+)\(", p.read_text(encoding="utf-8"), re.M))
    return names


def _path_exists(ref: str) -> bool:
    ref = ref.rstrip("/")
    if "*" in ref:
        return any(ROOT.glob(ref))
    if "/" in ref:
        return (ROOT / ref).exists()
    # Tên file trần (vd `CLAUDE.md`): tìm ở gốc trước, rồi ở mọi nơi.
    return (ROOT / ref).exists() or any(
        p for p in ROOT.rglob(ref) if "node_modules" not in p.parts
    )


def _symbol_exists(owner: str, attr: str, sources: dict[Path, str]) -> bool:
    # `owner` là tên module (dish_ranking) HOẶC tên lớp (Dish) — thử cả hai.
    candidates = [p for p in sources if p.stem == owner]
    candidates += [p for p, s in sources.items() if re.search(rf"^class {owner}\b", s, re.M)]
    return any(attr in sources[p] for p in candidates)


def find_problems(doc_text: str) -> tuple[list[str], int]:
    sources = {p: p.read_text(encoding="utf-8", errors="ignore") for p in _python_files()}
    tests = _test_names()
    problems: list[str] = []
    checked = 0

    for lineno, line in enumerate(doc_text.splitlines(), start=1):
        if line.lstrip().startswith(">"):
            continue
        for token in re.findall(r"`([^`\n]+)`", line):
            token = token.strip()
            first = token.split()[0]
            if TEST_RE.match(first):
                checked += 1
                if first not in tests:
                    problems.append(f"dong {lineno}: test `{first}` khong ton tai trong tests/")
                continue
            m = SYMBOL_RE.match(first)
            if m and not PATH_RE.fullmatch(first):
                checked += 1
                owner, attr = m.groups()
                if not _symbol_exists(owner, attr, sources):
                    problems.append(f"dong {lineno}: ky hieu `{first}` khong tim thay")
                continue
            # Lệnh như `python scripts/x.py --flag` cũng chứa đường dẫn cần kiểm.
            for ref in PATH_RE.findall(token):
                checked += 1
                if not _path_exists(ref):
                    problems.append(f"dong {lineno}: duong dan `{ref}` khong ton tai")
    problems += _missing_coverage(doc_text)
    return problems, checked


# Thư mục mà MỌI file trong đó phải có một dòng trong bảng. Đây mới là lỗi thật của lần
# rà soát 2026-10-10: mọi đường dẫn trong bảng đều đúng, nhưng bảng THIẾU hẳn tài khoản,
# bộ sưu tập, địa chỉ, cả trang quản trị — kiểm "trỏ đúng" thôi thì không bao giờ thấy.
MUST_BE_TRACED = ("src/application/use_cases", "src/presentation/api/routers")


def _missing_coverage(doc_text: str) -> list[str]:
    missing: list[str] = []
    for folder in MUST_BE_TRACED:
        for p in sorted((ROOT / folder).glob("*.py")):
            if p.name == "__init__.py":
                continue
            rel = p.relative_to(ROOT).as_posix()
            if rel not in doc_text:
                missing.append(f"chua co trong bang: `{rel}`")
    return missing


def main() -> int:
    if not DOC.exists():
        print("KHONG CO traceability.md")
        return 1
    problems, checked = find_problems(DOC.read_text(encoding="utf-8"))
    if problems:
        print(f"Ma tran truy vet: {len(problems)} van de ({checked} tham chieu da kiem)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"Ma tran truy vet OK: {checked} tham chieu deu ton tai")
    return 0


if __name__ == "__main__":
    sys.exit(main())
