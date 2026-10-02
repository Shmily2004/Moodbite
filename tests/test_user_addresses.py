""""Địa chỉ của tôi" (duyệt 2026-09-29) — domain · use case (kho giả) · SQLite · HTTP.

Chỗ dễ sai nhất và được khoá ở đây:

  1. KHÔNG BAO GIỜ có hai địa chỉ mặc định cho một người — đặt mặc định mới phải tắt cái
     cũ trong cùng một giao dịch, và chỉ mục UNIQUE của CSDL là lưới an toàn thứ hai;
  2. toạ độ ngoài Hà Nội bị từ chối kèm câu nói rõ vì sao;
  3. `address_text` bỏ trống là `None` (không có dữ liệu) — không bịa, không chuỗi rỗng;
     và đổi nhãn KHÔNG được lặng lẽ xoá mô tả;
  4. địa chỉ của người khác là 404.
"""
from __future__ import annotations

import math
import sqlite3

import pytest

from src.application.use_cases.manage_addresses import (
    AddressNotFoundError,
    AddressesNotAvailable,
    CreateAddressCommand,
    CreateAddressUseCase,
    DeleteAddressUseCase,
    ListAddressesUseCase,
    UpdateAddressCommand,
    UpdateAddressUseCase,
)
from src.domain.entities.user_address import (
    MAX_ADDRESS_LABEL_LENGTH,
    MAX_ADDRESS_TEXT_LENGTH,
    MAX_ADDRESSES_PER_USER,
    InvalidUserAddress,
    UserAddress,
    ensure_can_add_address,
    resolve_default_flag,
    validate_address_coordinates,
    validate_address_label,
    validate_address_text,
)
from src.infrastructure.repositories.sqlite_user_address_repository import (
    SqliteUserAddressRepository,
)
from tests.test_auth_api import API, build_client, register

HO_GUOM = (21.0285, 105.8542)
CAU_GIAY = (21.0368, 105.7826)
SAI_GON = (10.7769, 106.7009)

# ==========================================================================
# Domain
# ==========================================================================


def test_nhan_gon_khoang_trang_va_gioi_han_do_dai():
    assert validate_address_label("  Nhà   bố mẹ ") == "Nhà bố mẹ"
    with pytest.raises(InvalidUserAddress):
        validate_address_label("  ")
    with pytest.raises(InvalidUserAddress):
        validate_address_label("a" * (MAX_ADDRESS_LABEL_LENGTH + 1))


def test_mo_ta_bo_trong_la_None_khong_phai_chuoi_rong():
    assert validate_address_text(None) is None
    assert validate_address_text("   ") is None
    assert validate_address_text(" Ngõ 12 Trần Duy Hưng ") == "Ngõ 12 Trần Duy Hưng"
    with pytest.raises(InvalidUserAddress):
        validate_address_text("x" * (MAX_ADDRESS_TEXT_LENGTH + 1))


def test_toa_do_trong_ha_noi_thi_nhan():
    assert validate_address_coordinates(*HO_GUOM) == HO_GUOM


@pytest.mark.parametrize("toa_do", [SAI_GON, (0.0, 0.0), (math.nan, 105.85), (21.0, math.inf)])
def test_toa_do_ngoai_ha_noi_bi_tu_choi_kem_ly_do(toa_do):
    with pytest.raises(InvalidUserAddress, match="Hà Nội"):
        validate_address_coordinates(*toa_do)


def test_toa_do_khong_phai_so():
    with pytest.raises(InvalidUserAddress):
        validate_address_coordinates("abc", 105.8)


def test_dia_chi_dau_tien_tu_thanh_mac_dinh_cac_dia_chi_sau_thi_khong():
    assert resolve_default_flag(None, 0) is True
    assert resolve_default_flag(None, 1) is False
    # Người dùng nói rõ thì theo người dùng.
    assert resolve_default_flag(False, 0) is False
    assert resolve_default_flag(True, 3) is True


def test_gioi_han_so_dia_chi():
    ensure_can_add_address(MAX_ADDRESSES_PER_USER - 1)
    with pytest.raises(InvalidUserAddress):
        ensure_can_add_address(MAX_ADDRESSES_PER_USER)


# ==========================================================================
# Use case — kho giả
# ==========================================================================


