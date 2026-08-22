"""Chuẩn bị ảnh thiết kế cho frontend — chạy lại được mỗi khi có bản xuất mới.

    python scripts/prepare_design_assets.py

VÌ SAO CẦN SCRIPT CHỨ KHÔNG CHÉP TAY:

1. Chép tay thì lần sau xuất lại ảnh mới, không ai nhớ phải xử lý những gì.
2. `slogan.png` xuất ra KHÔNG CÓ KÊNH TRONG SUỐT — nó là ảnh chụp phẳng, có sẵn cả
   caro xám của nền "trong suốt" trong công cụ thiết kế (đo được: các ô 243 và 254).
   Đặt thẳng lên nền kem thì hiện nguyên bàn cờ. Script này tách nền trắng/caro ra
   thành trong suốt rồi cắt sát chữ.
3. Đo được luôn: ảnh nền có phần "giấy" màu TRẮNG TINH (255,255,255) trong khi trang
   màu kem #FCF4EA. Đó chính là chỗ trông "rời rạc" mà chủ dự án nhận xét. Phần này
   KHÔNG sửa bằng script mà sửa bằng CSS `mix-blend-mode: multiply` — nhân với nền kem
   thì trắng thành đúng màu kem, mép cắt biến mất. Script chỉ in ra cảnh báo.

Thuần Python: chỉ dùng `zlib` + `struct` của thư viện chuẩn. Không cần Pillow — máy chủ
dự án không cài Pillow, và thêm một phụ thuộc 5MB cho việc này là không đáng.
"""
from __future__ import annotations

import shutil
import struct
import sys
import zlib
from pathlib import Path

# Console của Windows có thể đang ở bảng mã cp1252/cp437 — in tiếng Việt vào đó sẽ ném
# UnicodeEncodeError và giết cả script dù công việc đã xong. Ép UTF-8 ngay từ đầu.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
NGUON = ROOT / "frontend" / "design" / "attribute"
DICH = ROOT / "frontend" / "apps" / "client" / "public" / "anh"

# Ảnh chép nguyên trạng: đã có kênh trong suốt đúng, cũng không cần thu nhỏ vì chúng
# trải kín màn hình.
CHEP_NGUYEN = {
    "Background-login.png": "nen-dang-nhap.png",
    "Register background.png": "nen-dang-ky.png",
    "banner home.png": "banner-trang-chu.png",
}

# Ảnh cần XỬ LÝ trước khi dùng: {tên nguồn: (tên đích, tách nền?, bề ngang tối đa)}.
#
# Bề ngang tối đa đặt bằng ~3 lần cỡ hiển thị thật, đủ nét cho màn hình 2x–3x mà không
# bắt người dùng tải về một tấm ảnh mấy megabyte cho một cái logo.
XU_LY = {
    # Logo hiển thị rộng ~310px trên máy tính. Bản gốc 2172px là quá dư.
    "logo.png": ("logo.png", False, 930),
    # Khẩu hiệu hiển thị rộng ~545px.
    "slogan.png": ("slogan.png", True, 1120),
    # Mascot ở dải mời đăng ký, hiển thị rộng ~120px.
    "mascot.png": ("mascot.png", False, 420),
    # Favicon: 180px là cỡ `apple-touch-icon` yêu cầu; trình duyệt tự thu xuống 32px cho
    # tab. Một file dùng cho cả hai chỗ, đỡ phải sinh 4 kích thước như thời xưa.
    "favicon.png": ("favicon.png", False, 180),
}

# Ngưỡng tách nền, chọn theo số đo thật của `slogan.png`:
#   - ô caro sáng nhất 254, tối nhất 242  -> phải coi mọi mức >= 238 là nền
#   - nét chữ navy đậm nhất ~ 20          -> từ 180 trở xuống là mực đặc
# Khoảng 180..238 là viền khử răng cưa, cho mờ dần theo độ sáng.
NEN_TU = 238
MUC_DEN = 180
# Điểm có chênh lệch kênh màu lớn hơn mức này thì chắc chắn là MỰC (chữ cam), không phải
# nền xám. Nếu không, chữ cam sáng sẽ bị tách nhầm thành trong suốt.
NGUONG_MAU = 14


