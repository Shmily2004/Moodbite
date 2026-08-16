"""Test tầng thu thập dữ liệu: chuẩn hoá bản ghi, nối vòng ranh giới, tra quận.

Toàn bộ chạy OFFLINE - không gọi mạng, không cần Overpass. Nhờ vậy CI luôn chạy được
và không phụ thuộc một dịch vụ bên ngoài có thể sập.
"""
import pytest

from data_pipeline.sources.base import (
    CONFIDENCE_COMMUNITY,
    CONFIDENCE_DERIVED,
    RawPlace,
    dedupe_places,
    utc_now_iso,
)
from data_pipeline.sources.districts import (
    DistrictLocator,
    point_in_ring,
    stitch_rings,
)
from data_pipeline.sources.osm_overpass import OsmOverpassSource


# --- RawPlace ----------------------------------------------------------------


def test_raw_place_always_records_provenance():
    """Mọi bản ghi phải trả lời được: ở đâu ra, đáng tin tới đâu, cập nhật lúc nào."""
    record = RawPlace(
        placeId="osm-node-1", title="Quán A", source="openstreetmap"
    ).to_record()
    assert record["source"] == "openstreetmap"
    assert record["data_confidence"] == CONFIDENCE_COMMUNITY
    assert record["last_updated"], "phải tự điền thời điểm nếu nguồn không cung cấp"


def test_dedupe_places_removes_repeated_place_id():
    places = [
        RawPlace(placeId="a", title="A", source="s"),
        RawPlace(placeId="a", title="A trùng", source="s"),
        RawPlace(placeId="b", title="B", source="s"),
    ]
    unique, removed = dedupe_places(places)
    assert [p.placeId for p in unique] == ["a", "b"]
    assert removed == 1


def test_utc_now_iso_has_timezone():
    assert utc_now_iso().endswith("+00:00")


# --- Nối vòng ranh giới -------------------------------------------------------


def test_stitch_rings_joins_split_segments():
    """Overpass trả ranh giới thành NHIỀU đoạn rời. Không nối lại thì mọi phép
    kiểm tra điểm-trong-đa-giác đều sai (bug đã gặp: mọi quán đều không có quận)."""
    segments = [[(0, 0), (0, 10)], [(0, 10), (10, 10)], [(10, 10), (10, 0), (0, 0)]]
    rings = stitch_rings(segments)
    assert len(rings) == 1
    assert rings[0][0] == rings[0][-1], "vòng phải khép kín"


def test_stitch_rings_handles_reversed_segments():
    """OSM không đảm bảo các way cùng chiều - phải tự đảo chiều khi nối."""
    segments = [[(0, 0), (0, 10)], [(10, 10), (0, 10)], [(10, 10), (10, 0), (0, 0)]]
    rings = stitch_rings(segments)
    assert len(rings) == 1
    assert point_in_ring((5, 5), rings[0]) is True


def test_stitch_rings_closes_incomplete_boundary():
    """Ranh giới thiếu đoạn vẫn dùng được (khép tạm) thay vì mất cả quận."""
    rings = stitch_rings([[(0, 0), (0, 10), (10, 10), (10, 0)]])
    assert rings and rings[0][0] == rings[0][-1]


def test_stitch_rings_ignores_degenerate_segments():
    assert stitch_rings([[(0, 0)]]) == []
    assert stitch_rings([]) == []


# --- Điểm trong đa giác -------------------------------------------------------


SQUARE = [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]


@pytest.mark.parametrize(
    "point,expected",
    [((5, 5), True), ((1, 1), True), ((20, 20), False), ((-1, 5), False), ((5, 20), False)],
)
def test_point_in_ring(point, expected):
    assert point_in_ring(point, SQUARE) is expected


def test_district_locator_finds_and_misses():
    locator = DistrictLocator({"Quận Test": [SQUARE]})
    assert locator.district_count == 1
    assert locator.find(5, 5) == "Quận Test"
    assert locator.find(99, 99) is None


# --- Chuyển đổi bản ghi OSM ---------------------------------------------------


def make_element(**tags):
    return {"type": "node", "id": 123, "lat": 21.03, "lon": 105.85, "tags": tags}


