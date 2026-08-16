"""Test hai lớp mô hình mới: phân cụm trải nghiệm (Lớp 1) và tìm kiếm ngữ nghĩa (Lớp 2).

Chạy OFFLINE, không cần file dữ liệu thật.
"""
import numpy as np
import pytest

from src.domain.value_objects.price import PriceRange, parse_price
from src.infrastructure.adapters.tfidf_semantic_search import TfidfSemanticSearch
from tests.fakes import make_restaurant


# --- Phân tích khoảng giá -----------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected_level",
    [
        ("1-100.000 ₫", 1),
        ("100-200 N ₫", 2),
        ("200-300 N ₫", 2),
        ("Trên 1 Tr ₫", 4),
        ("70 US$", 4),        # phải quy đổi USD, không thì rơi nhầm mức rẻ nhất
    ],
)
def test_parse_price_levels(raw, expected_level):
    parsed = parse_price(raw)
    assert parsed is not None and parsed.level == expected_level


@pytest.mark.parametrize("raw", [None, "", "   ", "rác không có số", 123])
def test_parse_price_unknown_returns_none(raw):
    """Không hiểu được -> None = KHÔNG BIẾT, tuyệt đối không phải 'miễn phí'."""
    assert parse_price(raw) is None


def test_parse_price_keeps_raw_for_display():
    """`level` chỉ dùng để lọc/phân cụm; hiển thị cho người dùng phải là chuỗi gốc."""
    parsed = parse_price("100-200 N ₫")
    assert parsed.raw == "100-200 N ₫"
    assert parsed.label == "Trung bình"


def test_parse_price_handles_non_breaking_space():
    assert parse_price("100-200\xa0N\xa0₫") is not None


# --- Tìm kiếm ngữ nghĩa (Lớp 2) ----------------------------------------------


def _corpus():
    """Tập quán đủ đa dạng để TF-IDF học được từ nào là đặc trưng."""
    return [
        make_restaurant("Cà Phê Yên Tĩnh", category="Quán cà phê",
                        review_text="không gian tĩnh lặng, ngồi lâu làm việc rất hợp"),
        make_restaurant("Lẩu Cay Tứ Xuyên", category="Nhà hàng lẩu",
                        review_text="lẩu cay tê nóng hổi đậm đà"),
        make_restaurant("Sushi Tươi", category="Nhà hàng Nhật Bản",
                        review_text="sashimi tươi ngon, cá hồi béo"),
        make_restaurant("Bún Chả Hà Nội", category="Quán bún chả",
                        review_text="bún chả thịt nướng thơm"),
        make_restaurant("Pizza Ý", category="Nhà hàng pizza",
                        review_text="pizza phô mai đế mỏng"),
        make_restaurant("Trà Sữa Ngọt", category="Quán trà sữa",
                        review_text="trà sữa trân châu đường đen"),
        make_restaurant("Cơm Văn Phòng", category="Quán cơm",
                        review_text="cơm trưa văn phòng nhanh gọn"),
        make_restaurant("Quán Nhậu Bia", category="Quán bia",
                        review_text="bia lạnh đồ nhắm ốc"),
        make_restaurant("Bánh Mì Vỉa Hè", category="Tiệm bánh mì",
                        review_text="bánh mì pate trứng giòn"),
        make_restaurant("Phở Bò Gia Truyền", category="Nhà hàng phở",
                        review_text="phở bò nước dùng ngọt xương"),
        make_restaurant("Chè Thập Cẩm", category="Quán chè",
                        review_text="chè mát lạnh nhiều topping"),
        make_restaurant("Nhà Hàng Chay An Lạc", category="Nhà hàng chay",
                        review_text="đồ chay thanh đạm rau củ"),
    ]


def test_semantic_search_builds_index():
    engine = TfidfSemanticSearch(_corpus())
    assert engine.is_ready
    assert engine.status()["indexed"] == 12