def tim_file(ten: str) -> Path | None:
    """Tìm file trong thư mục nguồn, KHÔNG phân biệt hoa/thường.

    Chủ dự án vừa đổi `Logo.png` thành `logo.png` (2026-08-22). Windows coi hai tên đó là
    một nên không ai thấy gì; Linux (máy chạy CI) thì coi là hai file khác nhau và script
    sẽ lặng lẽ bỏ qua. Đây đúng kiểu lỗi chỉ nổ trên CI — chặn ngay từ đầu.
    """
    thang = NGUON / ten
    if thang.exists():
        return thang
    thuong = ten.lower()
    for f in NGUON.iterdir():
        if f.name.lower() == thuong:
            return f
    return None


def doc_png(duong_dan: Path) -> tuple[int, int, int, list[bytearray]]:
    """Giải mã PNG thành các hàng pixel. Trả (rộng, cao, số kênh, hàng)."""
    raw = duong_dan.read_bytes()
    pos, idat = 8, b""
    rong = cao = kenh = 0
    while pos < len(raw):
        do_dai = struct.unpack(">I", raw[pos : pos + 4])[0]
        loai = raw[pos + 4 : pos + 8]
        if loai == b"IHDR":
            rong, cao, sau, kieu_mau = struct.unpack(">IIBB", raw[pos + 8 : pos + 18])
            if sau != 8:
                raise SystemExit(f"{duong_dan.name}: chỉ hỗ trợ ảnh 8 bit/kênh.")
            kenh = {0: 1, 2: 3, 4: 2, 6: 4}[kieu_mau]
        elif loai == b"IDAT":
            idat += raw[pos + 8 : pos + 8 + do_dai]
        pos += 12 + do_dai

    data = zlib.decompress(idat)
    buoc = rong * kenh
    truoc = bytearray(buoc)
    hang: list[bytearray] = []
    i = 0
    for _ in range(cao):
        bo_loc = data[i]
        i += 1
        dong = bytearray(data[i : i + buoc])
        i += buoc
        # Bỏ bộ lọc PNG (mục 9 của đặc tả). Viết thẳng ở đây vì không dùng thư viện ngoài.
        for x in range(buoc):
            a = dong[x - kenh] if x >= kenh else 0
            b = truoc[x]
            c = truoc[x - kenh] if x >= kenh else 0
            if bo_loc == 1:
                dong[x] = (dong[x] + a) & 255
            elif bo_loc == 2:
                dong[x] = (dong[x] + b) & 255
            elif bo_loc == 3:
                dong[x] = (dong[x] + (a + b) // 2) & 255
            elif bo_loc == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                gan = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                dong[x] = (dong[x] + gan) & 255
        hang.append(dong)
        truoc = dong
    return rong, cao, kenh, hang


def ghi_png_rgba(duong_dan: Path, rong: int, cao: int, diem: bytearray) -> None:
    """Ghi ảnh RGBA. Dùng bộ lọc 0 (không lọc) cho đơn giản và dễ đọc lại."""
    tho = bytearray()
    buoc = rong * 4
    for y in range(cao):
        tho.append(0)
        tho += diem[y * buoc : (y + 1) * buoc]

    def chunk(loai: bytes, noi_dung: bytes) -> bytes:
        return (
            struct.pack(">I", len(noi_dung))
            + loai
            + noi_dung
            + struct.pack(">I", zlib.crc32(loai + noi_dung) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", rong, cao, 8, 6, 0, 0, 0)
    duong_dan.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(tho), 9))
        + chunk(b"IEND", b"")
    )