def test_osm_element_to_place_extracts_rich_tags():
    """Bản cào cũ chỉ lấy tên + toạ độ, bỏ phí hàng chục tag hữu ích."""
    source = OsmOverpassSource()
    place = source._to_place(make_element(
        name="Phở Thìn",
        amenity="restaurant",
        cuisine="vietnamese;pho",
        phone="+84 24 1234",
        website="https://pho.example",
        opening_hours="Mo-Su 06:00-22:00",
        outdoor_seating="yes",
        air_conditioning="yes",
        **{"diet:vegetarian": "yes", "addr:street": "Lò Đúc", "addr:housenumber": "13"},
    ))
    assert place is not None
    assert place.placeId == "osm-node-123"
    assert place.title == "Phở Thìn"
    assert place.categoryName == "Nhà hàng"
    assert place.cuisine == "vietnamese"
    assert "pho" in place.dishes
    assert place.phone == "+84 24 1234"
    assert place.openingHours == "Mo-Su 06:00-22:00"
    assert "outdoor_seating" in place.amenities
    assert "air_conditioning" in place.amenities
    assert "vegetarian" in place.dietary
    assert "Lò Đúc" in place.address
    assert place.source_url.endswith("/node/123")


def test_osm_place_without_name_is_skipped():
    """Quán không tên thì không hiển thị được cho người dùng."""
    source = OsmOverpassSource()
    assert source._to_place(make_element(amenity="restaurant")) is None


def test_osm_place_without_coordinates_is_skipped():
    source = OsmOverpassSource()
    element = {"type": "node", "id": 1, "tags": {"name": "X", "amenity": "cafe"}}
    assert source._to_place(element) is None


def test_osm_way_uses_center_coordinates():
    """Quán được vẽ dạng way/polygon không có lat/lon trực tiếp, phải lấy `center`."""
    source = OsmOverpassSource()
    element = {
        "type": "way", "id": 55,
        "center": {"lat": 21.0, "lon": 105.8},
        "tags": {"name": "Quán Way", "amenity": "restaurant"},
    }
    place = source._to_place(element)
    assert place is not None and place.placeId == "osm-way-55"
    assert place.location == {"lat": "21.0", "lng": "105.8"}


def test_osm_aliases_exclude_duplicate_of_primary_name():
    source = OsmOverpassSource()
    place = source._to_place(make_element(
        name="Cộng Cà Phê", amenity="cafe",
        **{"name:en": "Cong Caphe", "alt_name": "Cộng Cà Phê"},
    ))
    assert "Cong Caphe" in place.aliases
    assert place.aliases.count("Cộng Cà Phê") == 0, "không lặp lại chính tên chính"


def test_osm_tiles_cover_the_whole_bbox():
    """Chia ô phải phủ kín bbox, nếu không sẽ mất quán ở rìa."""
    source = OsmOverpassSource(bbox=(20.0, 105.0, 20.2, 105.2), tile_size_deg=0.1)
    tiles = list(source._tiles())
    assert len(tiles) == 4
    assert min(t[0] for t in tiles) == 20.0
    assert max(t[2] for t in tiles) == 20.2


def test_osm_source_declares_itself():
    source = OsmOverpassSource()
    assert source.name == "openstreetmap"


# --- Khử trùng lặp khi gộp nguồn ---------------------------------------------


def test_dedupe_keeps_richest_record_not_first():
    """Bug thật: cách cũ giữ bản ghi ĐẦU TIÊN theo thứ tự tên file, nên một đợt cào mới
    (giàu rating/review) bị bản cũ rỗng hơn đè mất chỗ."""
    from data_pipeline.merge_and_prepare_raw import _dedupe_keep_richest

    poor = {"placeId": "ChIJ1", "title": "Quán A"}
    rich = {"placeId": "ChIJ1", "title": "Quán A", "totalScore": 4.5,
            "reviewsCount": 120, "price": "100-200 N ₫", "phone": "0900"}

    kept = _dedupe_keep_richest([poor, rich])
    assert len(kept) == 1
    assert kept[0]["totalScore"] == 4.5, "phải giữ bản giàu thông tin hơn"

    # Đảo thứ tự vẫn ra cùng kết quả - không phụ thuộc tên file nữa.
    kept_reversed = _dedupe_keep_richest([rich, poor])
    assert kept_reversed[0]["totalScore"] == 4.5


