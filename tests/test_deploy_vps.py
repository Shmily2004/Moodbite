"""Khoá `scripts/deploy_vps.py` - công cụ đưa bản mới lên VPS.

KHÔNG test nào chạm mạng, ssh hay npm: lệnh ra ngoài đều bị chặn. Những gì khoá ở đây là thứ
đã (hoặc rất dễ) gây hại thật trên production:

  * Chuỗi lệnh chạy trên VPS không được có dấu nháy kép (đi qua ssh.exe của Windows).
  * Bản build bị Git Bash đổi địa chỉ API thành `D:/Git/api/v1` phải bị chặn TRƯỚC khi chép lên.
  * Tham số từ bàn phím (host, commit) không được lọt ký tự lạ vào lệnh chạy bằng root.
  * Các bước cập nhật code/dữ liệu KHÔNG được đụng tới kho tài khoản.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location("deploy_vps", ROOT / "scripts" / "deploy_vps.py")
deploy = importlib.util.module_from_spec(_SPEC)
sys.modules["deploy_vps"] = deploy
_SPEC.loader.exec_module(deploy)

HOST = "root@luunguyet.id.vn"


def _moi_lenh_tren_vps() -> dict[str, str]:
    return {
        "backend": deploy.backend_command(False),
        "data": deploy.backend_command(True),
        "rollback": deploy.rollback_command("207f86a"),
        "status": deploy.status_command(),
        "frontend": deploy.frontend_install_command("/tmp/moodbite_dist_x"),
        "backup": deploy.backup_command("/tmp/mb_users_x.db"),
    }


# --- Tham số từ bàn phím --------------------------------------------------------------------


def test_parse_host_nhan_dia_chi_hop_le():
    assert deploy.parse_host(HOST) == (HOST, "luunguyet.id.vn")


@pytest.mark.parametrize(
    "host",
    [
        "",
        "luunguyet.id.vn",  # thiếu user
        "root@",
        "@luunguyet.id.vn",
        "-oProxyCommand=calc@host",  # bắt đầu bằng '-' sẽ bị ssh hiểu thành tuỳ chọn
        "root@host; rm -rf /",
        "root@ho st",
        "root@host`id`",
    ],
)
def test_parse_host_tu_choi_chuoi_la(host):
    with pytest.raises(ValueError):
        deploy.parse_host(host)


@pytest.mark.parametrize("commit", ["207f86a", "708e206a41009580e2ec5734d3e7d352734e31de"])
def test_ma_commit_hop_le(commit):
    assert deploy.COMMIT_RE.match(commit)


@pytest.mark.parametrize("commit", ["main", "abc", "207F86A", "207f86a; reboot", "--force", ""])
def test_ma_commit_la_bi_tu_choi(commit):
    assert not deploy.COMMIT_RE.match(commit)


# --- Lệnh chạy trên VPS ---------------------------------------------------------------------


@pytest.mark.parametrize("ten", list(_moi_lenh_tren_vps()))
def test_lenh_tren_vps_khong_co_dau_nhay_kep(ten):
    assert '"' not in _moi_lenh_tren_vps()[ten]


def test_backend_dung_thu_tu_pull_roi_cai_roi_khoi_dong_lai():
    lenh = deploy.backend_command(with_data=False)
    thu_tu = [
        "set -e",
        "cd /opt/moodbite",
        "git checkout -q main",
        "git pull --ff-only",
        "pip install -q -r requirements.txt",
        "systemctl restart moodbite",
        "HEALTH_OK",
    ]
    vi_tri = [lenh.index(phan) for phan in thu_tu]
    assert vi_tri == sorted(vi_tri)
    assert lenh.startswith("set -e")


def test_cd_truoc_moi_sudo_vi_moodbite_khong_vao_duoc_root():
    # Đứng ở /root thì `sudo -u moodbite python` lỗi getcwd (Permission denied).
    for lenh in (deploy.backend_command(True), deploy.rollback_command("207f86a")):
        assert lenh.index("cd /opt/moodbite") < lenh.index("sudo -u moodbite")


def test_cap_nhat_du_lieu_giu_quan_da_an_va_dung_truoc_khi_khoi_dong_lai():
    lenh = deploy.backend_command(with_data=True)
    assert "build_sqlite.py --keep-hidden" in lenh
    assert lenh.index("build_sqlite.py") < lenh.index("build_dish_catalog.py")
    assert lenh.index("build_dish_catalog.py") < lenh.index("systemctl restart")


def test_backend_khong_dung_build_du_lieu_khi_khong_yeu_cau():
    assert "build_sqlite" not in deploy.backend_command(with_data=False)


@pytest.mark.parametrize("co_du_lieu", [False, True])
def test_cap_nhat_khong_bao_gio_dung_vao_kho_tai_khoan(co_du_lieu):
    """`moodbite_users.db` là dữ liệu gốc: mất là mất hẳn."""
    lenh = deploy.backend_command(co_du_lieu)
    assert "moodbite_users" not in lenh
    assert "rm " not in lenh


def test_backup_dung_api_backup_va_khoa_quyen_file():
    lenh = deploy.backup_command("/tmp/mb_users_x.db")
    assert "s.backup(d)" in lenh
    assert deploy.REMOTE_USERS_DB in lenh
    assert "chmod 600 /tmp/mb_users_x.db" in lenh
    assert "build_sqlite" not in lenh


def test_frontend_chep_noi_dung_khong_xoa_thu_muc_web_cu():
    lenh = deploy.frontend_install_command("/tmp/moodbite_dist_x")
    assert "cp -r /tmp/moodbite_dist_x/. /var/www/moodbite/" in lenh
    # Xoá thư mục web làm vỡ các tab đang mở bản cũ (JS nạp theo nhu cầu).
    assert "rm -rf /var/www" not in lenh
    assert "rm -rf /tmp/moodbite_dist_x" in lenh


@pytest.mark.skipif(sys.platform == "win32", reason="bash.exe trên Windows có thể là stub WSL")
@pytest.mark.parametrize("ten", list(_moi_lenh_tren_vps()))
def test_lenh_tren_vps_dung_cu_phap_bash(ten):
    ket_qua = subprocess.run(
        ["bash", "-n", "-c", _moi_lenh_tren_vps()[ten]], capture_output=True, text=True
    )
    assert ket_qua.returncode == 0, ket_qua.stderr


# --- Kiểm tra bản build ---------------------------------------------------------------------


def _dist(tmp_path, js: str, co_index: bool = True) -> Path:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True, exist_ok=True)
    if co_index:
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    if js:
        (dist / "assets" / "index-abc.js").write_text(js, encoding="utf-8")
    return dist


def test_ban_build_dung_duoc_chap_nhan_du_con_dia_chi_mac_dinh_localhost(tmp_path):
    """Bundle LUÔN còn `http://localhost:8001/api/v1` (tham số mặc định không dùng tới).

    Không được coi đó là lỗi - nếu không thì không build nào qua được kiểm tra.
    """
    js = 'const so="http://localhost:8001/api/v1";function f(e=so){};const su="/api/v1";'
    assert deploy.check_dist(_dist(tmp_path, js)) == []


def test_chan_ban_build_bi_git_bash_doi_dia_chi_api(tmp_path):
    js = 'const so="http://localhost:8001/api/v1";const su="D:/Git/api/v1";'
    van_de = deploy.check_dist(_dist(tmp_path, js))
    assert any("Windows" in v and "D:/Git/api/v1" in v for v in van_de)
    assert any("tuong doi" in v for v in van_de)  # cũng không còn địa chỉ tương đối đúng


def test_chan_ban_build_quen_dat_bien_moi_truong(tmp_path):
    van_de = deploy.check_dist(_dist(tmp_path, 'const so="http://localhost:8001/api/v1";'))
    assert any("tuong doi" in v for v in van_de)


def test_chan_ban_build_thieu_file(tmp_path):
    # Hai thư mục riêng: `_dist` tạo `dist/` nên gọi hai lần trên cùng một chỗ sẽ trùng.
    thieu_index = _dist(tmp_path / "a", 'a="/api/v1"', co_index=False)
    thieu_js = _dist(tmp_path / "b", "")
    assert any("index.html" in v for v in deploy.check_dist(thieu_index))
    assert any("JS" in v for v in deploy.check_dist(thieu_js))


# --- Kiểm tra site thật ---------------------------------------------------------------------


def _gia_fetch(monkeypatch, tra_loi):
    """`tra_loi` ánh xạ phần đường dẫn sau `https://x.test/` sang kết quả (hoặc lỗi)."""

    def fake(url, timeout=20):
        ket_qua = tra_loi[url.removeprefix("https://x.test/")]
        if isinstance(ket_qua, Exception):
            raise ket_qua
        return ket_qua

    monkeypatch.setattr(deploy, "fetch", fake)


def test_verify_public_ok(monkeypatch):
    _gia_fetch(
        monkeypatch,
        {
            "": (200, "text/html; charset=utf-8", "<html>"),
            "api/v1/health": (200, "application/json", '{"data":{"status":"ok"}}'),
        },
    )
    assert deploy.verify_public("https://x.test") == []


def test_verify_public_bao_loi_khi_trang_chu_va_health_hong(monkeypatch):
    _gia_fetch(
        monkeypatch,
        {
            "": (502, "text/html", ""),
            "api/v1/health": (200, "application/json", '{"data":{"status":"degraded"}}'),
        },
    )
    van_de = deploy.verify_public("https://x.test")
    assert len(van_de) == 2


def test_verify_public_khong_no_khi_mat_ket_noi(monkeypatch):
    loi = urllib.error.URLError("khong ket noi")
    _gia_fetch(monkeypatch, {"": loi, "api/v1/health": loi})
    assert len(deploy.verify_public("https://x.test")) == 2


def test_verify_public_chiu_duoc_health_khong_phai_json(monkeypatch):
    _gia_fetch(
        monkeypatch,
        {"": (200, "text/html", ""), "api/v1/health": (200, "text/html", "<html>")},
    )
    assert len(deploy.verify_public("https://x.test")) == 1


# --- Kế hoạch và chương trình chính ---------------------------------------------------------


def test_ke_hoach_cac_che_do():
    plan = deploy.plan_steps
    assert plan("status", False) == ["status"]
    assert plan("frontend", False) == ["frontend"]  # frontend không đụng tài khoản
    assert plan("backend", False) == ["backup", "backend"]
    assert plan("data", False) == ["backup", "data"]
    assert plan("all", False) == ["backup", "backend", "frontend"]
    assert plan("all", True) == ["backend", "frontend"]
    assert plan("backup", False) == ["backup"]


@pytest.fixture
def cam_chay_lenh(monkeypatch):
    """Mọi lần gọi tiến trình con đều làm test đỏ."""

    def cam(*args, **kwargs):
        raise AssertionError(f"khong duoc chay lenh that: {args}")

    monkeypatch.setattr(deploy.subprocess, "run", cam)
    monkeypatch.setattr(deploy, "git_warnings", lambda mode: [])
    monkeypatch.delenv("MOODBITE_DEPLOY_HOST", raising=False)


def test_thieu_host_thi_tu_choi_va_khong_chay_gi(cam_chay_lenh, capsys):
    assert deploy.main(["status"]) == 1
    assert "MOODBITE_DEPLOY_HOST" in capsys.readouterr().out


def test_host_lay_tu_bien_moi_truong(cam_chay_lenh, monkeypatch, capsys):
    monkeypatch.setenv("MOODBITE_DEPLOY_HOST", HOST)
    assert deploy.main(["status", "--dry-run"]) == 0
    assert HOST in capsys.readouterr().out


def test_rollback_tu_choi_ma_commit_la(cam_chay_lenh, capsys):
    assert deploy.main(["rollback", "main; reboot", "--host", HOST, "--dry-run"]) == 1
    assert deploy.main(["rollback", "--host", HOST, "--dry-run"]) == 1
    assert "commit" in capsys.readouterr().out


def test_dry_run_all_in_lenh_nhung_khong_chay_gi(cam_chay_lenh, capsys):
    assert deploy.main(["all", "--host", HOST, "--dry-run"]) == 0
    ra = capsys.readouterr().out
    for mong_doi in ("ssh", "scp", "npm run build", "git pull --ff-only", "/var/www/moodbite"):
        assert mong_doi in ra
    assert "DRY-RUN" in ra


def test_dry_run_frontend_khong_sao_luu_tai_khoan(cam_chay_lenh, capsys):
    assert deploy.main(["frontend", "--host", HOST, "--dry-run"]) == 0
    assert "SAO LUU" not in capsys.readouterr().out


def test_dry_run_rollback_in_dung_ma_commit(cam_chay_lenh, capsys):
    assert deploy.main(["rollback", "207f86a", "--host", HOST, "--dry-run"]) == 0
    assert "git checkout -q 207f86a" in capsys.readouterr().out


def test_dung_o_buoc_loi_va_khong_chay_buoc_sau(cam_chay_lenh, monkeypatch, capsys):
    """Sao lưu hỏng thì KHÔNG được đi tiếp sang `git pull`."""
    daydu = []
    monkeypatch.setattr(deploy, "step_backup", lambda host, dry: False)
    monkeypatch.setattr(deploy, "step_backend", lambda *a: daydu.append("backend") or True)
    assert deploy.main(["backend", "--host", HOST, "--yes"]) == 1
    assert daydu == []
