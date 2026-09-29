"""Chụp màn hình giao diện bằng TRÌNH DUYỆT THẬT, và đo xem trang có TRÀN NGANG không.

    python scripts/chup_man_hinh.py http://localhost:5173/
    python scripts/chup_man_hinh.py http://localhost:5173/recommend --rong 420 --mobile
    python scripts/chup_man_hinh.py http://localhost:5173/ --ra runs/anh/trang-chu.png

Chạy giống nhau ở PowerShell, CMD, bash - không phải nhớ cú pháp shell (CLAUDE.md mục 1).

VÌ SAO CẦN FILE NÀY
-------------------
Dự án đã nhiều lần gặp lỗi giao diện mà TEST KHÔNG BẮT ĐƯỢC, vì jsdom không tính bố cục:
cột lọc tràn khung và thanh trượt bán kính lòi ra ngoài (2026-09-16). Cách duy nhất thấy
được là mở trình duyệt thật.

⚠️ VÀ ĐÂY LÀ CÁI BẪY (đã mắc ngày 2026-09-23): dùng

    msedge --headless --screenshot=a.png --window-size=420,900

cho ra ảnh TRÔNG NHƯ tràn ngang - chữ và thẻ bị cắt ở mép phải. Đó là **ảo giác của công
cụ**, không phải lỗi giao diện: `--window-size` không đặt viewport bố cục giống một chiếc
điện thoại thật. Đặt lại bằng `Emulation.setDeviceMetricsOverride` thì
`document.scrollWidth` đúng bằng bề rộng màn hình - tức là KHÔNG hề tràn.

Suýt nữa thì có người đi "sửa" một lỗi không tồn tại. Nên script này luôn IN RA số đo
`scrollWidth` bên cạnh ảnh: **ảnh để nhìn, số để kết luận**.

KHÔNG THÊM PHỤ THUỘC
--------------------
`requirements.txt` đã cố ý rút từ 15 xuống 7 gói. Thêm playwright/selenium chỉ để chụp
ảnh là đi ngược lại việc đó, nên WebSocket ở đây tự viết bằng thư viện chuẩn - vừa đủ để
nói chuyện với DevTools Protocol, không hơn.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent

CDP_PORT = 9222
# Hồ sơ RIÊNG: dùng chung hồ sơ thật thì Edge đang mở sẵn sẽ không chịu bật cổng gỡ lỗi.
PROFILE_DIR = Path(os.environ.get("TEMP", "/tmp")) / "moodbite-edge-chup"

EDGE_PATHS = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/microsoft-edge",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)


def tim_edge() -> str:
    for p in EDGE_PATHS:
        if Path(p).exists():
            return p
    raise SystemExit(
        "Khong tim thay Microsoft Edge. Sua EDGE_PATHS trong scripts/chup_man_hinh.py."
    )


# --- WebSocket tối giản (đủ để nói chuyện với CDP) ---------------------------


class WebSocket:
    """Client WebSocket chỉ làm đúng việc cần: gửi text, nhận text.

    Không TLS, không nén, không chia mảnh khi GỬI - CDP chạy ở localhost và lệnh gửi đi
    đều ngắn. Chiều NHẬN thì phải ghép mảnh thật, vì ảnh chụp mã base64 rất dài.
    """

    def __init__(self, url: str) -> None:
        if not url.startswith("ws://"):
            raise SystemExit(f"Chi ho tro ws://, nhan duoc: {url}")
        hostport, _, path = url[len("ws://"):].partition("/")
        host, _, port = hostport.partition(":")
        self.sock = socket.create_connection((host, int(port or 80)))
        self.sock.settimeout(90)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall(
            (
                f"GET /{path} HTTP/1.1\r\n"
                f"Host: {hostport}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        self._buf = b""
        while b"\r\n\r\n" not in self._buf:
            self._buf += self._doc(1)
        head, _, self._buf = self._buf.partition(b"\r\n\r\n")
        if b"101" not in head.split(b"\r\n")[0]:
            raise SystemExit(f"Bat tay WebSocket that bai: {head[:120]!r}")

    def _doc(self, n: int) -> bytes:
        data = self.sock.recv(max(n, 65536))
        if not data:
            raise SystemExit("Trinh duyet dong ket noi giua chung.")
        return data

    def _lay(self, n: int) -> bytes:
        while len(self._buf) < n:
            self._buf += self._doc(n - len(self._buf))
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def gui(self, text: str) -> None:
        payload = text.encode()
        n = len(payload)
        if n < 126:
            head = struct.pack("!BB", 0x81, 0x80 | n)
        elif n < 65536:
            head = struct.pack("!BBH", 0x81, 0x80 | 126, n)
        else:
            head = struct.pack("!BBQ", 0x81, 0x80 | 127, n)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(head + mask + masked)

    def nhan(self) -> str:
        """Một THÔNG ĐIỆP hoàn chỉnh, đã ghép đủ các mảnh."""
        manh: List[bytes] = []
        while True:
            b1, b2 = struct.unpack("!BB", self._lay(2))
            fin, opcode = b1 & 0x80, b1 & 0x0F
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack("!H", self._lay(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self._lay(8))[0]
            payload = self._lay(n)  # máy chủ không mask
            if opcode == 0x8:
                raise SystemExit("Trinh duyet gui frame dong ket noi.")
            if opcode == 0x9:  # ping -> pong, không trả lời thì bị cắt kết nối
                self.sock.sendall(struct.pack("!BB", 0x8A, 0x80) + os.urandom(4))
                continue
            manh.append(payload)
            if fin:
                return b"".join(manh).decode()


class Cdp:
    def __init__(self, ws_url: str) -> None:
        self.ws = WebSocket(ws_url)
        self._id = 0

    def goi(self, method: str, **params: Any) -> Dict:
        self._id += 1
        self.ws.gui(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.nhan())
            # Bỏ qua event (gói không có "id") - ở đây chỉ hỏi-đáp.
            if m.get("id") == self._id:
                if "error" in m:
                    raise SystemExit(f"CDP loi o {method}: {m['error']}")
                return m.get("result", {})


# --- điều khiển trình duyệt ---------------------------------------------------


def mo_edge() -> subprocess.Popen:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [
            tim_edge(),
            "--headless=new",
            "--disable-gpu",
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={PROFILE_DIR}",
            "--no-first-run",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=1)
            return proc
        except Exception:
            time.sleep(0.5)
    proc.terminate()
    raise SystemExit("Edge khong mo duoc cong go loi sau 30 giay.")


def trang_dau_tien() -> str:
    raw = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list", timeout=5).read()
    for t in json.loads(raw):
        if t.get("type") == "page":
            return t["webSocketDebuggerUrl"]
    raise SystemExit("Khong thay tab nao trong Edge.")


# Đo bề rộng THẬT. `scrollWidth` lớn hơn `clientWidth` nghĩa là có thứ gì đó thò ra ngoài
# và người dùng phải cuộn ngang - gần như luôn là lỗi bố cục.
JS_DO_TRAN = r"""(() => {
  const vw = document.documentElement.clientWidth;
  const out = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.right <= vw + 1) continue;
    const p = el.parentElement;
    const pr = p && p.getBoundingClientRect();
    if (pr && pr.right > vw + 1) continue;   // cha cũng tràn -> không phải nguồn gốc
    // Nằm trong khối CUỘN NGANG CÓ CHỦ ĐÍCH (dải thẻ món ở trang chủ) thì không phải lỗi.
    let t = el, trongDaiCuon = false;
    while (t && t !== document.body) {
      const ox = getComputedStyle(t).overflowX;
      if (ox === 'auto' || ox === 'scroll') { trongDaiCuon = true; break; }
      t = t.parentElement;
    }
    if (trongDaiCuon) continue;
    out.push({
      tag: el.tagName.toLowerCase(),
      cls: String(el.getAttribute('class') || '').slice(0, 70),
      right: Math.round(r.right),
      w: Math.round(r.width),
    });
  }
  return JSON.stringify({
    vw: vw,
    scrollW: document.documentElement.scrollWidth,
    nguon: out.slice(0, 15),
  });
})()"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Chup man hinh + do tran ngang.")
    ap.add_argument("url", help="Dia chi can chup, VD http://localhost:5173/")
    ap.add_argument("--rong", type=int, default=1440, help="Be rong viewport (px)")
    ap.add_argument("--cao", type=int, default=900, help="Chieu cao viewport (px)")
    ap.add_argument("--mobile", action="store_true", help="Gia lap dien thoai that")
    ap.add_argument("--ra", default=None, help="Duong dan file PNG")
    ap.add_argument("--doi", type=float, default=6.0, help="So giay cho trang tai xong")
    args = ap.parse_args()

    ra = Path(args.ra) if args.ra else ROOT / "runs" / "anh" / f"chup-{args.rong}px.png"
    ra.parent.mkdir(parents=True, exist_ok=True)

    proc = mo_edge()
    try:
        cdp = Cdp(trang_dau_tien())
        cdp.goi(
            "Emulation.setDeviceMetricsOverride",
            width=args.rong,
            height=args.cao,
            deviceScaleFactor=2 if args.mobile else 1,
            mobile=args.mobile,
        )
        cdp.goi("Page.enable")
        cdp.goi("Page.navigate", url=args.url)
        time.sleep(args.doi)

        kq = cdp.goi("Runtime.evaluate", expression=JS_DO_TRAN, returnByValue=True)
        do = json.loads(kq["result"]["value"])

        anh = cdp.goi("Page.captureScreenshot", format="png", captureBeyondViewport=True)
        ra.write_bytes(base64.b64decode(anh["data"]))

        print(f"URL       : {args.url}")
        print(f"Viewport  : {do['vw']}px" + (" (mobile)" if args.mobile else ""))
        print(f"Anh       : {ra}")
        print(f"scrollWidth = {do['scrollW']}", end="  ")
        if do["scrollW"] <= do["vw"] + 1:
            print("-> KHONG tran ngang. OK.")
            return 0
        print(f"-> TRAN {do['scrollW'] - do['vw']}px. Phan tu gay tran:")
        for o in do["nguon"]:
            print(f"   <{o['tag']} class={o['cls']!r}>  right={o['right']} w={o['w']}")
        return 1
    finally:
        proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