def tach_nen_trang(rong: int, cao: int, kenh: int, hang: list[bytearray]):
    """Biến nền trắng/caro thành trong suốt, rồi cắt sát phần còn lại.

    Trả (rộng_mới, cao_mới, dữ liệu RGBA).
    """
    diem = bytearray(rong * cao * 4)
    for y in range(cao):
        dong = hang[y]
        for x in range(rong):
            g = x * kenh
            r, luc, lam = dong[g], dong[g + 1], dong[g + 2]
            sang = (r + luc + lam) // 3
            chenh = max(r, luc, lam) - min(r, luc, lam)

            if chenh > NGUONG_MAU or sang <= MUC_DEN:
                alpha = 255  # mực đặc (navy hoặc cam)
            elif sang >= NEN_TU:
                alpha = 0  # nền / ô caro
            else:
                # Viền khử răng cưa: mờ dần theo độ sáng.
                alpha = int((NEN_TU - sang) * 255 / (NEN_TU - MUC_DEN))

            d = (y * rong + x) * 4
            diem[d] = r
            diem[d + 1] = luc
            diem[d + 2] = lam
            diem[d + 3] = alpha

    # Cắt sát: bỏ hết lề trong suốt. Lề thừa làm CSS phải căn chỉnh bằng số ma thuật.
    trai, tren, phai, duoi = rong, cao, -1, -1
    for y in range(cao):
        for x in range(rong):
            if diem[(y * rong + x) * 4 + 3] > 8:
                trai = min(trai, x)
                phai = max(phai, x)
                tren = min(tren, y)
                duoi = max(duoi, y)
    if phai < 0:
        raise SystemExit("Ảnh rỗng sau khi tách nền — kiểm lại ngưỡng.")

    rong_moi, cao_moi = phai - trai + 1, duoi - tren + 1
    cat = bytearray(rong_moi * cao_moi * 4)
    for y in range(cao_moi):
        nguon = ((y + tren) * rong + trai) * 4
        cat[y * rong_moi * 4 : (y + 1) * rong_moi * 4] = diem[
            nguon : nguon + rong_moi * 4
        ]
    return rong_moi, cao_moi, cat


def sang_rgba(rong: int, cao: int, kenh: int, hang: list[bytearray]) -> tuple[int, int, bytearray]:
    """Đưa ảnh về dạng RGBA phẳng, giữ nguyên mọi thứ. Dùng cho ảnh đã trong suốt sẵn."""
    diem = bytearray(rong * cao * 4)
    for y in range(cao):
        dong = hang[y]
        for x in range(rong):
            g = x * kenh
            d = (y * rong + x) * 4
            diem[d] = dong[g]
            diem[d + 1] = dong[g + 1] if kenh >= 3 else dong[g]
            diem[d + 2] = dong[g + 2] if kenh >= 3 else dong[g]
            diem[d + 3] = dong[g + 3] if kenh == 4 else 255
    return rong, cao, diem


# Bề ngang tối đa của ảnh chữ sau khi xử lý. Chữ hiển thị rộng khoảng 560px trên máy
# tính, nên 1120px là vừa đủ nét cho màn hình 2x (Retina / 150% scaling của Windows).
# Giữ nguyên 1454px chỉ để file nặng gấp đôi mà mắt thường không thấy khác.
BE_NGANG_TOI_DA = 1120