class FakeAddressRepo:
    def __init__(self, ready: bool = True) -> None:
        self._ready = ready
        self.rows: dict = {}

    @property
    def is_ready(self):
        return self._ready

    def list_for_user(self, user_id):
        return [a for a in self.rows.values() if a.user_id == user_id]

    def get(self, user_id, address_id):
        a = self.rows.get(address_id)
        return a if a is not None and a.user_id == user_id else None

    def count_for_user(self, user_id):
        return len(self.list_for_user(user_id))

    def _bo_mac_dinh(self, user_id):
        for k, a in list(self.rows.items()):
            if a.user_id == user_id and a.is_default:
                self.rows[k] = _thay(a, is_default=False)

    def create(self, address):
        if address.is_default:
            self._bo_mac_dinh(address.user_id)
        self.rows[address.address_id] = address
        return address

    def update(self, user_id, address_id, *, label=None, address_text=None,
               clear_address_text=False, is_default=None):
        a = self.get(user_id, address_id)
        if a is None:
            return None
        if label is not None:
            a = _thay(a, label=label)
        if clear_address_text:
            a = _thay(a, address_text=None)
        elif address_text is not None:
            a = _thay(a, address_text=address_text)
        if is_default is True:
            self._bo_mac_dinh(user_id)
            a = _thay(a, is_default=True)
        elif is_default is False:
            a = _thay(a, is_default=False)
        self.rows[address_id] = a
        return a

    def delete(self, user_id, address_id):
        if self.get(user_id, address_id) is None:
            return False
        del self.rows[address_id]
        return True


def _thay(a: UserAddress, **doi) -> UserAddress:
    du_lieu = {**a.__dict__, **doi}
    return UserAddress(**du_lieu)


def _ids():
    so = iter(range(1, 1000))
    return lambda: f"a{next(so)}"


def _cmd(user="u1", label="Nhà", toa_do=HO_GUOM, **kw):
    return CreateAddressCommand(user_id=user, label=label, lat=toa_do[0], lng=toa_do[1], **kw)


def test_use_case_dia_chi_dau_la_mac_dinh_dia_chi_thu_hai_thi_khong():
    repo = FakeAddressRepo()
    tao = CreateAddressUseCase(repo, new_id=_ids())
    nha = tao.execute(_cmd(label="Nhà"))
    cong_ty = tao.execute(_cmd(label="Công ty", toa_do=CAU_GIAY))
    assert nha.is_default is True
    assert cong_ty.is_default is False
    assert nha.address_text is None


def test_use_case_ngoai_ha_noi_khong_luu_gi():
    repo = FakeAddressRepo()
    with pytest.raises(InvalidUserAddress):
        CreateAddressUseCase(repo, new_id=_ids()).execute(_cmd(toa_do=SAI_GON))
    assert repo.rows == {}


def test_use_case_dat_mac_dinh_moi_thi_bo_mac_dinh_cu():
    repo = FakeAddressRepo()
    tao = CreateAddressUseCase(repo, new_id=_ids())
    nha = tao.execute(_cmd(label="Nhà"))
    ct = tao.execute(_cmd(label="Công ty", toa_do=CAU_GIAY))
    UpdateAddressUseCase(repo).execute(
        UpdateAddressCommand(user_id="u1", address_id=ct.address_id, is_default=True)
    )
    mac_dinh = [a.address_id for a in repo.list_for_user("u1") if a.is_default]
    assert mac_dinh == [ct.address_id]
    assert repo.get("u1", nha.address_id).is_default is False


def test_use_case_doi_nhan_KHONG_xoa_mo_ta():
    repo = FakeAddressRepo()
    a = CreateAddressUseCase(repo, new_id=_ids()).execute(_cmd(address_text="Ngõ 12"))
    sau = UpdateAddressUseCase(repo).execute(
        UpdateAddressCommand(user_id="u1", address_id=a.address_id, label="Nhà mới")
    )
    assert sau.label == "Nhà mới" and sau.address_text == "Ngõ 12"

    xoa = UpdateAddressUseCase(repo).execute(
        UpdateAddressCommand(
            user_id="u1", address_id=a.address_id, address_text="", address_text_provided=True
        )
    )
    assert xoa.address_text is None


def test_use_case_dia_chi_nguoi_khac_la_404():
    repo = FakeAddressRepo()
    a = CreateAddressUseCase(repo, new_id=_ids()).execute(_cmd(user="chu"))
    with pytest.raises(AddressNotFoundError):
        UpdateAddressUseCase(repo).execute(
            UpdateAddressCommand(user_id="ke-la", address_id=a.address_id, label="X")
        )
    with pytest.raises(AddressNotFoundError):
        DeleteAddressUseCase(repo).execute("ke-la", a.address_id)
    assert repo.get("chu", a.address_id).label == "Nhà"


