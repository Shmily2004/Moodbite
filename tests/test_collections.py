""""Bộ sưu tập của tôi" (duyệt 2026-09-29) — domain · use case (kho giả) · SQLite · HTTP.

Thứ đáng khoá nhất KHÔNG phải "tạo được rồi đọc ra được", mà là:

  1. bộ sưu tập của NGƯỜI KHÁC phải là 404 ở MỌI thao tác — đọc, đổi tên, xoá, thêm mục,
     bỏ mục — và không để lại dấu vết gì ở dữ liệu của họ;
  2. xoá bộ thì xoá luôn mục bên trong (không để mục mồ côi);
  3. thêm lại mục đã có là idempotent, và không bị chặn bởi giới hạn số mục;
  4. tên rỗng/quá dài bị từ chối chứ không lặng lẽ cắt.
"""
from __future__ import annotations

import sqlite3

import pytest

from src.application.use_cases.manage_collections import (
    AddCollectionItemCommand,
    AddCollectionItemUseCase,
    CollectionNotFoundError,
    CollectionsNotAvailable,
    CreateCollectionUseCase,
    DeleteCollectionUseCase,
    ListCollectionsUseCase,
    RemoveCollectionItemUseCase,
    RenameCollectionUseCase,
)
from src.domain.entities.collection import (
    MAX_COLLECTION_NAME_LENGTH,
    MAX_COLLECTIONS_PER_USER,
    MAX_ITEMS_PER_COLLECTION,
    Collection,
    CollectionItem,
    InvalidCollection,
    ensure_can_add_item,
    ensure_can_create_collection,
    validate_collection_name,
)
from src.domain.entities.saved_item import InvalidSavedItem, SavedItemType
from src.infrastructure.repositories.sqlite_collection_repository import (
    SqliteCollectionRepository,
)
from tests.test_auth_api import API, build_client, register

# ==========================================================================
# Domain — thuần Python
# ==========================================================================


def test_ten_bo_suu_tap_duoc_gon_khoang_trang():
    assert validate_collection_name("  Hẹn   hò  cuối tuần ") == "Hẹn hò cuối tuần"


@pytest.mark.parametrize("ten", ["", "   ", None])
def test_ten_rong_bi_tu_choi(ten):
    with pytest.raises(InvalidCollection):
        validate_collection_name(ten)


def test_ten_qua_dai_bi_TU_CHOI_chu_khong_bi_cat():
    """Người dùng vừa GÕ tên này — cắt lặng lẽ thì họ thấy tên mình bị đổi."""
    validate_collection_name("a" * MAX_COLLECTION_NAME_LENGTH)
    with pytest.raises(InvalidCollection):
        validate_collection_name("a" * (MAX_COLLECTION_NAME_LENGTH + 1))


def test_gioi_han_so_bo_suu_tap():
    ensure_can_create_collection(MAX_COLLECTIONS_PER_USER - 1)
    with pytest.raises(InvalidCollection):
        ensure_can_create_collection(MAX_COLLECTIONS_PER_USER)


def test_bo_day_van_them_lai_duoc_muc_DA_CO():
    """Thêm lại là idempotent, không làm bộ to thêm — không được chặn."""
    ensure_can_add_item(MAX_ITEMS_PER_COLLECTION, already_in_collection=True)
    with pytest.raises(InvalidCollection):
        ensure_can_add_item(MAX_ITEMS_PER_COLLECTION, already_in_collection=False)


def test_to_public_khong_lo_user_id_va_dem_dung_so_muc():
    bo = Collection(
        collection_id="c1",
        user_id="u-bi-mat",
        name="Quán gần công ty",
        items=[CollectionItem(SavedItemType.DISH, "pho-bo", "Phở bò")],
    )
    pub = bo.to_public()
    assert "user_id" not in pub
    assert pub["item_count"] == 1
    assert pub["items"][0] == {
        "item_type": "dish",
        "item_id": "pho-bo",
        "name": "Phở bò",
        "added_at": None,
    }


# ==========================================================================
# Use case — kho giả trong bộ nhớ
# ==========================================================================