def test_dedupe_preserves_first_seen_order():
    from data_pipeline.merge_and_prepare_raw import _dedupe_keep_richest

    records = [
        {"placeId": "a", "title": "A"},
        {"placeId": "b", "title": "B"},
        {"placeId": "a", "title": "A", "phone": "1"},
    ]
    assert [r["placeId"] for r in _dedupe_keep_richest(records)] == ["a", "b"]


def test_dedupe_falls_back_to_title_address_without_place_id():
    from data_pipeline.merge_and_prepare_raw import _dedupe_keep_richest

    records = [
        {"title": "Quán X", "address": "1 Lò Đúc"},
        {"title": "Quán X", "address": "1 Lò Đúc", "totalScore": 4.0},
    ]
    kept = _dedupe_keep_richest(records)
    assert len(kept) == 1 and kept[0]["totalScore"] == 4.0


# --- Khử trùng lặp GIỮA các nguồn --------------------------------------------


def _place(pid, title, lat, lng, **extra):
    return {"placeId": pid, "title": title,
            "location": {"lat": str(lat), "lng": str(lng)}, **extra}


def test_cross_source_merges_same_restaurant_from_osm_and_google():
    """OSM và Google đánh id khác nhau nên bước khử trùng theo placeId không bắt được.
    Đo thật: 22/435 quán Apify đã có sẵn trong dataset từ OSM."""
    from data_pipeline.merge_and_prepare_raw import dedupe_across_sources

    osm = _place("osm-node-1", "Chops", 21.0500, 105.8200)
    google = _place("ChIJx", "Chops Tay Ho", 21.0500, 105.8201, totalScore=4.3)

    kept = dedupe_across_sources([osm, google])
    assert len(kept) == 1
    assert kept[0]["totalScore"] == 4.3, "phải giữ bản có rating"


def test_cross_source_fills_gaps_from_the_discarded_record():
    """Gộp KHÔNG được làm mất dữ liệu: trường nào bản thắng còn trống thì lấy từ bản kia."""
    from data_pipeline.merge_and_prepare_raw import dedupe_across_sources

    osm = _place("osm-node-1", "Ding tea", 21.05, 105.82, phone="0900", cuisine="tea")
    google = _place("ChIJy", "Ding tea Xuân La", 21.05, 105.8201,
                    totalScore=4.1, reviewsCount=88, price="20-50 N ₫")

    kept = dedupe_across_sources([osm, google])
    assert len(kept) == 1
    assert kept[0]["totalScore"] == 4.1      # từ Google
    assert kept[0]["phone"] == "0900"        # giữ lại từ OSM


def test_cross_source_keeps_different_restaurants_that_are_close():
    """Hai quán KHÁC NHAU cạnh nhau trên cùng con phố không được gộp."""
    from data_pipeline.merge_and_prepare_raw import dedupe_across_sources

    a = _place("osm-1", "Phở Thìn", 21.05, 105.82)
    b = _place("osm-2", "Bún Chả Hương Liên", 21.05, 105.8201)
    assert len(dedupe_across_sources([a, b])) == 2


def test_cross_source_keeps_same_name_when_far_apart():
    """Chuỗi cửa hàng: cùng tên nhưng ở hai nơi -> là hai quán thật."""
    from data_pipeline.merge_and_prepare_raw import dedupe_across_sources

    a = _place("osm-1", "Highlands Coffee", 21.05, 105.82)
    b = _place("ChIJz", "Highlands Coffee", 21.02, 105.85)
    assert len(dedupe_across_sources([a, b])) == 2


def test_cross_source_short_names_are_not_substring_matched():
    """"Bún" nằm trong "Bún Chả Hương Liên" nhưng là hai quán khác nhau."""
    from data_pipeline.merge_and_prepare_raw import dedupe_across_sources

    a = _place("osm-1", "Bún", 21.05, 105.82)
    b = _place("ChIJq", "Bún Chả Hương Liên", 21.05, 105.8201)
    assert len(dedupe_across_sources([a, b])) == 2


def test_cross_source_keeps_records_without_coordinates():
    from data_pipeline.merge_and_prepare_raw import dedupe_across_sources

    records = [{"placeId": "x", "title": "Không toạ độ"}]
    assert len(dedupe_across_sources(records)) == 1
