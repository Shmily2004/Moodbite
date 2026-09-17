"""Test cho bộ sinh người dùng GIẢ LẬP và đánh giá xếp hạng offline.

Bốn điều phải khoá bằng test, vì hỏng một trong số đó là hỏng lặng lẽ:
  1. Không bao giờ ghi vào dữ liệu thật.
  2. Utility của người giả lập không được dựa trên công thức xếp hạng MoodBite
     (nếu không, đánh giá thành vòng tròn và luôn "đẹp").
  3. Độ đo (NDCG/P@K/MRR) đúng với ví dụ tính tay.
  4. Cờ MOODBITE_SYNTHETIC_DATA đọc đúng và hiện ra ở /health và /admin/system.
"""
from __future__ import annotations

import ast
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.synthetic import an_toan, metrics
from scripts.synthetic.an_toan import (
    UnsafeSyntheticPathError,
    apply_synthetic_env,
    assert_safe_out_dir,
    assert_settings_are_synthetic,
    synthetic_paths,
)
from scripts.synthetic.persona import Persona, relevance_grade, restaurant_utility
from src.infrastructure.config.settings import parse_synthetic_flag

ROOT = Path(__file__).resolve().parents[1]


# --- 1. Không ghi vào dữ liệu thật ---------------------------------------------------


def test_duong_dan_mac_dinh_nam_ngoai_du_lieu_that():
    paths = synthetic_paths(an_toan.DEFAULT_OUT_DIR)
    assert_safe_out_dir(paths)  # không ném
    assert paths.interactions.resolve() != an_toan.REAL_INTERACTIONS.resolve()
    assert paths.users_db.resolve() != an_toan.REAL_USERS_DB.resolve()


@pytest.mark.parametrize("out_dir", [
    an_toan.REAL_DATA_DIR,
    an_toan.REAL_DATA_DIR / "con",
])
def test_tu_choi_thu_muc_nam_trong_data_cleaned(out_dir):
    with pytest.raises(UnsafeSyntheticPathError):
        assert_safe_out_dir(synthetic_paths(out_dir))


def test_bien_moi_truong_tro_vao_thu_muc_gia_lap(tmp_path):
    paths = synthetic_paths(tmp_path)
    env: dict = {}
    apply_synthetic_env(paths, env)
    assert Path(env["MOODBITE_INTERACTIONS"]) == paths.interactions
    assert Path(env["MOODBITE_USERS_DB"]) == paths.users_db
    assert env["MOODBITE_SYNTHETIC_DATA"] == "1"
    # Tắt gửi thư: máy có SMTP thật không được bắn thư tới tài khoản demo.
    assert env["MOODBITE_SMTP_HOST"] == ""


def test_settings_tro_vao_file_that_thi_bi_chan(tmp_path):
    paths = synthetic_paths(tmp_path)
    settings_that = SimpleNamespace(
        interactions_path=an_toan.REAL_INTERACTIONS,
        users_db=paths.users_db,
        synthetic_data=True,
    )
    with pytest.raises(UnsafeSyntheticPathError):
        assert_settings_are_synthetic(settings_that, paths)


def test_settings_that_su_doc_bien_gia_lap(tmp_path, monkeypatch):
    """Đi qua đúng `Settings.from_env()` mà app dùng — không chỉ kiểm dict tự dựng."""
    from src.infrastructure.config.settings import Settings

    paths = synthetic_paths(tmp_path)
    env: dict = {}
    apply_synthetic_env(paths, env)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    settings = Settings.from_env()
    assert_settings_are_synthetic(settings, paths)  # không ném
    assert settings.interactions_path.resolve() != an_toan.REAL_INTERACTIONS.resolve()


# --- 2. Utility độc lập với công thức MoodBite ---------------------------------------


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_persona_khong_import_cong_thuc_xep_hang():
    modules = _imported_modules(ROOT / "scripts" / "synthetic" / "persona.py")
    cam = [m for m in modules if "search_ranking" in m
           or m.startswith("src.domain.services") or m.startswith("src.application")]
    assert cam == [], f"persona.py phụ thuộc vào logic MoodBite: {cam}"


def test_utility_khong_doi_khi_diem_cua_moodbite_doi():
    """Đầu ra của mô hình MoodBite (điểm, hạng, cụm) không được ảnh hưởng tới utility."""
    persona = Persona("demo_0001", "P", 21.0, 105.8, ("sad",), ("pho",), 0.5, 3.0, 0.4)
    quan = {"restaurant_id": "r1", "name": "Phở Thìn", "category": "Nhà hàng phở",
            "distance_m": 800, "rating": None, "price_range": None,
            "predicted_score": 0.1, "rank_position": 40, "experience_cluster_id": 1}
    doi_diem = dict(quan, predicted_score=0.99, rank_position=1, experience_cluster_id=6,
                    is_famous=True, match_source="semantic")
    assert restaurant_utility(persona, quan) == restaurant_utility(persona, doi_diem)