def thu_nho(rong: int, cao: int, diem: bytearray, rong_moi: int):
    """Thu nhỏ ảnh RGBA bằng cách LẤY TRUNG BÌNH cả ô — không phải lấy mẫu điểm.

    Lấy mẫu điểm (nearest) làm nét chữ rỗ như răng cưa. Trung bình theo diện tích cho
    kết quả mượt, đúng thứ mắt mong đợi ở một dòng tiêu đề.

    Nhân alpha vào màu trước khi trộn (premultiply) rồi chia ra sau: nếu không, điểm
    trong suốt (màu rác) sẽ kéo màu của điểm đặc bên cạnh nhạt đi, tạo viền sáng quanh chữ.
    """
    if rong_moi >= rong:
        return rong, cao, diem
    ty_le = rong / rong_moi
    cao_moi = max(1, round(cao / ty_le))
    ra = bytearray(rong_moi * cao_moi * 4)
    for y in range(cao_moi):
        y0, y1 = int(y * ty_le), max(int(y * ty_le) + 1, int((y + 1) * ty_le))
        y1 = min(y1, cao)
        for x in range(rong_moi):
            x0, x1 = int(x * ty_le), max(int(x * ty_le) + 1, int((x + 1) * ty_le))
            x1 = min(x1, rong)
            tr = tg = tb = ta = 0
            n = 0
            for yy in range(y0, y1):
                nen = (yy * rong) * 4
                for xx in range(x0, x1):
                    d = nen + xx * 4
                    a = diem[d + 3]
                    tr += diem[d] * a
                    tg += diem[d + 1] * a
                    tb += diem[d + 2] * a
                    ta += a
                    n += 1
            d = (y * rong_moi + x) * 4
            if ta:
                ra[d] = min(255, tr // ta)
                ra[d + 1] = min(255, tg // ta)
                ra[d + 2] = min(255, tb // ta)
            ra[d + 3] = ta // n if n else 0
    return rong_moi, cao_moi, ra


def kiem_giay_trang(ten: str, rong: int, cao: int, kenh: int, hang: list[bytearray]) -> None:
    """Cảnh báo nếu ảnh có vùng TRẮNG TINH — nó sẽ chỏi với nền kem của trang."""
    if kenh != 4:
        return
    trang = 0
    tong = 0
    for y in range(0, cao, 7):
        dong = hang[y]
        for x in range(0, rong, 7):
            g = x * kenh
            if dong[g + 3] > 250:
                tong += 1
                if dong[g] > 250 and dong[g + 1] > 250 and dong[g + 2] > 250:
                    trang += 1
    if tong and trang * 100 // tong >= 5:
        print(
            f"    ⚠ {trang * 100 // tong}% vùng đặc là TRẮNG TINH. Trang màu kem nên chỗ "
            "này sẽ lộ mảng trắng nếu đặt thẳng lên."
        )
        print(
            "      Cách xử lý đã dùng: CSS `mix-blend-mode: multiply` ở `.auth__scene` "
            "(app/styles/auth.css) — nhân với nền kem thì trắng thành đúng màu kem."
        )


def main() -> int:
    if not NGUON.is_dir():
        print(f"Không thấy thư mục {NGUON}")
        return 1
    DICH.mkdir(parents=True, exist_ok=True)

    print("CHUẨN BỊ ẢNH THIẾT KẾ")
    print(f"  nguồn: {NGUON}")
    print(f"  đích : {DICH}\n")

    for ten_nguon, ten_dich in CHEP_NGUYEN.items():
        f = tim_file(ten_nguon)
        if f is None:
            print(f"  [BỎ QUA] {ten_nguon} — không có file")
            continue
        rong, cao, kenh, hang = doc_png(f)
        shutil.copyfile(f, DICH / ten_dich)
        print(f"  [CHÉP]  {ten_nguon} -> {ten_dich}  ({rong}×{cao}, {kenh} kênh)")
        if kenh != 4:
            print("    ⚠ Ảnh KHÔNG có kênh trong suốt. Xuất lại dạng PNG-32 sẽ đẹp hơn.")
        kiem_giay_trang(ten_dich, rong, cao, kenh, hang)

    for ten_nguon, (ten_dich, tach_nen, be_ngang) in XU_LY.items():
        f = tim_file(ten_nguon)
        if f is None:
            print(f"  [BỎ QUA] {ten_nguon} — không có file")
            continue
        rong, cao, kenh, hang = doc_png(f)
        if tach_nen:
            r2, c2, diem = tach_nen_trang(rong, cao, kenh, hang)
        else:
            r2, c2, diem = sang_rgba(rong, cao, kenh, hang)
        r2, c2, diem = thu_nho(r2, c2, diem, be_ngang)
        # `favicon.png` phải nằm ở GỐC `public/` (trình duyệt tìm `/favicon.png`),
        # còn lại nằm trong `public/anh/`.
        dich = (DICH.parent / ten_dich) if ten_dich == "favicon.png" else (DICH / ten_dich)
        ghi_png_rgba(dich, r2, c2, diem)
        kb_truoc = f.stat().st_size // 1024
        kb_sau = dich.stat().st_size // 1024
        viec = "TÁCH NỀN" if tach_nen else "THU NHỎ"
        print(
            f"  [{viec}] {f.name} -> {ten_dich}  "
            f"{rong}×{cao} ({kb_truoc} KB) -> {r2}×{c2} ({kb_sau} KB)"
        )
        print(f"    -> khai ở images.ts: width: {r2}, height: {c2}")

    print("\nXong. Kích thước ảnh khai ở frontend/apps/client/src/shared/config/images.ts")
    print("— sửa file ảnh mà đổi kích thước thì nhớ sửa cả số ở đó.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
