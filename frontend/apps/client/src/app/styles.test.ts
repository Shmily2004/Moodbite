/**
 * Kiểm tra BIẾN CSS — mọi `var(--x)` phải có chỗ khai báo `--x`.
 *
 * VÌ SAO CÓ FILE NÀY — lỗi thật, chủ dự án phát hiện 2026-08-26:
 * Bong bóng trợ lý viết `background: var(--nen-the, #fff)` và `color: var(--ink)`.
 * `--nen-the` KHÔNG TỒN TẠI trong dự án (tên đúng là `--surface`), nên trình duyệt dùng
 * fallback `#fff` — trắng CỨNG, không đổi theo giao diện. Còn `--ink` thì có thật và ở
 * chế độ TỐI nó là màu SÁNG. Kết quả: chữ trắng trên nền trắng, không đọc được gì.
 *
 * Điều tệ nhất là CSS **không báo lỗi** khi dùng biến không tồn tại — nó lặng lẽ lấy
 * fallback. Không build nào đỏ, không test nào đỏ; chỉ người nhìn màn hình mới thấy.
 * Vì vậy phải có test.
 *
 * Cùng lượt rà đó tìm ra 5 biến bịa: `--nen-the`, `--nen-phu`, `--vien`, `--ok`, `--danger`.
 */
import { describe, expect, it } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const THU_MUC_APP = join(__dirname);
const THU_MUC_STYLES = join(__dirname, 'styles');

/**
 * Biến được gán ĐỘNG từ JSX qua `style={{ '--x': ... }}` chứ không khai trong CSS.
 * Chúng đều có fallback trong `var()` nên an toàn — xem `AvatarPicker`, `StatTiles`.
 */
const DAT_DONG_TU_JS = new Set(['--avatar-h', '--tile-h']);

function docHetCss(): string {
  const files = [
    join(THU_MUC_APP, 'styles.css'),
    ...readdirSync(THU_MUC_STYLES)
      .filter((f) => f.endsWith('.css'))
      .map((f) => join(THU_MUC_STYLES, f)),
  ];
  return files.map((f) => readFileSync(f, 'utf-8')).join('\n');
}

describe('biến CSS', () => {
  it('mọi var(--x) đều có chỗ khai báo --x', () => {
    const css = docHetCss();

    const khaiBao = new Set(Array.from(css.matchAll(/^\s*(--[a-z0-9-]+)\s*:/gm), (m) => m[1]));
    const dangDung = new Set(Array.from(css.matchAll(/var\(\s*(--[a-z0-9-]+)/g), (m) => m[1]));

    const thieu = [...dangDung].filter((b) => !khaiBao.has(b) && !DAT_DONG_TU_JS.has(b));

    expect(thieu, `Biến chưa khai báo: ${thieu.join(', ')}`).toEqual([]);
  });

  it('không dùng lại những tên biến đã bịa ra hồi 2026-08-26', () => {
    // Chặn đích danh: đây là những cái tên nghe hợp lý nên rất dễ gõ lại theo phản xạ.
    const css = docHetCss();
    const daBia = ['--nen-the', '--nen-phu', '--vien', '--ok', '--danger'];

    for (const ten of daBia) {
      expect(css.includes(`var(${ten}`), `Đã bịa lại biến ${ten}`).toBe(false);
    }
  });
});