def test_utility_rating_none_khong_bi_coi_la_0_sao():
    persona = Persona("demo_0001", "P", 21.0, 105.8, ("sad",), ("pho",), 0.0, 3.0, 0.4)
    base = {"restaurant_id": "r1", "name": "Quán A", "distance_m": 500, "price_range": None}
    khong_ro = restaurant_utility(persona, dict(base, rating=None))
    mot_sao = restaurant_utility(persona, dict(base, rating=1.0))
    assert khong_ro > mot_sao


def test_utility_dung_khau_vi_cao_hon_khong_dung():
    persona = Persona("demo_0001", "P", 21.0, 105.8, ("sad",), ("pho",), 0.0, 3.0, 0.4)
    pho = {"restaurant_id": "x", "name": "Phở Bò Gia Truyền", "distance_m": 500, "rating": None}
    tao_pho = {"restaurant_id": "x", "name": "Tào Phớ Hàng Bạc", "distance_m": 500, "rating": None}
    assert restaurant_utility(persona, pho) > restaurant_utility(persona, tao_pho)


# --- 3. Độ đo trên ví dụ tính tay ----------------------------------------------------


def test_ndcg_tinh_tay():
    # Nhãn [3, 2, 0, 1]. DCG@4 = 7/1 + 3/log2(3) + 0 + 1/log2(5)
    # Lý tưởng [3, 2, 1, 0]: IDCG@4 = 7 + 3/log2(3) + 1/log2(4) = 7 + 1.8928 + 0.5
    dcg = 7 + 3 / math.log2(3) + 1 / math.log2(5)
    idcg = 7 + 3 / math.log2(3) + 1 / 2
    assert metrics.ndcg_at_k([3, 2, 0, 1], 4) == pytest.approx(dcg / idcg)
    assert metrics.ndcg_at_k([3, 2, 1, 0], 4) == pytest.approx(1.0)


def test_ndcg_khong_co_muc_lien_quan_tra_none_va_bi_loai_khoi_trung_binh():
    assert metrics.ndcg_at_k([0, 0, 0], 3) is None
    assert metrics.mean([None, 0.5, 1.0]) == pytest.approx(0.75)


def test_precision_mau_so_luon_la_k():
    assert metrics.precision_at_k([True, False, True, False, False], 5) == pytest.approx(0.4)
    # Danh sách ngắn hơn k: mẫu số vẫn là k.
    assert metrics.precision_at_k([True, True], 5) == pytest.approx(0.4)


def test_mrr():
    assert metrics.reciprocal_rank([False, False, True]) == pytest.approx(1 / 3)
    assert metrics.reciprocal_rank([False, False]) == 0.0


def test_coverage():
    assert metrics.catalog_coverage([["a", "b"], ["b", "c"]], ["a", "b", "c", "d"]) == 0.75


def test_nhan_phan_cap():
    assert [relevance_grade(u) for u in (0.1, 0.5, 0.7, 0.9)] == [0, 1, 2, 3]


def test_baseline_khoang_cach_va_ngau_nhien_on_dinh():
    from scripts.danh_gia_xep_hang import evaluate

    candidates = [
        {"restaurant_id": "xa", "moodbite_rank": 1, "distance_m": 900, "grade": 0},
        {"restaurant_id": "gan", "moodbite_rank": 2, "distance_m": 100, "grade": 3},
    ]
    sessions = [{"session_id": "synthetic-1", "entry": "dish", "candidates": candidates}]
    report = evaluate(sessions, seed=1)
    assert report["metrics"]["distance"]["mrr"] == 1.0
    assert report["metrics"]["moodbite"]["mrr"] == 0.5
    assert report == evaluate(sessions, seed=1)  # xáo ngẫu nhiên có seed -> tái lập được


# --- 4. Cờ dữ liệu giả lập -----------------------------------------------------------


@pytest.mark.parametrize("raw,expected", [
    (None, False), ("", False), ("0", False), ("true", False), ("1", True), (" 1 ", True),
])
def test_doc_co_synthetic(raw, expected):
    assert parse_synthetic_flag(raw) is expected


def test_health_bao_co_synthetic():
    from fastapi.testclient import TestClient

    from src.presentation.api.main import create_app
    from tests.test_api import _container

    container = _container()
    app = create_app(container=container)
    client = TestClient(app)
    assert client.get("/api/v1/health").json()["data"]["synthetic_data"] is False

    container.settings = SimpleNamespace(synthetic_data=True)
    assert client.get("/api/v1/health").json()["data"]["synthetic_data"] is True


def test_admin_system_bao_co_synthetic(tmp_path):
    """Trang quản trị dựa vào trường này để hiện banner "dữ liệu giả lập"."""
    from tests.test_admin_api import API, auth_header, build_client, make_db

    client, _ = build_client(make_db(tmp_path, {
        "place_id": "pho-1", "name": "Phở Bò", "category": "Nhà hàng phở",
        "address": "12 Hàng Đồng", "is_active": 1,
    }))
    headers = auth_header(client)
    data = client.get(f"{API}/admin/system", headers=headers).json()["data"]
    assert data["synthetic_data"] is False

    client.app.state.container.settings = SimpleNamespace(synthetic_data=True)
    data = client.get(f"{API}/admin/system", headers=headers).json()["data"]
    assert data["synthetic_data"] is True
