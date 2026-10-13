"""Khoá `scripts/check_traceability.py` — máy kiểm ma trận truy vết.

Hai lỗi thật nó phải bắt: (1) bảng trỏ vào file/test KHÔNG có (bản đầu: 9/10 đường dẫn
sai), (2) bảng BỎ SÓT tính năng (2026-10-10: thiếu 15/20 use case dù mọi đường dẫn đều
đúng). Và một thứ nó KHÔNG được bắt: dòng trích dẫn kể lại lịch sử file cũ đã gỡ.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "check_traceability", ROOT / "scripts" / "check_traceability.py"
)
checker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(checker)


def _problems(doc: str) -> list[str]:
    problems, _ = checker.find_problems(doc)
    # Bỏ phần "chưa có trong bảng" — doc giả trong test cố ý không liệt kê đủ use case.
    return [p for p in problems if "chua co trong bang" not in p]


def test_duong_dan_khong_ton_tai_bi_bat():
    assert _problems("| x | `src/domain/services/khong_co_file_nay.py` |")


def test_ten_test_bia_bi_bat():
    assert _problems("| x | `test_ten_nay_khong_he_ton_tai` |")


def test_ky_hieu_khong_co_trong_module_bi_bat():
    assert _problems("| x | `dish_ranking._ham_khong_ton_tai` |")


def test_tham_chieu_that_thi_khong_bao_loi():
    doc = (
        "| x | `src/domain/services/dish_ranking.py` | `dish_ranking._passes_hard_filter` "
        "| `test_weights_sum_to_one` | `Dish.has_description` | `frontend/apps/*/src/` |"
    )
    assert _problems(doc) == []


def test_dong_trich_dan_lich_su_duoc_bo_qua():
    assert _problems("> bản cũ trỏ tới `src/application/use-cases/Cu.ts` đã gỡ") == []


def test_duong_dan_trong_cau_lenh_cung_duoc_kiem():
    assert _problems("chạy `python scripts/khong_co_script.py --flag`")


def test_use_case_khong_co_trong_bang_bi_bat():
    problems, _ = checker.find_problems("bảng rỗng")
    assert any("src/application/use_cases/suggest_dishes.py" in p for p in problems)
    assert any("src/presentation/api/routers/dishes.py" in p for p in problems)


def test_ma_tran_that_cua_du_an_dat():
    problems, checked = checker.find_problems((ROOT / "traceability.md").read_text(encoding="utf-8"))
    assert problems == []
    assert checked > 100