class FakeCollectionRepo:
    def __init__(self, ready: bool = True) -> None:
        self._ready = ready
        self.rows: dict = {}  # collection_id -> Collection

    @property
    def is_ready(self) -> bool:
        return self._ready

    def list_for_user(self, user_id):
        return [c for c in self.rows.values() if c.user_id == user_id]

    def get(self, user_id, collection_id):
        c = self.rows.get(collection_id)
        return c if c is not None and c.user_id == user_id else None

    def count_for_user(self, user_id):
        return len(self.list_for_user(user_id))

    def create(self, collection):
        self.rows[collection.collection_id] = collection
        return collection

    def rename(self, user_id, collection_id, name):
        c = self.get(user_id, collection_id)
        if c is None:
            return False
        self.rows[collection_id] = Collection(c.collection_id, c.user_id, name, c.created_at, c.items)
        return True

    def delete(self, user_id, collection_id):
        if self.get(user_id, collection_id) is None:
            return False
        del self.rows[collection_id]
        return True

    def add_item(self, user_id, collection_id, item):
        c = self.get(user_id, collection_id)
        if c is None:
            return False
        con_lai = [i for i in c.items if (i.item_type, i.item_id) != (item.item_type, item.item_id)]
        self.rows[collection_id] = Collection(
            c.collection_id, c.user_id, c.name, c.created_at, [item, *con_lai]
        )
        return True

    def remove_item(self, user_id, collection_id, item_type, item_id):
        c = self.get(user_id, collection_id)
        if c is None:
            return False
        con_lai = [i for i in c.items if (i.item_type, i.item_id) != (item_type, item_id)]
        self.rows[collection_id] = Collection(
            c.collection_id, c.user_id, c.name, c.created_at, con_lai
        )
        return len(con_lai) != len(c.items)


def _ids():
    so = iter(range(1, 1000))
    return lambda: f"c{next(so)}"


def test_use_case_tao_va_liet_ke():
    repo = FakeCollectionRepo()
    bo = CreateCollectionUseCase(repo, new_id=_ids()).execute("u1", "  Hẹn hò ")
    assert bo.name == "Hẹn hò" and bo.collection_id == "c1"
    assert [c.name for c in ListCollectionsUseCase(repo).execute("u1")] == ["Hẹn hò"]
    assert ListCollectionsUseCase(repo).execute("u2") == []


def test_use_case_chan_khi_du_so_bo():
    repo = FakeCollectionRepo()
    tao = CreateCollectionUseCase(repo, new_id=_ids())
    for i in range(MAX_COLLECTIONS_PER_USER):
        tao.execute("u1", f"Bộ {i}")
    with pytest.raises(InvalidCollection):
        tao.execute("u1", "Một bộ nữa")
    # Giới hạn là THEO NGƯỜI, không phải toàn hệ thống.
    tao.execute("u2", "Bộ của người khác")


def test_use_case_bo_cua_nguoi_khac_la_404_o_moi_thao_tac():
    repo = FakeCollectionRepo()
    bo = CreateCollectionUseCase(repo, new_id=_ids()).execute("chu", "Của tôi")
    cid = bo.collection_id

    with pytest.raises(CollectionNotFoundError):
        RenameCollectionUseCase(repo).execute("ke-la", cid, "Cướp")
    with pytest.raises(CollectionNotFoundError):
        DeleteCollectionUseCase(repo).execute("ke-la", cid)
    with pytest.raises(CollectionNotFoundError):
        AddCollectionItemUseCase(repo).execute(
            AddCollectionItemCommand("ke-la", cid, "dish", "pho-bo", "Phở bò")
        )
    with pytest.raises(CollectionNotFoundError):
        RemoveCollectionItemUseCase(repo).execute("ke-la", cid, "dish", "pho-bo")

    # Không có gì thay đổi ở dữ liệu của chủ.
    con = repo.get("chu", cid)
    assert con.name == "Của tôi" and con.items == []


def test_use_case_them_muc_idempotent_va_kiem_loai():
    repo = FakeCollectionRepo()
    cid = CreateCollectionUseCase(repo, new_id=_ids()).execute("u1", "Bộ").collection_id
    them = AddCollectionItemUseCase(repo)
    them.execute(AddCollectionItemCommand("u1", cid, "dish", "pho-bo", "Phở bò"))
    sau = them.execute(AddCollectionItemCommand("u1", cid, "dish", "pho-bo", "Phở bò tái"))
    assert len(sau.items) == 1 and sau.items[0].name == "Phở bò tái"

    with pytest.raises(InvalidSavedItem):
        them.execute(AddCollectionItemCommand("u1", cid, "quan-an", "x", "X"))


def test_use_case_bo_muc_khong_co_van_thanh_cong():
    repo = FakeCollectionRepo()
    cid = CreateCollectionUseCase(repo, new_id=_ids()).execute("u1", "Bộ").collection_id
    assert RemoveCollectionItemUseCase(repo).execute("u1", cid, "dish", "khong-co") is False


