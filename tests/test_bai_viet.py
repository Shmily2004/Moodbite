"""Test BÀI VIẾT (cẩm nang + tin cập nhật): domain -> use case -> kho SQLite thật -> HTTP.

Tầng trên cùng là router. Dựng FastAPI TỐI THIỂU chỉ gắn hai router của bài viết, không dựng
cả container (container đọc dataset thật, chậm và không liên quan). Kho SQLite dùng bản THẬT
trong tmp_path, vì chống trùng đường dẫn và chặn nháp là hành vi nằm ở kho, bản giả không
tái hiện được.

Trọng tâm: BÀI NHÁP KHÔNG LỌT RA NGOÀI, và bài web bắt buộc có nguồn.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.application.use_cases.manage_posts import (
    CreatePostUseCase,
    DeletePostUseCase,
    GetPostUseCase,
    GetPublishedPostUseCase,
    ListAllPostsUseCase,
    ListPublishedPostsUseCase,
    PostInput,
    PostNotFoundError,
    PostsNotAvailable,
    UpdatePostUseCase,
)
from src.domain.entities.post import (
    InvalidPost,
    MAX_TITLE_LENGTH,
    Post,
    PostOrigin,
    PostStatus,
    make_slug,
    validate_post_fields,
)
from src.infrastructure.repositories.sqlite_post_repository import SqlitePostRepository
from src.presentation.api.dependencies import require_admin
from src.presentation.api.error_handlers import register_error_handlers
from src.presentation.api.routers import admin_posts, posts


# --- Domain (thuần Python, không cần kho) ------------------------------------------------

def test_slug_bo_dau_va_doi_d():
    # Tiếng Việt phải thành đường dẫn ASCII; "đ" không tách được bằng NFD nên đổi tay.
    assert make_slug("Phở Bò Đặc Biệt") == "pho-bo-dac-biet"


def test_slug_tieu_de_toan_ky_tu_la_dung_du_phong():
    # Không để slug rỗng: use case sẽ thêm hậu tố số để không trùng.
    assert make_slug("!!!") == "bai-viet"


def test_bai_web_thieu_nguon_bi_tu_choi():
    # Nội dung của người khác đã viết lại mà không ghi nguồn thì không kiểm chứng được.
    with pytest.raises(InvalidPost):
        validate_post_fields(
            title="Tin cập nhật", summary="", body="Nội dung",
            origin=PostOrigin.WEB_SAMPLE, source_name=None, source_url=None,
        )


def test_bai_admin_khong_can_nguon():
    # Chủ bài tự viết thì nguồn là tuỳ chọn, không bắt buộc.
    tieu_de, _, _, ten, url = validate_post_fields(
        title="Cẩm nang", summary="", body="Nội dung",
        origin=PostOrigin.ADMIN, source_name=None, source_url=None,
    )
    assert (tieu_de, ten, url) == ("Cẩm nang", None, None)


def test_tieu_de_qua_dai_bi_bao_loi_khong_tu_cat():
    # Người viết phải thấy đúng cái được lưu: báo lỗi, KHÔNG cắt im lặng.
    with pytest.raises(InvalidPost, match=str(MAX_TITLE_LENGTH)):
        validate_post_fields(
            title="a" * (MAX_TITLE_LENGTH + 1), summary="", body="x",
            origin=PostOrigin.ADMIN, source_name=None, source_url=None,
        )


def test_nguon_khong_phai_http_bi_tu_choi():
    with pytest.raises(InvalidPost):
        validate_post_fields(
            title="t", summary="", body="x", origin=PostOrigin.ADMIN,
            source_name="Báo", source_url="javascript:alert(1)",
        )


# --- Use case + kho SQLite thật ---------------------------------------------------------

@pytest.fixture
def kho(tmp_path):
    return SqlitePostRepository(tmp_path / "users.db")


@pytest.fixture
def uc(kho):
    return SimpleNamespace(
        tao=CreatePostUseCase(kho),
        sua=UpdatePostUseCase(kho),
        xoa=DeletePostUseCase(kho),
        danh_sach_cong_khai=ListPublishedPostsUseCase(kho),
        xem_cong_khai=GetPublishedPostUseCase(kho),
        danh_sach_tat_ca=ListAllPostsUseCase(kho),
        xem=GetPostUseCase(kho),
    )


def _nhap(**ghi_de) -> PostInput:
    mac_dinh = dict(
        title="Cẩm nang phở Hà Nội", summary="Tóm tắt", body="Nội dung bài",
        status=PostStatus.DRAFT, origin=PostOrigin.ADMIN,
    )
    mac_dinh.update(ghi_de)
    return PostInput(**mac_dinh)


def test_tao_bai_moi_luon_la_nhap_khi_admin_khong_chon(uc):
    bai = uc.tao.execute(_nhap())
    assert bai.status is PostStatus.DRAFT
    assert bai.published_at is None


def test_nhap_khong_lot_ra_trang_cong_khai(uc):
    # Điều quan trọng nhất của tính năng: nháp chỉ admin thấy.
    uc.tao.execute(_nhap(title="Bản nháp bí mật"))
    assert uc.danh_sach_cong_khai.execute() == []
    with pytest.raises(PostNotFoundError):
        uc.xem_cong_khai.execute("ban-nhap-bi-mat")


def test_cong_bo_roi_moi_hien_va_dong_dau_gio_mot_lan(uc):
    bai = uc.tao.execute(_nhap())
    cong_bo = uc.sua.execute(bai.post_id, _nhap(status=PostStatus.PUBLISHED))
    assert cong_bo.published_at is not None
    assert [b.post_id for b in uc.danh_sach_cong_khai.execute()] == [bai.post_id]

    # Về nháp rồi công khai lại: giữ giờ công khai đầu tiên, để danh sách không nhảy lung tung.
    ve_nhap = uc.sua.execute(bai.post_id, _nhap(status=PostStatus.DRAFT))
    lai = uc.sua.execute(bai.post_id, _nhap(status=PostStatus.PUBLISHED))
    assert lai.published_at == cong_bo.published_at
    assert ve_nhap.published_at == cong_bo.published_at


def test_trung_tieu_de_van_tao_duoc_va_co_duong_dan_khac(uc):
    # Hai bài cùng tên là chuyện thường; không được từ chối, chỉ đổi đường dẫn.
    a = uc.tao.execute(_nhap())
    b = uc.tao.execute(_nhap())
    assert a.slug != b.slug
    assert b.slug.startswith(a.slug)


def test_sua_tieu_de_khong_doi_duong_dan(uc):
    # Link đã gửi đi không được gãy vì admin sửa tiêu đề.
    bai = uc.tao.execute(_nhap(title="Tên cũ"))
    sua = uc.sua.execute(bai.post_id, _nhap(title="Tên hoàn toàn mới"))
    assert sua.slug == bai.slug


def test_sua_bai_khong_ton_tai_bao_404(uc):
    with pytest.raises(PostNotFoundError):
        uc.sua.execute("khong-co", _nhap())


def test_xoa_roi_khong_con_thay(uc):
    bai = uc.tao.execute(_nhap())
    uc.xoa.execute(bai.post_id)
    with pytest.raises(PostNotFoundError):
        uc.xem.execute(bai.post_id)
    with pytest.raises(PostNotFoundError):
        uc.xoa.execute(bai.post_id)


def test_kho_khong_mo_duoc_thi_bao_503_khong_lam_sap(tmp_path):
    kho_hong = SqlitePostRepository(tmp_path / "khong-co-thu-muc" / "x" / "users.db")
    # Giả lập đường dẫn không ghi được: kho phải báo "chưa sẵn sàng" chứ không ném lỗi thô.
    kho_hong._error = "không mở được kho (giả lập)"
    with pytest.raises(PostsNotAvailable):
        ListPublishedPostsUseCase(kho_hong).execute()


def test_kho_thiet_lap_dung_trang_thai_cua_bai(kho):
    tao = CreatePostUseCase(kho).execute(_nhap(status=PostStatus.PUBLISHED))
    assert kho.get(tao.post_id).status is PostStatus.PUBLISHED
    assert kho.slug_taken(tao.slug)
    assert not kho.slug_taken("chua-co-bai-nay")


# --- Router (HTTP) ----------------------------------------------------------------------

@pytest.fixture
def client(tmp_path, uc):
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(posts.router, prefix="/api/v1")
    app.include_router(admin_posts.router, prefix="/api/v1")
    # Admin thật cần cấu hình tài khoản quản trị; test này chỉ kiểm phần bài viết nên
    # bỏ qua chốt xác thực. Chốt đó được kiểm riêng ở `test_router_quan_tri_gan_chot_admin`.
    app.dependency_overrides[require_admin] = lambda: "admin-test"
    app.state.container = SimpleNamespace(
        list_published_posts=uc.danh_sach_cong_khai,
        get_published_post=uc.xem_cong_khai,
        list_all_posts=uc.danh_sach_tat_ca,
        get_post=uc.xem,
        create_post=uc.tao,
        update_post=uc.sua,
        delete_post=uc.xoa,
    )
    return TestClient(app, raise_server_exceptions=False)


def test_router_quan_tri_gan_chot_admin():
    # Router quản trị PHẢI gắn `require_admin` ở cấp router, để endpoint thêm sau không quên.
    gan = [dep.dependency for dep in admin_posts.router.dependencies]
    assert require_admin in gan


def test_cong_khai_khong_thay_nhap_qua_http(client, uc):
    uc.tao.execute(_nhap(title="Bài nháp HTTP"))
    res = client.get("/api/v1/posts")
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 0


def test_mot_bai_nhap_tra_404_qua_http_nhu_khong_ton_tai(client, uc):
    bai = uc.tao.execute(_nhap(title="Nháp ẩn"))
    res = client.get(f"/api/v1/posts/{bai.slug}")
    assert res.status_code == 404


def test_cong_bo_roi_cong_khai_qua_http(client, uc):
    bai = uc.tao.execute(_nhap(title="Phở Hà Nội", status=PostStatus.PUBLISHED))
    res = client.get("/api/v1/posts")
    assert res.status_code == 200
    danh_sach = res.json()["data"]["posts"]
    assert [p["slug"] for p in danh_sach] == [bai.slug]
    chi_tiet = client.get(f"/api/v1/posts/{bai.slug}")
    assert chi_tiet.status_code == 200
    assert chi_tiet.json()["data"]["post"]["title"] == "Phở Hà Nội"

