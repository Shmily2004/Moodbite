"""Vẽ biểu đồ UML thành file SVG theo đúng ký hiệu của giáo trình (hình 2.15, 2.16a).

    python docs/bieu_do_uml/ve_bieu_do.py

Đọc đặc tả trong `sinh_bieu_do.py` (DAC_TA) và sinh ra:
  svg/hoat_dong/UCxx_*.svg   — biểu đồ hoạt động, làn bơi Khách / Hệ thống
  svg/trinh_tu/UCxx_*.svg    — biểu đồ trình tự, ký hiệu actor / boundary / control / entity
  svg/01_use_case.svg        — biểu đồ use case
  index.html                 — mở để xem tất cả, dùng trình duyệt

Ký hiệu trình tự (theo ảnh mẫu):
  actor     : hình người
  boundary  : vòng tròn có vạch đứng bên trái, nối bằng gạch ngang
  control   : vòng tròn có mũi tên ở đầu
  entity    : vòng tròn có gạch ngang phía dưới
  lời gọi   : mũi tên đặc; trả về: nét đứt, mũi tên hở
  alt / opt : khung có nhãn ở góc trên trái, đường đứt ngăn các nhánh

Ký hiệu hoạt động: start = chấm đen; end = vòng tròn có chấm; hành động = hình chữ nhật
bo góc; rẽ nhánh = hình thoi; fork/join = thanh đen dày.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sinh_bieu_do as dac_ta  # noqa: E402

GOC = Path(__file__).resolve().parent
THU_MUC_SVG = GOC / "svg"
FONT = "Arial, Helvetica, sans-serif"
NET = "#000"


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _cat_chu(s: str, n: int) -> list[str]:
    """Ngắt dòng theo số ký tự tối đa, ưu tiên ngắt ở khoảng trắng."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= n:
            cur = f"{cur} {w}" if cur else w
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


class SVG:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.p: list[str] = []

    def add(self, s: str) -> None:
        self.p.append(s)

    def line(self, x1, y1, x2, y2, dash=False, arrow=None, sw=1.2) -> None:
        d = ' stroke-dasharray="6 4"' if dash else ""
        m = ' marker-end="url(#%s)"' % arrow if arrow else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{NET}" stroke-width="{sw}"{d}{m}/>')

    def path(self, d: str, dash=False, arrow=None, fill="none", sw=1.2) -> None:
        da = ' stroke-dasharray="6 4"' if dash else ""
        m = ' marker-end="url(#%s)"' % arrow if arrow else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{NET}" stroke-width="{sw}"{da}{m}/>')

    def text(self, x, y, s, size=13, anchor="start", weight="normal", italic=False) -> None:
        it = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
                 f'text-anchor="{anchor}" font-weight="{weight}" fill="#000"{it}>{_esc(s)}</text>')

    def multitext(self, x, y, lines, size=13, anchor="middle", lh=16) -> None:
        for i, t in enumerate(lines):
            self.text(x, y + i * lh, t, size=size, anchor=anchor)

    def rect(self, x, y, w, h, rx=0, fill="#fff", dash=False, sw=1.2) -> None:
        da = ' stroke-dasharray="6 4"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                 f'stroke="{NET}" stroke-width="{sw}"{da}/>')

    def circle(self, cx, cy, r, fill="#fff", sw=1.2) -> None:
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{NET}" stroke-width="{sw}"/>')

    def out(self) -> str:
        defs = (
            '<defs>'
            '<marker id="dac" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">'
            '<path d="M0,0 L10,5 L0,10 z" fill="#000"/></marker>'
            '<marker id="ho" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="11" markerHeight="11" orient="auto">'
            '<path d="M1,1 L11,6 L1,11" fill="none" stroke="#000" stroke-width="1.2"/></marker>'
            '</defs>'
        )
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">{defs}'
                f'<rect width="100%" height="100%" fill="#fff"/>' + "\n".join(self.p) + "</svg>\n")


# ---------------------------------------------------------------------------
# TRÌNH TỰ
# ---------------------------------------------------------------------------
TEN_THAM_GIA = {
    "KH": ("actor", None), "QT": ("actor", None),
    "UI": ("boundary", None), "CTRL": ("control", None),
    "DB": ("entity", None), "TK": ("entity", None), "NK": ("entity", None),
}


def _thu_thap_nguoi(buoc: list, dung: set[str]) -> None:
    for b in buoc:
        if b[0] in ("msg", "ret"):
            dung.update([b[1], b[2]])
        elif b[0] == "alt":
            _thu_thap_nguoi(b[2], dung)
            _thu_thap_nguoi(b[3], dung)
        elif b[0] == "opt":
            _thu_thap_nguoi(b[2], dung)