def test_use_case_kho_hong_la_503():
    with pytest.raises(CollectionsNotAvailable):
        ListCollectionsUseCase(FakeCollectionRepo(ready=False)).execute("u1")


# ==========================================================================
# SQLite adapter
# ==========================================================================


@pytest.fixture
def repo(tmp_path):
    return SqliteCollectionRepository(tmp_path / "users.db")


def _tao(repo, user, cid, name="Bộ"):
    return repo.create(Collection(collection_id=cid, user_id=user, name=name))


def test_sqlite_tao_doc_doi_ten(repo):
    _tao(repo, "u1", "c1", "Cũ")
    assert repo.rename("u1", "c1", "Mới") is True
    bo = repo.get("u1", "c1")
    assert bo.name == "Mới" and bo.created_at is not None
    assert repo.count_for_user("u1") == 1


def test_sqlite_nguoi_khac_khong_doc_khong_sua_khong_xoa_duoc(repo):
    _tao(repo, "chu", "c1")
    repo.add_item("chu", "c1", CollectionItem(SavedItemType.DISH, "pho-bo", "Phở bò"))

    assert repo.get("ke-la", "c1") is None
    assert repo.list_for_user("ke-la") == []
    assert repo.rename("ke-la", "c1", "X") is False
    assert repo.delete("ke-la", "c1") is False
    assert repo.add_item("ke-la", "c1", CollectionItem(SavedItemType.DISH, "bun", "Bún")) is False
    assert repo.remove_item("ke-la", "c1", SavedItemType.DISH, "pho-bo") is False

    bo = repo.get("chu", "c1")
    assert bo.name == "Bộ"
    assert [i.item_id for i in bo.items] == ["pho-bo"]


def test_sqlite_them_lai_giu_added_at_cap_nhat_ten(repo):
    _tao(repo, "u1", "c1")
    repo.add_item("u1", "c1", CollectionItem(SavedItemType.RESTAURANT, "q1", "Tên cũ"))
    dau = repo.get("u1", "c1").items[0].added_at
    repo.add_item("u1", "c1", CollectionItem(SavedItemType.RESTAURANT, "q1", "Tên mới"))
    items = repo.get("u1", "c1").items
    assert len(items) == 1
    assert items[0].name == "Tên mới" and items[0].added_at == dau


def test_sqlite_xoa_bo_xoa_luon_muc_ben_trong(repo, tmp_path):
    _tao(repo, "u1", "c1")
    _tao(repo, "u1", "c2")
    repo.add_item("u1", "c1", CollectionItem(SavedItemType.DISH, "pho-bo", "Phở bò"))
    repo.add_item("u1", "c2", CollectionItem(SavedItemType.DISH, "bun-cha", "Bún chả"))

    assert repo.delete("u1", "c1") is True

    conn = sqlite3.connect(tmp_path / "users.db")
    try:
        con_lai = conn.execute("SELECT collection_id FROM collection_items").fetchall()
    finally:
        conn.close()
    assert con_lai == [("c2",)], "mục của bộ đã xoá phải bị xoá cùng, mục bộ khác giữ nguyên"


def test_sqlite_bo_muc(repo):
    _tao(repo, "u1", "c1")
    repo.add_item("u1", "c1", CollectionItem(SavedItemType.DISH, "pho-bo", "Phở bò"))
    assert repo.remove_item("u1", "c1", SavedItemType.DISH, "pho-bo") is True
    assert repo.remove_item("u1", "c1", SavedItemType.DISH, "pho-bo") is False
    assert repo.get("u1", "c1").items == []


def test_sqlite_duong_dan_hong_thi_khong_sap(tmp_path):
    """Thiếu/hỏng file KHÔNG làm sập app (CLAUDE.md mục 4.3) — kho báo chưa sẵn sàng."""
    thu_muc = tmp_path / "la-thu-muc.db"
    thu_muc.mkdir()
    hong = SqliteCollectionRepository(thu_muc)
    assert hong.is_ready is False
    assert hong.list_for_user("u1") == []
    assert hong.status()["ready"] is False


# ==========================================================================
# HTTP
# ==========================================================================


@pytest.fixture
def client(tmp_path):
    c, _ = build_client(tmp_path)
    attach_collections(c, tmp_path)
    return c


