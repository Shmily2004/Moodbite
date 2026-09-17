"""Bộ công cụ sinh NGƯỜI DÙNG GIẢ LẬP + đánh giá xếp hạng offline.

Chia nhỏ để mỗi file một trách nhiệm (CLAUDE.md mục 6):

    an_toan.py      chốt chặn đường dẫn: KHÔNG BAO GIỜ ghi vào dữ liệu thật
    persona.py      chân dung người dùng + "độ hợp" (utility) ĐỘC LẬP với công thức MoodBite
    click_model.py  mô hình bấm: thiên lệch vị trí x độ hợp
    metrics.py      NDCG / Precision / MRR / độ phủ — thuần Python
    session.py      một phiên dùng app: gọi API thật qua TestClient

Hai script dùng bộ này: `scripts/gia_lap_nguoi_dung.py` và `scripts/danh_gia_xep_hang.py`.
"""