def _ve_actor(s: SVG, x: float, y: float) -> None:
    s.circle(x, y - 40, 9)
    s.line(x, y - 31, x, y - 4)
    s.line(x - 14, y - 20, x + 14, y - 20)
    s.line(x, y - 4, x - 11, y + 10)
    s.line(x, y - 4, x + 11, y + 10)


def _ve_boundary(s: SVG, x: float, y: float) -> None:
    # vạch đứng bên trái, nối với vòng tròn bằng gạch ngang
    s.line(x - 24, y - 16, x - 24, y + 16)
    s.line(x - 24, y, x - 16, y)
    s.circle(x, y, 16)


def _ve_control(s: SVG, x: float, y: float) -> None:
    s.circle(x, y, 16)
    # mũi tên ở đầu vòng tròn, chỉ lên-phải
    s.path(f"M {x - 6} {y - 17} L {x + 2} {y - 22} L {x + 3} {y - 16} Z", fill="#000")


def _ve_entity(s: SVG, x: float, y: float) -> None:
    s.circle(x, y, 16)
    s.line(x - 13, y + 9, x + 13, y + 9)


def _ve_nhan_tham_gia(s: SVG, kieu: str, x: float, y: float) -> None:
    {"actor": _ve_actor, "boundary": _ve_boundary, "control": _ve_control,
     "entity": _ve_entity}[kieu](s, x, y)