def attach_collections(client, tmp_path):
    """Lắp kho + use case bộ sưu tập vào container của `build_client` (dựng tay bằng
    `Container.__new__`, nên không tự có). Kho THẬT (SQLite trong tmp_path)."""
    c = client.app.state.container
    kho = SqliteCollectionRepository(tmp_path / "users.db")
    c.collections = kho
    c.list_collections = ListCollectionsUseCase(kho)
    c.create_collection = CreateCollectionUseCase(kho)
    c.rename_collection = RenameCollectionUseCase(kho)
    c.delete_collection = DeleteCollectionUseCase(kho)
    c.add_collection_item = AddCollectionItemUseCase(kho)
    c.remove_collection_item = RemoveCollectionItemUseCase(kho)


def _auth(client, username):
    res = register(client, username=username)
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['data']['token']}"}


def _tao_bo(client, headers, name="Hẹn hò"):
    res = client.post(f"{API}/me/collections", json={"name": name}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["data"]


def test_api_chua_dang_nhap_la_401(client):
    assert client.get(f"{API}/me/collections").status_code == 401
    assert client.post(f"{API}/me/collections", json={"name": "X"}).status_code == 401


def test_api_luong_day_du(client):
    a = _auth(client, "nguoi-a")
    bo = _tao_bo(client, a, "  Quán gần công ty ")
    assert bo["name"] == "Quán gần công ty"
    assert bo["item_count"] == 0 and bo["items"] == []
    cid = bo["collection_id"]

    res = client.post(
        f"{API}/me/collections/{cid}/items",
        json={"item_type": "dish", "item_id": "pho-bo", "name": "Phở bò"},
        headers=a,
    )
    assert res.status_code == 200, res.text
    assert res.json()["data"]["item_count"] == 1

    res = client.patch(f"{API}/me/collections/{cid}", json={"name": "Đổi tên"}, headers=a)
    assert res.status_code == 200 and res.json()["data"]["name"] == "Đổi tên"

    ds = client.get(f"{API}/me/collections", headers=a).json()["data"]
    assert ds["total"] == 1
    assert ds["collections"][0]["items"][0]["item_id"] == "pho-bo"

    res = client.delete(f"{API}/me/collections/{cid}/items/dish/pho-bo", headers=a)
    assert res.status_code == 200

    res = client.delete(f"{API}/me/collections/{cid}", headers=a)
    assert res.status_code == 200
    assert client.get(f"{API}/me/collections", headers=a).json()["data"]["total"] == 0


def test_api_bo_cua_nguoi_khac_la_404_va_khong_lo_gi(client):
    a = _auth(client, "nguoi-a")
    b = _auth(client, "nguoi-b")
    cid = _tao_bo(client, a)["collection_id"]
    client.post(
        f"{API}/me/collections/{cid}/items",
        json={"item_type": "dish", "item_id": "pho-bo", "name": "Phở bò"},
        headers=a,
    )

    goi = [
        client.patch(f"{API}/me/collections/{cid}", json={"name": "Cướp"}, headers=b),
        client.delete(f"{API}/me/collections/{cid}", headers=b),
        client.post(
            f"{API}/me/collections/{cid}/items",
            json={"item_type": "dish", "item_id": "bun", "name": "Bún"},
            headers=b,
        ),
        client.delete(f"{API}/me/collections/{cid}/items/dish/pho-bo", headers=b),
    ]
    for res in goi:
        assert res.status_code == 404, res.text
        assert res.json()["error"]["code"] == "COLLECTION_NOT_FOUND"

    # Mã không tồn tại cho ra ĐÚNG cùng mã lỗi — không phân biệt được với "của người khác".
    khong_co = client.delete(f"{API}/me/collections/khong-ton-tai", headers=b)
    assert khong_co.status_code == 404
    assert khong_co.json()["error"]["code"] == "COLLECTION_NOT_FOUND"

    assert client.get(f"{API}/me/collections", headers=b).json()["data"]["total"] == 0
    cua_a = client.get(f"{API}/me/collections", headers=a).json()["data"]["collections"][0]
    assert cua_a["name"] == "Hẹn hò" and cua_a["item_count"] == 1


def test_api_ten_sai_la_400(client):
    a = _auth(client, "nguoi-a")
    res = client.post(f"{API}/me/collections", json={"name": "   "}, headers=a)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_REQUEST"
    res = client.post(f"{API}/me/collections", json={"name": "x" * 61}, headers=a)
    assert res.status_code == 400


def test_api_them_muc_loai_la_la_400(client):
    a = _auth(client, "nguoi-a")
    cid = _tao_bo(client, a)["collection_id"]
    res = client.post(
        f"{API}/me/collections/{cid}/items",
        json={"item_type": "banh", "item_id": "x", "name": "X"},
        headers=a,
    )
    assert res.status_code == 400
