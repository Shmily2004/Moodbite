"""Khoá lại quy tắc TÓM TẮT REVIEW (Lớp 4 của đề án).

Hàm tóm tắt là hàm THUẦN: nhận list review, trả dict. Không đọc file, không gọi mạng -
nên test chạy được kể cả trên máy chưa chạy data_pipeline.
"""
import pytest

from data_pipeline.review_summary import split_sentences, summarize_one


def review(text, stars=5):
    return {"text": text, "stars": stars, "name": "nguoi dung"}


# Sáu review đủ dài để qua ngưỡng ký tự tối thiểu của `split_sentences`.
NHIEU_REVIEW = [
    review("Đồ ăn ngon, nước dùng đậm đà và thơm mùi quế hồi rất dễ chịu.", 5),
    review("Quán sạch sẽ, nhân viên phục vụ nhanh nhẹn và niềm nở với khách.", 5),
    review("Giá cả hợp lý so với chất lượng, phần ăn đầy đặn no bụng.", 4),
    review("Chỗ ngồi hơi chật vào giờ cao điểm nên phải chờ khá lâu mới có bàn.", 2),
    review("Nước dùng hôm nay nhạt hơn mọi khi, hơi thất vọng so với lần trước.", 1),
    review("Không gian ấm cúng, phù hợp ngồi lâu trò chuyện cùng bạn bè.", 5),
]


# --- Tách câu ----------------------------------------------------------------


def test_bo_cau_qua_ngan():
    """"Ngon", "Ok ạ" không mang thông tin gì - đưa vào tóm tắt chỉ làm loãng."""
    assert split_sentences("Ngon. Ok ạ. Tuyệt!") == []


def test_giu_cau_du_dai():
    cau = "Nước dùng đậm đà và thơm mùi quế hồi rất dễ chịu"
    assert cau in split_sentences(cau + ".")


def test_tach_theo_dau_ket_cau_va_xuong_dong():
    text = "Quán sạch sẽ và rộng rãi lắm nhé\nNhân viên phục vụ rất nhiệt tình chu đáo"
    assert len(split_sentences(text)) == 2


# --- Ngưỡng dữ liệu ----------------------------------------------------------


def test_qua_it_review_thi_KHONG_tom_tat():
    """Dưới 3 review thì "tóm tắt" chỉ là chép lại một ý kiến cá nhân, mà lại được trình
    bày như nhận xét chung của quán - gây hiểu lầm hơn là không có gì."""
    assert summarize_one([review("Đồ ăn ngon, nước dùng đậm đà thơm mùi quế hồi.")]) is None


def test_review_khong_co_chu_khong_duoc_tinh():
    """Review chỉ bấm sao, không viết chữ -> không dùng để tóm tắt được."""
    chi_co_sao = [{"stars": 5}, {"stars": 4}, {"stars": 5}]
    assert summarize_one(chi_co_sao) is None


def test_nguong_co_the_chinh():
    assert summarize_one(NHIEU_REVIEW[:4], min_reviews=10) is None
    assert summarize_one(NHIEU_REVIEW[:4], min_reviews=4) is not None


# --- Nội dung tóm tắt --------------------------------------------------------


def test_moi_cau_deu_la_TRICH_NGUYEN_VAN_tu_review():
    """Không được sinh chữ mới. Mọi câu phải truy được về một review có thật -
    đây là chốt chặn chống bịa dữ liệu (CLAUDE.md mục 4b)."""
    ket_qua = summarize_one(NHIEU_REVIEW)

    nguon = " ".join(r["text"] for r in NHIEU_REVIEW)
    for cau in ket_qua["summary"] + ket_qua["positive"] + ket_qua["negative"]:
        assert cau in nguon, f"cau nay khong co trong review goc: {cau}"


def test_diem_manh_lay_tu_review_sao_CAO():
    ket_qua = summarize_one(NHIEU_REVIEW)

    cau_sao_thap = " ".join(r["text"] for r in NHIEU_REVIEW if r["stars"] <= 2)
    for cau in ket_qua["positive"]:
        assert cau not in cau_sao_thap


def test_diem_yeu_lay_tu_review_sao_THAP():
    ket_qua = summarize_one(NHIEU_REVIEW)

    cau_sao_cao = " ".join(r["text"] for r in NHIEU_REVIEW if r["stars"] >= 4)
    assert ket_qua["negative"], "phai bat duoc diem yeu tu review 1-2 sao"
    for cau in ket_qua["negative"]:
        assert cau not in cau_sao_cao


def test_review_3_sao_khong_vao_ca_hai_ben():
    """3 sao là trung tính. Gán vào điểm mạnh hay điểm yếu đều làm sai bức tranh."""
    trung_tinh = [review(f"Quán ăn được, không có gì đặc biệt để chê hay khen số {i}.", 3)
                  for i in range(4)]

    ket_qua = summarize_one(trung_tinh)

    assert ket_qua["positive"] == []
    assert ket_qua["negative"] == []
    assert ket_qua["summary"], "van phai co tom tat chung"


def test_diem_manh_KHONG_lap_lai_cau_da_co_trong_tom_tat():
    """Đọc cùng một câu hai lần trên một màn hình làm người dùng tưởng hệ thống lỗi."""
    ket_qua = summarize_one(NHIEU_REVIEW)

    trung = set(ket_qua["summary"]) & set(ket_qua["positive"] + ket_qua["negative"])
    assert not trung, f"cau bi lap: {trung}"


def test_ghi_ro_PHUONG_PHAP_la_trich_rut():
    """UI phải nói được đây là câu trích nguyên văn, không phải máy tự nhận xét."""
    assert summarize_one(NHIEU_REVIEW)["method"] == "extractive_tfidf"


def test_tra_ve_so_review_va_sao_trung_binh():
    ket_qua = summarize_one(NHIEU_REVIEW)

    assert ket_qua["review_count"] == len(NHIEU_REVIEW)
    assert ket_qua["average_stars"] == pytest.approx(
        sum(r["stars"] for r in NHIEU_REVIEW) / len(NHIEU_REVIEW), abs=0.01
    )


def test_khong_co_sao_thi_average_la_None_chu_khong_phai_0():
    """`None` = chưa có dữ liệu. `0` nghĩa là 0 sao - hai chuyện khác hẳn nhau
    (CLAUDE.md mục 4 quy tắc 1)."""
    khong_sao = [{"text": f"Quán này ăn cũng được, không gian thoáng mát số {i}."}
                 for i in range(4)]

    assert summarize_one(khong_sao)["average_stars"] is None
