"""Khoá NHÃN trong `dish_seed_manual.json` — cách chế biến (bộ lọc "đồ luộc", "đồ nướng"…)
và ẩm thực.

BUG THẬT 2026-11-11: chọn lọc "Luộc" thì trang gợi ý món trả về Ốc luộc, **Cơm gà**, **Mì Ý**,
**Mì Ý sốt bò bằm**, kèm lý do "đúng cách chế biến bạn chọn". Hai món đầu tiên sai rõ ràng:
ai bấm "đồ luộc" cũng không mong thấy mì spaghetti.

NGUYÊN NHÂN GỐC là DỮ LIỆU, không phải thuật toán xếp hạng: nhãn `luoc` được gắn theo MÔ TẢ
("mì sợi dài luộc chín, trộn cùng sốt…", "cơm nấu cùng nước luộc gà…"), tức là theo một BƯỚC
trong công thức chứ không phải theo cách món đó được ĂN. Ngược lại "Gà luộc" — món luộc đúng
nghĩa — lại để trống nhãn nên không bao giờ nhận được lý do "đúng cách chế biến".

RÀ SOÁT CÙNG NGÀY cho ra thêm 3 họ lỗi cùng một gốc (nhãn gắn từ nguồn sai, không từ chính
món), và test dưới đây khoá từng họ:
  1. TÊN nói rõ cách chế biến mà không có nhãn (35 món: "Bò nướng", "Cánh gà chiên"…).
     Từ khi bộ lọc cách chế biến ẨN món chưa nhãn, mỗi món thiếu nhãn là một món biến mất
     khỏi bộ lọc đúng của nó.
  2. Đồ uống mang nhãn `tron` (Trà chanh, Sữa chua trân châu) — nhãn "trộn" lấy từ bước pha.
     Trước khi sửa, chọn "Trộn" ra Trà chanh ở vị trí số 1.
  3. `cuisine` do script làm giàu tự gắn từ Wikipedia khớp NHẦM thực thể: Cơm gà → "Tây Ban
     Nha" (nhầm với arroz con pollo), Miến → "Philippines", Xôi → "Thái Lan". Ba món rất Việt
     này biến mất mỗi khi người dùng chọn ẩm thực "Việt Nam".

Bộ lọc cứng chỉ loại món có nhãn KHÁC; món chưa có nhãn cách chế biến bị ẩn (xem
`dish_ranking.py`). Vì vậy một nhãn gắn SAI là nguy hiểm hơn một nhãn bỏ trống: nó không chỉ
lọt qua mà còn được cộng điểm và được ghi lý do khớp.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_dish_catalog import MANUAL_SEED_PATH, load_manual_seed
from src.domain.entities.dish import (
    METHOD_BOILED,
    METHOD_MIXED,
)
from src.domain.services.dish_ranking import DishFilter, filter_dishes, rank_dishes
from src.domain.value_objects.context_signal import NEUTRAL_CONTEXT
from src.domain.value_objects.text import contains_phrase

# Từ trong TÊN -> các nhãn chấp nhận được. Chỉ gồm từ ĐỘNG TỪ có dấu và không mơ hồ.
# Cố ý KHÔNG có "quay" (không dấu nên `contains_phrase` khớp nhầm "quẩy" - xem text.py),
# "rang"/"đồ" (nhiều nghĩa) và các danh từ như "gỏi", "salad".
# "nướng" chấp nhận cả `nuong_lo` vì bánh nướng lò (bánh mì, bánh nướng) mang nhãn đó.
TU_TRONG_TEN: dict[str, frozenset[str]] = {
    "luộc": frozenset({"luoc"}),
    "nướng": frozenset({"nuong", "nuong_lo"}),
    "chiên": frozenset({"chien"}),
    "rán": frozenset({"chien"}),
    "hấp": frozenset({"hap"}),
    "xào": frozenset({"xao"}),
    "trộn": frozenset({"tron"}),
}

# Ngoại lệ CỦA CHIỀU "tên -> nhãn". Mỗi dòng phải có LÝ DO, không phải lối thoát để qua test.
NGOAI_LE_TEN_SANG_NHAN: dict[str, frozenset[str]] = {
    # "Cơm chiên" = "cơm rang" (cùng một món, cách gọi miền Nam). Seed đã gắn "Cơm rang" là
    # `xao` ("xào, rang"), nên hai tên của một món phải cùng nhãn.
    "com-chien": frozenset({"xao"}),
    "com-chien-duong-chau": frozenset({"xao"}),
}

# Chiều ngược: nhãn nào thì TÊN phải có từ nào. Chỉ khai cho nhãn mà tên món luôn lộ ra được.
# Không khai cho `nuoc`/`nuong`/`hap`…: món nước (phở), bánh mì, xôi… không chứa từ chỉ cách chế biến.
TU_BAT_BUOC_CHO_NHAN: dict[str, tuple[str, ...]] = {
    METHOD_BOILED: ("luộc",),
    METHOD_MIXED: ("trộn", "salad", "nộm"),
}

# Món được phép mang nhãn dù tên không có từ trên. ĐỂ Ý: không có món `luoc` nào ở đây.
NGOAI_LE_NHAN_KHONG_CO_TU_TRONG_TEN: dict[str, str] = {
    # Mô tả của chính món: "mì sợi dài luộc chín, TRỘN cùng sốt". Ăn ở dạng trộn sốt, không phải luộc.
    "mi-y": METHOD_MIXED,
    "mi-y-sot-bo-bam": METHOD_MIXED,
}


def _doc_seed() -> list[dict]:
    return json.loads(Path(MANUAL_SEED_PATH).read_text(encoding="utf-8"))["dishes"]


def _co_tu(ten: str, tu: str) -> bool:
    # `contains_phrase` (CLAUDE.md mục 4.5): bỏ dấu + khớp TỪ NGUYÊN VẸN + dấu là bằng chứng.
    return contains_phrase(ten, tu)


# --- 1. TÊN nói cách chế biến -> nhãn phải khớp -------------------------------


def test_ten_mon_noi_ro_cach_che_bien_thi_nhan_phai_khop():
    """Bắt đúng lỗi 'Gà luộc' để trống nhãn, và cả nhãn đặt NGƯỢC với tên.

    Tên chứa từ chỉ MỘT cách chế biến -> nhãn phải là cách đó (hoặc ngoại lệ có lý do).
    Tên chứa hai cách mâu thuẫn ("nướng" + "chiên") thì bỏ qua: tự tên đã không kết luận được.
    """
    sai = []
    for mon in _doc_seed():
        cach = {TU_TRONG_TEN[t] for t in TU_TRONG_TEN if _co_tu(mon["name"], t)}
        if len(cach) != 1:
            continue
        chap_nhan = NGOAI_LE_TEN_SANG_NHAN.get(mon["dish_id"], next(iter(cach)))
        if mon.get("cooking_method") not in chap_nhan:
            sai.append(
                f"{mon['dish_id']} ({mon['name']}): nhãn={mon.get('cooking_method')!r}, "
                f"tên đòi {sorted(chap_nhan)}"
            )
    assert sai == [], (
        "Tên món nói rõ cách chế biến nhưng nhãn thiếu/sai — món sẽ biến mất khỏi bộ lọc "
        "đúng của nó, hoặc hiện nhầm vào bộ lọc khác:\n  " + "\n  ".join(sai)
    )


# --- 2. nhãn -> TÊN phải có từ tương ứng --------------------------------------


@pytest.mark.parametrize("nhan", sorted(TU_BAT_BUOC_CHO_NHAN))
def test_mon_mang_nhan_phai_co_tu_tuong_ung_trong_TEN(nhan):
    """Chiều CHÍNH XÁC: bắt Mì Ý/Cơm gà (`luoc`) và Trà chanh/Sữa chua (`tron`) — nhãn gắn
    theo mô tả hoặc theo bước pha chế chứ không theo cách món được ĂN."""
    tu = TU_BAT_BUOC_CHO_NHAN[nhan]
    sai = [
        f"{m['dish_id']} ({m['name']})"
        for m in _doc_seed()
        if m.get("cooking_method") == nhan
        and not any(_co_tu(m["name"], t) for t in tu)
        and NGOAI_LE_NHAN_KHONG_CO_TU_TRONG_TEN.get(m["dish_id"]) != nhan
    ]
    assert sai == [], (
        f"Các món này mang nhãn `{nhan}` nhưng tên không có {tu}, nên sẽ hiện ra khi người "
        f"dùng chọn cách chế biến đó: {sai}. Chỉ gắn nhãn khi món được ĂN ở dạng ấy."
    )


# --- 3. ẩm thực của món quen thuộc ở Hà Nội ----------------------------------

# Ba món bán đầy ở Hà Nội mà script làm giàu từng gắn ẩm thực nước ngoài do khớp nhầm
# thực thể Wikipedia. Đặt thẳng "Việt Nam" (không để trống): `backfill_dish_cuisine.py` chỉ
# điền ô TRỐNG nên lần chạy lại sẽ không ghi đè, và đúng tinh thần của script đó là ưu tiên
# Việt Nam vì ứng dụng dành cho người ăn ở Hà Nội.
MON_VIET_BI_GAN_NHAM_AM_THUC = ("xoi", "mien", "com-ga")


@pytest.mark.parametrize("dish_id", MON_VIET_BI_GAN_NHAM_AM_THUC)
def test_mon_viet_khong_bi_gan_am_thuc_nuoc_ngoai(dish_id):
    mon = next(m for m in _doc_seed() if m["dish_id"] == dish_id)
    assert mon.get("cuisine") == "Việt Nam", (
        f"{mon['name']} có ẩm thực {mon.get('cuisine')!r}: món này biến mất khi người dùng "
        "chọn 'Việt Nam'. Nếu vừa chạy lại backfill_dish_cuisine.py thì đây là khớp nhầm Wikipedia."
    )


# --- 4. Hành vi người dùng thấy -----------------------------------------------


@pytest.fixture(scope="module")
def mon_trong_seed():
    return load_manual_seed(Path(MANUAL_SEED_PATH))


def _hang(dishes, bo_loc):
    """Đúng đường đi của use case: lọc cứng rồi xếp hạng, mọi món có cùng số quán."""
    con_lai = filter_dishes(dishes, bo_loc)
    dem = {d.identifier: 10 for d in con_lai}
    return rank_dishes(con_lai, bo_loc, NEUTRAL_CONTEXT, dem, limit=len(con_lai))


def test_loc_luoc_khong_xep_mi_y_va_com_ga_la_khop_cach_che_bien(mon_trong_seed):
    """Hành vi người dùng thấy: KHÔNG món nào ngoài đồ luộc được ghi 'đúng cách chế biến'."""
    bang = _hang(mon_trong_seed, DishFilter(cooking_methods=[METHOD_BOILED]))

    duoc_ghi_khop = {r.dish.name for r in bang if "đúng cách chế biến bạn chọn" in r.reasons}

    assert "Ốc luộc" in duoc_ghi_khop
    assert "Gà luộc" in duoc_ghi_khop
    for sai in ("Mì Ý", "Mì Ý sốt bò bằm", "Cơm gà"):
        assert sai not in duoc_ghi_khop, f"{sai} không phải đồ luộc"


def test_loc_luoc_chi_con_lai_mon_da_biet_la_luoc(mon_trong_seed):
    """Đúng khiếu nại gốc: lọc "Luộc" thì MỌI món còn lại phải là món đã gắn nhãn luộc.

    Mì Ý bị loại vì mang nhãn KHÁC (`tron`); Cơm gà bị loại vì CHƯA CÓ nhãn (từ 2026-11-11
    bộ lọc cách chế biến ẩn món chưa biết, xem `dish_ranking._passes_hard_filter`).
    """
    con_lai = filter_dishes(mon_trong_seed, DishFilter(cooking_methods=[METHOD_BOILED]))

    assert con_lai, "không món nào còn lại: dữ liệu seed không có món luộc nào?"
    assert {d.cooking_method for d in con_lai} == {METHOD_BOILED}
    ten = {d.name for d in con_lai}
    assert {"Ốc luộc", "Gà luộc"} <= ten
    for sai in ("Mì Ý", "Mì Ý sốt bò bằm", "Cơm gà"):
        assert sai not in ten


def test_loc_tron_khong_con_do_uong(mon_trong_seed):
    """Trước khi sửa, chọn 'Trộn' ra Trà chanh ở vị trí số 1 (380 quán, điểm cao nhất)."""
    ten = {d.name for d in filter_dishes(mon_trong_seed, DishFilter(cooking_methods=[METHOD_MIXED]))}

    assert {"Trà chanh", "Sữa chua trân châu"}.isdisjoint(ten)
    assert {"Bánh tráng trộn", "Miến trộn"} <= ten