def test_semantic_search_finds_related_wording():
    """Điểm mạnh so với khớp từ khoá: 'yên tĩnh' khớp được quán review là 'tĩnh lặng'."""
    engine = TfidfSemanticSearch(_corpus())
    scores = engine.similarity("chỗ yên tĩnh ngồi làm việc")
    assert scores, "phải tìm được ít nhất một quán"
    best = max(scores, key=scores.get)
    assert best == "id-Cà Phê Yên Tĩnh"


def test_semantic_search_ranks_by_topic():
    engine = TfidfSemanticSearch(_corpus())
    scores = engine.similarity("lẩu cay nóng")
    assert scores.get("id-Lẩu Cay Tứ Xuyên", 0) > scores.get("id-Chè Thập Cẩm", 0)


def test_semantic_search_empty_query_returns_nothing():
    engine = TfidfSemanticSearch(_corpus())
    assert engine.similarity("") == {}
    assert engine.similarity("   ") == {}


def test_semantic_search_degrades_gracefully_without_data():
    """Chưa đủ dữ liệu -> is_ready=False, hệ thống lui về khớp từ khoá thay vì hỏng."""
    engine = TfidfSemanticSearch([make_restaurant("Duy Nhất")])
    assert engine.is_ready is False
    assert engine.similarity("bất kỳ") == {}
    assert engine.status()["error"]


def test_semantic_search_skips_restaurants_without_place_id():
    from src.domain.entities.restaurant import Restaurant
    from src.domain.value_objects.location import Location

    corpus = _corpus() + [
        Restaurant(place_id=None, name="Không Có Id", category="Quán ăn",
                   location=Location(lat=21.0, lng=105.8))
    ]
    engine = TfidfSemanticSearch(corpus)
    assert engine.status()["indexed"] == 12


# --- Phân cụm: hàm đánh giá (Lớp 1) ------------------------------------------


def test_clustering_metrics_computed():
    """Ba chỉ số đề án mục 8 yêu cầu phải tính được và có ý nghĩa.

    Dữ liệu test PHẢI có phương sai trong cụm - nếu mọi điểm trùng nhau thì
    Calinski-Harabasz suy biến về 1.0 và phép kiểm mất ý nghĩa.
    """
    from data_pipeline.clustering import evaluate

    rng = np.random.default_rng(0)
    matrix = np.vstack([
        rng.normal(-5, 0.3, (20, 3)),
        rng.normal(5, 0.3, (20, 3)),
    ])
    labels = np.array([0] * 20 + [1] * 20)
    metrics = evaluate(matrix, labels)

    assert metrics["silhouette"] > 0.9          # càng gần 1 càng tốt
    assert metrics["davies_bouldin"] < 0.5      # càng gần 0 càng tốt
    assert metrics["calinski_harabasz"] > 100   # càng cao càng tốt


def test_clustering_prefers_k_with_usable_cluster_sizes():
    """Silhouette một mình sẽ chọn k sinh ra cụm vài phần tử - 'tách biệt tốt' về mặt
    toán học nhưng vô dụng khi gợi ý. `choose_k` phải loại các k đó."""
    from data_pipeline.clustering import choose_k

    rng = np.random.default_rng(42)
    # 3 nhóm cân bằng, tách biệt rõ -> k=3 là lựa chọn dùng được.
    matrix = np.vstack([
        rng.normal(0, 0.4, (60, 2)),
        rng.normal(8, 0.4, (60, 2)),
        rng.normal(16, 0.4, (60, 2)),
    ])
    best_k, scores = choose_k(matrix, candidates=range(2, 7))

    assert best_k == 3
    assert scores[best_k]["smallest_cluster"] >= 30, "các cụm phải cân bằng"


def test_clustering_falls_back_when_no_k_gives_large_clusters():
    """Dữ liệu có ngoại lệ thật -> mọi k đều sinh cụm nhỏ. Khi đó vẫn phải trả về một k
    (kèm cảnh báo) thay vì hỏng."""
    from data_pipeline.clustering import choose_k

    rng = np.random.default_rng(1)
    matrix = np.vstack([rng.normal(0, 0.4, (40, 2)), np.array([[500.0, 500.0]])])
    best_k, scores = choose_k(matrix, candidates=range(2, 4))
    assert best_k in scores
