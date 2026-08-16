"""Bổ sung rule món ăn Việt vào dish_knowledge_base.json.

VÌ SAO CẦN: knowledge base cũ chỉ có 21 rule và bỏ sót phần lớn món Việt phổ biến.
Đo trên dataset thật (4170 quán), số quán có từ khoá món trong TÊN QUÁN:
    bún 238 | phở 144 | pizza 62 | lẩu 62 | ốc 56 | bún chả 56 | nướng 51
    bánh mì 34 | bún bò 32 | bún đậu 31 | nem 29 | sushi 28 | cháo 24 ...
Trong đó chỉ phở/pizza/lẩu/nướng đã có rule -> phần lớn quán bún, bánh mì, ốc, cháo...
đều rơi vào rule chung "nhà hàng" và bị gợi ý món sai.

THỨ TỰ QUAN TRỌNG: rule cụ thể phải đứng TRƯỚC rule chung, vì hệ thống lấy rule khớp
ĐẦU TIÊN. "bún chả" phải đứng trước "bún", và mọi rule cụ thể phải đứng trước
"nhà hàng"/"cà phê" (generic_fallback).

Chạy 1 lần: python scripts/extend_dish_knowledge.py
Chạy lại nhiều lần cũng an toàn - rule đã tồn tại (theo id) sẽ được bỏ qua.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KB_PATH = Path("data_pipeline/dish_knowledge_base.json")


def dish(name, cuisine="Việt Nam", spice=0, temperature="hot",
         portion="regular", moods=("comfort", "cozy")):
    return {
        "name": name,
        "cuisine": cuisine,
        "spice_level": spice,
        "temperature": temperature,
        "portion_size": portion,
        "mood_keywords": list(moods),
    }


# Rule mới, ĐÃ SẮP THEO ĐỘ CỤ THỂ GIẢM DẦN (cụ thể nhất lên đầu).
NEW_RULES = [
    {"id": "bun_cha", "match_category": ["bún chả"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Bún chả", moods=("comfort", "cozy")),
                dish("Nem rán", temperature="hot", moods=("comfort",))]},
    {"id": "bun_dau", "match_category": ["bún đậu"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Bún đậu mắm tôm", temperature="cold", moods=("cheap", "comfort"))]},
    {"id": "bun_bo", "match_category": ["bún bò"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Bún bò Huế", spice=2, moods=("spicy", "comfort"))]},
    {"id": "bun_rieu", "match_category": ["bún riêu"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Bún riêu cua", moods=("comfort", "fresh"))]},
    {"id": "bun_generic", "match_category": ["bún"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Bún nước", moods=("comfort", "quick"))]},
    {"id": "banh_mi", "match_category": ["bánh mì"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Bánh mì thịt", portion="small", moods=("quick", "cheap"))]},
    {"id": "banh_cuon", "match_category": ["bánh cuốn"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Bánh cuốn nóng", portion="small", moods=("fresh", "comfort"))]},
    {"id": "xoi", "match_category": ["xôi"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Xôi mặn", portion="small", moods=("cheap", "quick", "comfort"))]},
    {"id": "chao", "match_category": ["cháo"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Cháo nóng", moods=("comfort", "cozy"))]},
    {"id": "mien", "match_category": ["miến"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Miến trộn", moods=("comfort", "quick"))]},
    {"id": "oc", "match_category": ["ốc"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Ốc luộc", spice=1, moods=("spicy", "fresh"))]},
    {"id": "nem_chua_ran", "match_category": ["nem"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Nem chua rán", portion="small", moods=("quick", "cheap"))]},
    {"id": "che", "match_category": ["chè"], "match_cuisine": ["vietnamese"],
     "confidence": "specific",
     "dishes": [dish("Chè", temperature="cold", portion="small", moods=("sweet", "fresh"))]},
    {"id": "kem", "match_category": ["kem"], "match_cuisine": [],
     "confidence": "specific",
     "dishes": [dish("Kem", cuisine=None, temperature="cold", portion="small",
                     moods=("sweet", "fresh"))]},
    {"id": "tra_sua", "match_category": ["trà sữa"], "match_cuisine": [],
     "confidence": "specific",
     "dishes": [dish("Trà sữa trân châu", cuisine=None, temperature="cold",
                     moods=("sweet", "quick"))]},
    {"id": "sushi", "match_category": ["sushi"], "match_cuisine": ["japanese"],
     "confidence": "specific",
     "dishes": [dish("Sushi", cuisine="Nhật Bản", temperature="cold",
                     moods=("fresh",))]},
    {"id": "com_tam_ga", "match_category": ["cơm tấm", "cơm gà"],
     "match_cuisine": ["vietnamese"], "confidence": "specific",
     "dishes": [dish("Cơm tấm sườn", moods=("comfort", "cheap"))]},
]

# Rule chung phải luôn nằm CUỐI: chèn rule mới ngay trước rule generic đầu tiên.
GENERIC_IDS = {"ca_phe", "nha_hang_generic"}


def main() -> int:
    if not KB_PATH.exists():
        print(f"Khong tim thay {KB_PATH}")
        return 1

    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    rules = kb["rules"]
    existing_ids = {r["id"] for r in rules}

    to_add = [r for r in NEW_RULES if r["id"] not in existing_ids]
    if not to_add:
        print("Khong co rule moi nao can them (da chay truoc do).")
        return 0

    first_generic = next(
        (i for i, r in enumerate(rules) if r["id"] in GENERIC_IDS), len(rules)
    )
    kb["rules"] = rules[:first_generic] + to_add + rules[first_generic:]

    KB_PATH.write_text(
        json.dumps(kb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Da them {len(to_add)} rule: {[r['id'] for r in to_add]}")
    print(f"Tong so rule: {len(kb['rules'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