def ve_trinh_tu(uc: dict) -> str:
    la_qt = uc["nhom"] == "Quản trị"
    ma_nguoi = "QT" if la_qt else "KH"
    ten_nguoi = dac_ta.QT_TEN if la_qt else dac_ta.KH_TEN
    ui = dac_ta.UI_QT if la_qt else dac_ta.UI_KH
    ctrl = dac_ta.CTRL_QT if la_qt else dac_ta.CTRL_KH
    ten_db = dac_ta.DB
    dung: set[str] = set()
    _thu_thap_nguoi(uc["trinh_tu"], dung)

    # thứ tự cột: tác nhân, giao diện, xử lý, dữ liệu, rồi các bảng dữ liệu phụ
    cot = [ma_nguoi, "UI", "CTRL", "DB"] + [k for k in ("TK", "NK") if k in dung]
    ten = {
        ma_nguoi: (ten_nguoi, "actor"), "UI": (ui, "boundary"), "CTRL": (ctrl, "control"),
        "DB": (ten_db, "entity"), "TK": ("Ent_TaiKhoan", "entity"), "NK": ("Ent_NhatKy", "entity"),
    }
    SP = 250
    LE = 110
    W = LE * 2 + SP * (len(cot) - 1)
    x_cot = {k: LE + i * SP for i, k in enumerate(cot)}

    # Ước lượng chiều cao: mỗi bước một dòng, khung/ghi chú thêm chút
    def dem(buoc: list) -> int:
        n = 0
        for b in buoc:
            if b[0] in ("msg", "ret", "note"):
                n += 1
            elif b[0] == "alt":
                n += 2 + dem(b[2]) + dem(b[3])
            elif b[0] == "opt":
                n += 2 + dem(b[2])
        return n

    TOP_Y = 150
    H = TOP_Y + dem(uc["trinh_tu"]) * 40 + 120
    s = SVG(int(W), int(H))

    # tiêu đề
    s.text(20, 26, f"{uc['ma']} — {uc['ten']}", size=15, weight="bold")
    s.text(20, 46, f"API: {uc['api']}", size=11, italic=True)

    # tên và ký hiệu tham gia (đầu cột)
    for k in cot:
        x = x_cot[k]
        kieu = ten[k][1]
        _ve_nhan_tham_gia(s, kieu, x, 100)
        s.text(x, 138, ten[k][0], size=12, anchor="middle")

    y_bat_dau = TOP_Y
    cuoi_y = [y_bat_dau]

    def lifeline_all(ytop: float, ybot: float) -> None:
        for k in cot:
            s.line(x_cot[k], ytop, x_cot[k], ybot, dash=True)

    y = [y_bat_dau]
    dang_kich: dict[str, float] = {}
    kich_hoat: list[tuple[float, float, float]] = []

    def ve_buoc(buoc: list, ind: float = 0) -> None:
        for b in buoc:
            loai = b[0]
            if loai in ("msg", "ret"):
                if b[1] not in x_cot or b[2] not in x_cot:
                    continue
                xa, xb = x_cot[b[1]], x_cot[b[2]]
                yy = y[0] + 26
                nhan = b[3]
                if b[1] == b[2]:
                    # tự gọi: vòng nhỏ bên phải
                    s.path(f"M {xa} {yy} H {xa + 34} V {yy + 18} H {xa + 2}", arrow="dac" if loai == "msg" else None,
                           dash=(loai == "ret"))
                    s.text(xa + 40, yy + 4, nhan, size=12)
                    y[0] += 42
                    continue
                if xb > xa:
                    xs, xe = xa + 2, xb - 2
                else:
                    xs, xe = xa - 2, xb + 2
                s.line(xs, yy, xe, yy, dash=(loai == "ret"), arrow="dac" if loai == "msg" else "ho")
                # thanh kích hoạt: bắt đầu khi nhận lời gọi, kết thúc khi trả về
                if loai == "msg" and b[2] not in (ma_nguoi,) and b[2] not in dang_kich:
                    dang_kich[b[2]] = yy
                if loai == "ret" and b[1] in dang_kich:
                    kich_hoat.append((x_cot[b[1]], dang_kich.pop(b[1]), yy + 6))
                tx = min(xa, xb) + 8
                s.text(tx, yy - 8, nhan, size=12)
                y[0] += 36
            elif loai == "note":
                x = x_cot["CTRL"]
                w = len(b[1]) * 6.4 + 16
                yy = y[0] + 2
                s.rect(x + 14, yy, w, 24, fill="#fff")
                s.text(x + 22, yy + 16, b[1], size=11)
                y[0] += 38
            elif loai == "alt":
                y0 = y[0]
                y[0] += 26  # chừa chỗ cho nhãn alt và điều kiện
                ve_buoc(b[2])
                y_mid = y[0] + 6
                s.line(x_cot[cot[0]] - 40, y_mid, x_cot[cot[-1]] + 40, y_mid, dash=True)
                s.text(x_cot[cot[0]] - 30, y_mid + 16, "[khác]", size=11)
                y[0] = y_mid + 24
                ve_buoc(b[3])
                y_end = y[0] + 8
                s.rect(x_cot[cot[0]] - 40, y0, x_cot[cot[-1]] - x_cot[cot[0]] + 80, y_end - y0, fill="none")
                s.add(f'<rect x="{x_cot[cot[0]] - 40}" y="{y0}" width="44" height="18" fill="#fff" stroke="#000" stroke-width="1.2"/>')
                s.text(x_cot[cot[0]] - 36, y0 + 13, "alt", size=11, weight="bold")
                s.text(x_cot[cot[0]] + 14, y0 + 14, f"[{b[1]}]", size=11)
                y[0] = y_end + 12
            elif loai == "opt":
                y0 = y[0]
                y[0] += 14
                ve_buoc(b[2])
                y_end = y[0] + 8
                s.rect(x_cot[cot[0]] - 40, y0, x_cot[cot[-1]] - x_cot[cot[0]] + 80, y_end - y0, fill="none")
                s.add(f'<rect x="{x_cot[cot[0]] - 40}" y="{y0}" width="44" height="18" fill="#fff" stroke="#000" stroke-width="1.2"/>')
                s.text(x_cot[cot[0]] - 36, y0 + 13, "opt", size=11, weight="bold")
                y[0] = y_end + 12

    vi_tri_duong_doi = len(s.p)  # chèn đường đời vào đây, để thông điệp và ghi chú nằm trên
    ve_buoc(uc["trinh_tu"])
    y_cuoi = y[0] + 20
    for k, y0 in dang_kich.items():
        kich_hoat.append((x_cot[k], y0, y_cuoi - 10))
    duong_doi = SVG(1, 1)
    for k in cot:
        duong_doi.line(x_cot[k], 138, x_cot[k], y_cuoi, dash=True)
    for xa, y0, y1 in kich_hoat:
        duong_doi.rect(xa - 6, y0, 12, y1 - y0, fill="#fff")
    s.p[vi_tri_duong_doi:vi_tri_duong_doi] = duong_doi.p
    s.h = int(y_cuoi + 40)
    return s.out()


# ---------------------------------------------------------------------------
# HOẠT ĐỘNG (làn bơi)
# ---------------------------------------------------------------------------
LANE_W = 520
LANE_HEAD = 34
BOX_W = 160
BOX_H = 50
GAP = 44
OFF = 170  # khoảng lệch của nhánh "không": đủ để không đè lên nhánh "có"


def _ten_lan(lane_name: str) -> str:
    return "Khách hàng" if lane_name == dac_ta.KH_TEN else lane_name