def test_use_case_kho_hong_la_503():
    with pytest.raises(AddressesNotAvailable):
        ListAddressesUseCase(FakeAddressRepo(ready=False)).execute("u1")


# ==========================================================================
# SQLite adapter
# ==========================================================================


@pytest.fixture
def repo(tmp_path):
    return SqliteUserAddressRepository(tmp_path / "users.db")


def _dc(aid, user="u1", default=False, text=None, label="Nhà"):
    return UserAddress(
        address_id=aid, user_id=user, label=label, address_text=text,
        lat=HO_GUOM[0], lng=HO_GUOM[1], is_default=default,
    )


def test_sqlite_tao_doc_va_mac_dinh_dung_dau(repo):
    repo.create(_dc("a1", label="Công ty"))
    repo.create(_dc("a2", default=True, label="Nhà"))
    ds = repo.list_for_user("u1")
    assert [a.address_id for a in ds] == ["a2", "a1"]
    assert ds[0].address_text is None
    assert ds[0].lat == HO_GUOM[0] and ds[0].created_at is not None


def test_sqlite_chi_mot_mac_dinh_moi_nguoi(repo):
    repo.create(_dc("a1", default=True))
    repo.create(_dc("a2", default=True))  # tạo mới làm mặc định -> a1 tự thôi
    assert [a.address_id for a in repo.list_for_user("u1") if a.is_default] == ["a2"]

    repo.update("u1", "a1", is_default=True)
    assert [a.address_id for a in repo.list_for_user("u1") if a.is_default] == ["a1"]

    # Người KHÁC có mặc định riêng, không ảnh hưởng lẫn nhau.
    repo.create(_dc("b1", user="u2", default=True))
    assert repo.get("u1", "a1").is_default is True
    assert repo.get("u2", "b1").is_default is True


def test_sqlite_chi_muc_unique_chan_hai_mac_dinh_neu_ai_do_ghi_tat(repo, tmp_path):
    """Lưới an toàn thứ hai: ghi thẳng bỏ qua bước tắt cờ cũ thì CSDL phải từ chối."""
    repo.create(_dc("a1", default=True))
    conn = sqlite3.connect(tmp_path / "users.db")
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO user_addresses VALUES ('a2','u1','X',NULL,21.0,105.8,1,'2026-01-01')"
            )
    finally:
        conn.close()


def test_sqlite_sua_mo_ta_va_xoa_mo_ta(repo):
    repo.create(_dc("a1", text="Ngõ 5"))
    assert repo.update("u1", "a1", label="Nhà mới").address_text == "Ngõ 5"
    assert repo.update("u1", "a1", address_text="Ngõ 7").address_text == "Ngõ 7"
    assert repo.update("u1", "a1", clear_address_text=True).address_text is None


def test_sqlite_nguoi_khac_khong_sua_khong_xoa_duoc(repo):
    repo.create(_dc("a1", user="chu", default=True))
    assert repo.get("ke-la", "a1") is None
    assert repo.update("ke-la", "a1", label="X") is None
    assert repo.update("ke-la", "a1", is_default=False) is None
    assert repo.delete("ke-la", "a1") is False
    con = repo.get("chu", "a1")
    assert con.label == "Nhà" and con.is_default is True


def test_sqlite_xoa_mac_dinh_thi_khong_con_mac_dinh(repo):
    repo.create(_dc("a1", default=True))
    repo.create(_dc("a2"))
    assert repo.delete("u1", "a1") is True
    assert [a.is_default for a in repo.list_for_user("u1")] == [False]


def test_sqlite_duong_dan_hong_thi_khong_sap(tmp_path):
    thu_muc = tmp_path / "la-thu-muc.db"
    thu_muc.mkdir()
    hong = SqliteUserAddressRepository(thu_muc)
    assert hong.is_ready is False
    assert hong.list_for_user("u1") == []


# ==========================================================================
# HTTP
# ==========================================================================


def attach_addresses(client, tmp_path):
    c = client.app.state.container
    kho = SqliteUserAddressRepository(tmp_path / "users.db")
    c.addresses = kho
    c.list_addresses = ListAddressesUseCase(kho)
    c.create_address = CreateAddressUseCase(kho)
    c.update_address = UpdateAddressUseCase(kho)
    c.delete_address = DeleteAddressUseCase(kho)


