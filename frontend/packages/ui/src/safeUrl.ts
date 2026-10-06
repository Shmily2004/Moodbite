/**
 * Chỉ cho phép link `http:` / `https:` đi vào `href`.
 *
 * VÌ SAO: `menu_url`, `website`, `google_maps_url`, `source_url`… đến từ dữ liệu CÀO
 * (Apify, OSM, nhập tay). React 18 chỉ CẢNH BÁO chứ không chặn `href="javascript:…"`,
 * nên một bản ghi bẩn là đủ để chạy mã tuỳ ý khi người dùng bấm vào link.
 *
 * Trả `null` khi không an toàn → nơi gọi KHÔNG render link (không phải render link rỗng).
 * Dùng `new URL()` thay cho regex: trình duyệt tự bỏ khoảng trắng/ký tự điều khiển ở đầu
 * và không phân biệt hoa thường scheme (`  JaVaScRiPt:`), regex tự viết dễ lọt.
 */
export function safeHttpUrl(raw: string | null | undefined): string | null {
  if (typeof raw !== 'string') return null;
  const trimmed = raw.trim();
  if (!trimmed) return null;
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    // Đường dẫn tương đối / chuỗi rác: dữ liệu ngoài không bao giờ hợp lệ ở dạng đó.
    return null;
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return null;
  return parsed.href;
}

/**
 * Chỉ cho phép đích chuyển hướng là ĐƯỜNG DẪN NỘI BỘ (`/abc`), dùng cho `state.from` sau
 * khi đăng nhập.
 *
 * VÌ SAO: react-router v6 dính GHSA-wrjc-x8rr-h8h6 (open redirect qua dấu `\`) và KHÔNG có
 * bản vá cho v6 (chỉ vá từ 7.18.0, audit 2026-10-06). Trình duyệt hiểu `/\evil.com` và
 * `//evil.com` là sang tên miền khác. Chặn ngay tại chỗ đọc `from`: phải bắt đầu bằng
 * ĐÚNG MỘT `/`, không có `\` hay ký tự điều khiển ở bất kỳ đâu. Không hợp lệ → `null`,
 * nơi gọi dùng đích mặc định.
 */
export function safeInternalPath(raw: unknown): string | null {
  if (typeof raw !== 'string' || raw === '') return null;
  if (!raw.startsWith('/')) return null;
  if (raw.startsWith('//')) return null;
  for (const ch of raw) {
    const ma = ch.charCodeAt(0);
    if (ch === '\\' || ma < 0x20 || ma === 0x7f) return null;
  }
  return raw;
}