def ve_hoat_dong(uc: dict) -> str:
    # Thu thập các làn theo thứ tự xuất hiện
    lanes: list[str] = []

    def quet(buoc: list) -> None:
        for b in buoc:
            if b[0] == "lane" and b[1] not in lanes:
                lanes.append(b[1])
            elif b[0] == "if":
                quet(b[2])
                quet(b[3])
            elif b[0] == "fork":
                for n in b[1]:
                    quet(n)

    quet(uc["hoat_dong"])
    if not lanes:
        lanes = ["Hệ thống"]
    if len(lanes) == 1:
        lanes = [lanes[0]]
    n_lanes = len(lanes)
    x_lan = {nm: 40 + i * LANE_W + LANE_W // 2 for i, nm in enumerate(lanes)}
    W = 40 + n_lanes * LANE_W + 40
    s = SVG(W, 900)  # chiều cao sẽ chỉnh sau

    s.text(20, 22, f"{uc['ma']} — {uc['ten']}", size=15, weight="bold")
    s.text(20, 40, f"API: {uc['api']}", size=11, italic=True)
    top = 60
    # nền làn và tên làn
    for i, nm in enumerate(lanes):
        x0 = 40 + i * LANE_W
        s.rect(x0, top, LANE_W, 1, fill="#fff")  # placeholder (chiều cao chỉnh dưới)
    body_top = top + LANE_HEAD

    # trạng thái bố trí
    st = {"y": body_top + 80, "lane": lanes[0], "tails": [], "start": None}
    nodes: list[dict] = []
    edges: list[tuple] = []

    def them_nut(kind: str, x: float, y: float, text: str = "", lane: str = "", w: int = BOX_W, h: int = BOX_H) -> dict:
        nd = {"kind": kind, "x": x, "y": y, "text": text, "lane": lane, "w": w, "h": h}
        nodes.append(nd)
        return nd

    def noi(a: dict, b: dict, nhan: str = "") -> None:
        edges.append((a, b, nhan))

    def cao_nut(nd: dict) -> float:
        return nd["h"]

    def dinh(nd: dict) -> tuple[float, float]:
        return nd["x"], nd["y"] - nd["h"] / 2

    def day(nd: dict) -> tuple[float, float]:
        return nd["x"], nd["y"] + nd["h"] / 2

    def chain(items: list, lane: str, x_off: float, y: float, tails: list) -> tuple[list, float]:
        """Xếp chuỗi bước; trả về (các đuôi cần nối tiếp, y kế tiếp)."""
        cur_lane = lane
        for it in items:
            loai = it[0]
            if loai == "lane":
                cur_lane = it[1]
                continue
            x = x_lan.get(cur_lane, x_lan[lanes[0]]) + x_off
            if loai == "act":
                nd = them_nut("act", x, y, it[1], cur_lane)
                for t_nd, t_nhan in tails:
                    noi(t_nd, nd, t_nhan)
                tails = [(nd, "")]
                y += BOX_H + GAP
            elif loai == "stop":
                nd = them_nut("end", x, y, "", cur_lane, w=22, h=22)
                for t_nd, t_nhan in tails:
                    noi(t_nd, nd, t_nhan)
                tails = []
                y += 40
            elif loai == "if":
                d = them_nut("dec", x, y, it[1], cur_lane, w=170, h=70)
                for t_nd, t_nhan in tails:
                    noi(t_nd, d, t_nhan)
                y_nhanh = y + 92
                tails_co, y_co = chain(it[2], cur_lane, x_off, y_nhanh, [(d, "có")])
                tails_khong, y_khong = chain(it[3], cur_lane, x_off + OFF, y_nhanh, [(d, "không")])
                tails = tails_co + tails_khong
                y = max(y_co, y_khong) + 6
            elif loai == "fork":
                rong_thanh = 2 * (OFF / 2) + BOX_W + 24
                bar = them_nut("bar", x, y, "", cur_lane, w=rong_thanh, h=7)
                for t_nd, t_nhan in tails:
                    noi(t_nd, bar, t_nhan)
                y_nhanh = y + 56
                nhanh_tails: list = []
                y_max = y_nhanh
                for j, nhanh in enumerate(it[1]):
                    dx = (-OFF / 2) if j == 0 else (OFF / 2)
                    t_j, y_j = chain(nhanh, cur_lane, x_off + dx, y_nhanh, [(bar, "")])
                    nhanh_tails += t_j
                    y_max = max(y_max, y_j)
                join = them_nut("bar", x, y_max + 8, "", cur_lane, w=rong_thanh, h=7)
                for t_nd, t_nhan in nhanh_tails:
                    noi(t_nd, join, t_nhan)
                tails = [(join, "")]
                y = y_max + 8 + BOX_H + 30  # chừa chỗ để hành động kế tiếp không đè lên thanh join
        return tails, y

    # Điểm bắt đầu
    start = them_nut("start", x_lan[lanes[0]], st["y"] - 52, "", lanes[0], w=22, h=22)
    tails, y_end = chain(uc["hoat_dong"], lanes[0], 0, st["y"], [(start, "")])

    # Chiều cao làn
    ymax = max([nd["y"] + nd["h"] / 2 for nd in nodes] + [y_end]) + 40
    s.h = int(ymax + 60)
    # Vẽ lại nền làn với chiều cao thật
    s.p = [p for p in s.p if not p.startswith('<rect x="40"') and not p.startswith('<rect x="460"')]
    for i, nm in enumerate(lanes):
        x0 = 40 + i * LANE_W
        s.rect(x0, top, LANE_W, ymax - top, fill="#fff")
        s.rect(x0, top, LANE_W, LANE_HEAD, fill="#fff")
        s.text(x0 + LANE_W / 2, top + 22, _ten_lan(nm), size=13, anchor="middle", weight="bold")

    # Vẽ mũi tên trước, nút vẽ sau để nút che đầu đường
    for a, b, nhan in edges:
        _ve_noi(s, a, b, nhan)
    for nd in nodes:
        _ve_nut(s, nd)
    return s.out()


def _ve_noi(s: SVG, a: dict, b: dict, nhan: str) -> None:
    if a["kind"] == "dec" and nhan == "không":
        # nhánh "không" đi từ góc phải của hình thoi, rẽ ngang rồi xuống hành động
        x1, y1 = a["x"] + a["w"] / 2, a["y"]
        x2, y2 = b["x"], b["y"] - b["h"] / 2
        s.path(f"M {x1} {y1} H {x2} V {y2}", arrow="dac")
        s.text(x1 + 6, y1 - 6, nhan, size=11)
        return
    if a["kind"] == "bar":
        x1, y1 = a["x"], a["y"] + a["h"] / 2
    elif a["kind"] == "dec":
        x1, y1 = a["x"], a["y"] + a["h"] / 2
    elif a["kind"] in ("start", "end"):
        x1, y1 = a["x"], a["y"] + a["h"] / 2
    else:
        x1, y1 = a["x"], a["y"] + a["h"] / 2
    if b["kind"] in ("bar", "end", "start"):
        x2, y2 = b["x"], b["y"] - b["h"] / 2
    else:
        x2, y2 = b["x"], b["y"] - b["h"] / 2
    if abs(x1 - x2) < 1:
        s.line(x1, y1, x2, y2, arrow="dac")
    else:
        my = (y1 + y2) / 2
        s.path(f"M {x1} {y1} V {my} H {x2} V {y2}", arrow="dac")
    if nhan:
        s.text((x1 + x2) / 2 + 6 if abs(x1 - x2) >= 1 else x1 + 8, (y1 + y2) / 2 - 4, nhan, size=11)


def _ve_nut(s: SVG, nd: dict) -> None:
    x, y, w, h = nd["x"], nd["y"], nd["w"], nd["h"]
    k = nd["kind"]
    if k == "start":
        s.circle(x, y, 10, fill="#000")
    elif k == "end":
        s.circle(x, y, 11, fill="#fff")
        s.circle(x, y, 6, fill="#000")
    elif k == "bar":
        s.rect(x - w / 2, y - h / 2, w, h, fill="#000")
    elif k == "dec":
        s.path(f"M {x} {y - h / 2} L {x + w / 2} {y} L {x} {y + h / 2} L {x - w / 2} {y} Z", fill="#fff")
        lines = _cat_chu(nd["text"], 20)
        for i, t in enumerate(lines):
            s.text(x, y - (len(lines) - 1) * 7 + i * 14 + 4, t, size=11, anchor="middle")
    else:  # hành động
        s.rect(x - w / 2, y - h / 2, w, h, rx=12, fill="#fff")
        lines = _cat_chu(nd["text"], 22)
        lh = 15
        y0 = y - (len(lines) - 1) * lh / 2 + 5
        for i, t in enumerate(lines):
            s.text(x, y0 + i * lh, t, size=12, anchor="middle")


# ---------------------------------------------------------------------------
# USE CASE
# ---------------------------------------------------------------------------
NHOM_UC = [
    ("Khám phá quán và món", ["UC01", "UC02", "UC03", "UC04", "UC05", "UC06", "UC07", "UC14"], "left"),
    ("Tài khoản", ["UC08", "UC09", "UC10", "UC11", "UC12", "UC13", "UC15"], "left"),
    ("Đăng nhập và tổng quan", ["UC16", "UC17"], "right"),
    ("Quản lý dữ liệu", ["UC18", "UC19", "UC20", "UC21", "UC22"], "right"),
    ("Nội dung và nhật ký", ["UC23", "UC24"], "right"),
]
# Quan hệ: (từ, đến, loại). include: từ gọi đến. extend: từ là phần mở rộng, mũi tên về đến.
QUAN_HE = [
    ("UC03", "UC04", "include"),
    ("UC03", "UC02", "extend"),
    ("UC06", "UC05", "extend"),
    ("UC07", "UC05", "extend"),
    ("UC10", "UC09", "extend"),
    ("UC22", "UC20", "extend"),
    ("UC11", "UC09", "include"),
    ("UC12", "UC09", "include"),
    ("UC13", "UC09", "include"),
    ("UC18", "UC16", "include"),
    ("UC19", "UC16", "include"),
    ("UC20", "UC16", "include"),
    ("UC21", "UC16", "include"),
    ("UC23", "UC16", "include"),
    ("UC24", "UC16", "include"),
]
KHACH_NOI = ["UC01", "UC02", "UC03", "UC04", "UC05", "UC06", "UC07", "UC08", "UC09", "UC10", "UC11", "UC12", "UC13", "UC14", "UC15"]
# UC04 chỉ được gọi bởi UC03 (include), không có đường nối trực tiếp từ khách
KHACH_KHONG_NOI = {"UC04"}
QT_NOI = ["UC16", "UC17", "UC18", "UC19", "UC20", "UC21", "UC22", "UC23", "UC24"]


def ve_use_case() -> str:
    """Bố cục: use case gốc ở cột giữa; use case mở rộng/được gọi ở hai bên để mũi tên
    ngang hoặc dọc, tránh cắt nhau. Tọa độ đặt tay, sửa trong bảng VI_TRI bên dưới."""
    ten_uc = {uc["ma"]: uc["ten"] for uc in dac_ta.DAC_TA}
    W, H = 1480, 960
    s = SVG(W, H)
    s.text(20, 26, "Biểu đồ use case — MoodBite", size=15, weight="bold")
    s.rect(220, 44, 650, 880, fill="#fff")
    s.text(545, 66, "Hệ thống MoodBite — phía người dùng", size=14, anchor="middle", weight="bold")
    s.rect(900, 44, 540, 560, fill="#fff")
    s.text(1170, 66, "Hệ thống MoodBite — quản trị", size=14, anchor="middle", weight="bold")

    VI_TRI = {
        # Người dùng — cột giữa: use case gốc
        "UC01": (560, 130), "UC02": (560, 220), "UC03": (560, 310), "UC04": (560, 400),
        "UC05": (560, 490), "UC14": (560, 580), "UC09": (560, 670), "UC15": (560, 760),
        "UC08": (560, 850),
        # cột trái: use case mở rộng
        "UC06": (330, 490), "UC07": (330, 580), "UC10": (330, 670),
        # cột phải: use case được đăng nhập gọi
        "UC11": (790, 610), "UC12": (790, 670), "UC13": (790, 730),
        # Quản trị — cột giữa: đăng nhập là gốc
        "UC16": (1190, 130), "UC17": (1190, 580), "UC22": (1190, 410),
        "UC18": (1000, 230), "UC19": (1000, 320), "UC20": (1000, 410),
        "UC21": (1000, 500), "UC23": (1000, 590), "UC24": (1000, 680),
    }
    ELW, ELH = 190, 52
    pos = VI_TRI

    def ellipse(ma: str) -> None:
        cx, cy = pos[ma]
        s.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{ELW / 2}" ry="{ELH / 2}" fill="#fff" stroke="#000" stroke-width="1.2"/>')
        lines = _cat_chu(f"{ma} {ten_uc[ma]}", 26)
        y0 = cy - (len(lines) - 1) * 7 + 4
        for i, t in enumerate(lines):
            s.text(cx, y0 + i * 14, t, size=11, anchor="middle")

    def mep(ma: str, toward: tuple[float, float]) -> tuple[float, float]:
        """Điểm trên mép elip của `ma` theo hướng về `toward`."""
        import math
        cx, cy = pos[ma]
        dx, dy = toward[0] - cx, toward[1] - cy
        if dx == 0 and dy == 0:
            return cx, cy
        t = 1 / math.sqrt((dx / (ELW / 2)) ** 2 + (dy / (ELH / 2)) ** 2)
        return cx + dx * t, cy + dy * t

    for a, b, loai in QUAN_HE:
        pa, pb = pos[a], pos[b]
        x1, y1 = mep(a, pb)
        x2, y2 = mep(b, pa)
        s.line(x1, y1, x2, y2, dash=True, arrow="dac")
        # nhãn đặt ở điểm giữa, lệch lên một chút để không đè lên đường
        s.text((x1 + x2) / 2 + 4, (y1 + y2) / 2 - 6, f"«{loai}»", size=10, anchor="middle")

    KH_X, KH_Y = 90, 470
    QT_X, QT_Y = 1420, 400
    for ma in KHACH_NOI:
        if ma in KHACH_KHONG_NOI:
            continue
        x2, y2 = mep(ma, (KH_X, KH_Y))
        s.line(KH_X + 14, KH_Y, x2, y2, sw=1)
    for ma in QT_NOI:
        x2, y2 = mep(ma, (QT_X, QT_Y))
        s.line(QT_X - 14, QT_Y, x2, y2, sw=1)
    for ma in pos:
        ellipse(ma)
    _ve_actor(s, KH_X, KH_Y)
    s.text(KH_X, KH_Y + 30, "Khách", size=12, anchor="middle")
    _ve_actor(s, QT_X, QT_Y)
    s.text(QT_X, QT_Y + 30, "Quản trị viên", size=12, anchor="middle")
    return s.out()


# ---------------------------------------------------------------------------
# USE CASE THEO NHÓM LỚN
# ---------------------------------------------------------------------------
NHOM_LON = [
    ("UC_nhom1_kham_pha", "Nhóm 1 — Khám phá quán và món", "Khách",
     ["UC01", "UC02", "UC03", "UC04", "UC05", "UC06", "UC07", "UC14"]),
    ("UC_nhom2_tai_khoan", "Nhóm 2 — Tài khoản người dùng", "Khách",
     ["UC08", "UC09", "UC10", "UC11", "UC12", "UC13", "UC15"]),
    ("UC_nhom3_quan_tri_dang_nhap", "Nhóm 3 — Đăng nhập và tổng quan (quản trị)", "Quản trị viên",
     ["UC16", "UC17"]),
    ("UC_nhom4_quan_ly_du_lieu", "Nhóm 4 — Quản lý dữ liệu (quản trị)", "Quản trị viên",
     ["UC18", "UC19", "UC20", "UC21", "UC22"]),
    ("UC_nhom5_noi_dung_nhat_ky", "Nhóm 5 — Nội dung và nhật ký (quản trị)", "Quản trị viên",
     ["UC23", "UC24"]),
]


def ve_use_case_nhom(tieu_de: str, ids: list[str], tac_nhan: str) -> str:
    """Biểu đồ use case cho một nhóm. Gồm các use case trong nhóm và use case gốc
    mà nhóm đó được include/extend tới, để mũi tên luôn có đích."""
    ten_uc = {uc["ma"]: uc["ten"] for uc in dac_ta.DAC_TA}
    thanh_vien = list(ids)
    quan_he = []
    for a, b, loai in QUAN_HE:
        if a in ids or b in ids:
            quan_he.append((a, b, loai))
            for x in (a, b):
                if x not in thanh_vien:
                    thanh_vien.append(x)
    # Đích của quan hệ (use case gốc) nằm cột phải, phần còn lại cột trái
    dich = {b for _, b, _ in quan_he}
    trai = [x for x in thanh_vien if x not in dich]
    phai = [x for x in thanh_vien if x in dich]
    ELW, ELH = 220, 56
    n = max(len(trai), len(phai), 1)
    H = max(420, 150 + n * 110)
    W = 1000
    s = SVG(W, H)
    s.text(20, 26, tieu_de, size=15, weight="bold")
    BX, BW = 230, 700
    s.rect(BX, 44, BW, H - 80, fill="#fff")
    s.text(BX + BW / 2, 66, "Hệ thống MoodBite", size=14, anchor="middle", weight="bold")
    pos: dict[str, tuple[float, float]] = {}
    for i, ma in enumerate(trai):
        pos[ma] = (BX + 170, 120 + i * 110 + (n - len(trai)) * 55)
    for i, ma in enumerate(phai):
        pos[ma] = (BX + BW - 170, 120 + i * 110 + (n - len(phai)) * 55)

    import math

    def mep(ma: str, toward: tuple[float, float]) -> tuple[float, float]:
        cx, cy = pos[ma]
        dx, dy = toward[0] - cx, toward[1] - cy
        if dx == 0 and dy == 0:
            return cx, cy
        t = 1 / math.sqrt((dx / (ELW / 2)) ** 2 + (dy / (ELH / 2)) ** 2)
        return cx + dx * t, cy + dy * t

    KX, KY = 90, H / 2 - 30
    for a, b, loai in quan_he:
        x1, y1 = mep(a, pos[b])
        x2, y2 = mep(b, pos[a])
        s.line(x1, y1, x2, y2, dash=True, arrow="dac")
        s.text((x1 + x2) / 2, (y1 + y2) / 2 - 6, f"«{loai}»", size=10, anchor="middle")
    for ma in thanh_vien:
        if ma == "UC04" and "UC03" in ids:
            pass
        if ma in KHACH_KHONG_NOI and tac_nhan == "Khách":
            continue
        if tac_nhan == "Khách" and ma not in KHACH_NOI:
            continue
        if tac_nhan != "Khách" and ma not in QT_NOI:
            continue
        x2, y2 = mep(ma, (KX, KY))
        s.line(KX + 14, KY, x2, y2, sw=1)
    for ma in thanh_vien:
        cx, cy = pos[ma]
        s.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{ELW / 2}" ry="{ELH / 2}" fill="#fff" stroke="#000" stroke-width="1.2"/>')
        lines = _cat_chu(f"{ma} {ten_uc[ma]}", 28)
        y0 = cy - (len(lines) - 1) * 7 + 4
        for i, t in enumerate(lines):
            s.text(cx, y0 + i * 14, t, size=12, anchor="middle")
    _ve_actor(s, KX, KY)
    s.text(KX, KY + 30, tac_nhan, size=12, anchor="middle")
    return s.out()


# ---------------------------------------------------------------------------
# CHẠY
# ---------------------------------------------------------------------------
def main() -> None:
    (THU_MUC_SVG / "hoat_dong").mkdir(parents=True, exist_ok=True)
    (THU_MUC_SVG / "trinh_tu").mkdir(parents=True, exist_ok=True)
    cac_muc = []
    for uc in dac_ta.DAC_TA:
        ten = f"{uc['ma']}_{dac_ta._ten_an_toan(uc['ten'])}"
        f1 = THU_MUC_SVG / "hoat_dong" / f"{ten}.svg"
        f2 = THU_MUC_SVG / "trinh_tu" / f"{ten}.svg"
        f1.write_text(ve_hoat_dong(uc), encoding="utf-8")
        f2.write_text(ve_trinh_tu(uc), encoding="utf-8")
        cac_muc.append((uc, f1, f2))
    (THU_MUC_SVG / "00_use_case_tong_quat.svg").write_text(ve_use_case(), encoding="utf-8")
    cac_nhom = []
    for ten_file, tieu_de, tac_nhan, ids in NHOM_LON:
        f = THU_MUC_SVG / f"{ten_file}.svg"
        f.write_text(ve_use_case_nhom(tieu_de, ids, tac_nhan), encoding="utf-8")
        cac_nhom.append((tieu_de, f))
    _viet_index(cac_muc, cac_nhom)
    print(f"Đã vẽ {len(cac_muc)} use case x 2 biểu đồ và 1 biểu đồ use case vào {THU_MUC_SVG}")


def _viet_index(cac_muc, cac_nhom) -> None:
    dong = []
    for uc, f1, f2 in cac_muc:
        dong.append(f"<section><h2>{_esc(uc['ma'])} — {_esc(uc['ten'])}</h2>"
                    f"<div class=\"hang\"><figure><figcaption>Hoạt động</figcaption>"
                    f"<img src=\"svg/hoat_dong/{f1.name}\"></figure>"
                    f"<figure><figcaption>Trình tự</figcaption>"
                    f"<img src=\"svg/trinh_tu/{f2.name}\"></figure></div></section>")
    html_text = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>Biểu đồ UML — MoodBite</title>
<style>
 body {{ font-family: Arial, sans-serif; margin: 20px; background:#f6f6f6; }}
 h1 {{ font-size: 20px; }} h2 {{ font-size: 16px; margin: 24px 0 8px; }}
 .hang {{ display:flex; gap:20px; flex-wrap:wrap; align-items:flex-start; }}
 figure {{ margin:0; background:#fff; border:1px solid #ccc; padding:8px; overflow:auto; max-width:100%; }}
 figcaption {{ font-size:12px; color:#555; margin-bottom:4px; }}
 img {{ max-width: none; }}
</style></head><body>
<h1>Biểu đồ UML — MoodBite</h1>
<h2>Biểu đồ use case tổng quát</h2>
<p><img src="svg/00_use_case_tong_quat.svg" style="max-width:100%;border:1px solid #ccc;background:#fff"></p>
<h2>Biểu đồ use case theo nhóm lớn</h2>
{''.join(f'<p><img src="svg/{f.name}" style="max-width:100%;border:1px solid #ccc;background:#fff"></p>' for _, f in cac_nhom)}
{''.join(dong)}
</body></html>
"""
    (GOC / "index.html").write_text(html_text, encoding="utf-8")


if __name__ == "__main__":
    main()