@pytest.fixture
def client(tmp_path):
    c, _ = build_client(tmp_path)
    attach_addresses(c, tmp_path)
    return c


def _auth(client, username):
    res = register(client, username=username)
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['data']['token']}"}


def _them(client, headers, label="Nhà", toa_do=HO_GUOM, **kw):
    return client.post(
        f"{API}/me/addresses",
        json={"label": label, "latitude": toa_do[0], "longitude": toa_do[1], **kw},
        headers=headers,
    )


def test_api_chua_dang_nhap_la_401(client):
    assert client.get(f"{API}/me/addresses").status_code == 401


def test_api_luong_day_du(client):
    a = _auth(client, "nguoi-a")
    res = _them(client, a, label="Nhà", address_text="Ngõ 12")
    assert res.status_code == 201, res.text
    nha = res.json()["data"]
    assert nha["is_default"] is True and nha["address_text"] == "Ngõ 12"

    ct = _them(client, a, label="Công ty", toa_do=CAU_GIAY).json()["data"]
    assert ct["is_default"] is False and ct["address_text"] is None

    res = client.patch(
        f"{API}/me/addresses/{ct['address_id']}", json={"is_default": True}, headers=a
    )
    assert res.status_code == 200 and res.json()["data"]["is_default"] is True

    ds = client.get(f"{API}/me/addresses", headers=a).json()["data"]
    assert ds["total"] == 2
    assert [x["label"] for x in ds["addresses"] if x["is_default"]] == ["Công ty"]

    # Đổi nhãn mà không gửi address_text -> mô tả GIỮ NGUYÊN.
    res = client.patch(
        f"{API}/me/addresses/{nha['address_id']}", json={"label": "Nhà mình"}, headers=a
    )
    assert res.json()["data"]["address_text"] == "Ngõ 12"
    # Gửi null -> XOÁ mô tả.
    res = client.patch(
        f"{API}/me/addresses/{nha['address_id']}", json={"address_text": None}, headers=a
    )
    assert res.json()["data"]["address_text"] is None

    assert client.delete(f"{API}/me/addresses/{nha['address_id']}", headers=a).status_code == 200
    assert client.get(f"{API}/me/addresses", headers=a).json()["data"]["total"] == 1


def test_api_ngoai_ha_noi_la_400_kem_ly_do(client):
    a = _auth(client, "nguoi-a")
    res = _them(client, a, toa_do=SAI_GON)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_REQUEST"
    assert "Hà Nội" in res.json()["error"]["message"]


def test_api_dia_chi_nguoi_khac_la_404(client):
    a = _auth(client, "nguoi-a")
    b = _auth(client, "nguoi-b")
    aid = _them(client, a).json()["data"]["address_id"]

    for res in [
        client.patch(f"{API}/me/addresses/{aid}", json={"label": "X"}, headers=b),
        client.patch(f"{API}/me/addresses/{aid}", json={"is_default": True}, headers=b),
        client.delete(f"{API}/me/addresses/{aid}", headers=b),
    ]:
        assert res.status_code == 404, res.text
        assert res.json()["error"]["code"] == "ADDRESS_NOT_FOUND"

    assert client.get(f"{API}/me/addresses", headers=b).json()["data"]["total"] == 0
    cua_a = client.get(f"{API}/me/addresses", headers=a).json()["data"]["addresses"][0]
    assert cua_a["label"] == "Nhà" and cua_a["is_default"] is True


def test_api_thieu_toa_do_la_400(client):
    a = _auth(client, "nguoi-a")
    res = client.post(f"{API}/me/addresses", json={"label": "Nhà"}, headers=a)
    assert res.status_code == 400


def test_toa_do_dung_TEN_TRUONG_chung_cua_API_latitude_longitude():
    """Đổi 2026-10-02: mọi endpoint khác (`/search`, `/dishes/...`, kết quả quán) đều dùng
    `latitude`/`longitude`. Riêng địa chỉ từng dùng `lat`/`lng` - client phải nhớ hai bộ
    tên cho cùng một khái niệm. Sửa khi endpoint còn mới, chưa ai phụ thuộc."""
    from src.domain.entities.user_address import UserAddress

    cong = UserAddress(address_id="a", user_id="u", label="Nhà", address_text=None,
                       lat=HO_GUOM[0], lng=HO_GUOM[1], is_default=True)
    ra = cong.to_public()

    assert ra["latitude"] == HO_GUOM[0] and ra["longitude"] == HO_GUOM[1]
    assert "lat" not in ra and "lng" not in ra
