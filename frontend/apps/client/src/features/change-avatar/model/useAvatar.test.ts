/**
 * Test BẢO MẬT của phần tải ảnh đại diện.
 *
 * Đây là chỗ nhận FILE TỪ NGƯỜI LẠ rồi hiển thị lại — đường vào kinh điển của XSS lưu
 * trữ. Mỗi test dưới đây là một cách tấn công thật, không phải tình huống giả tưởng:
 *
 *   - đổi đuôi file HTML thành .png       -> phải chặn ở bước đọc số ma thuật
 *   - tải lên SVG có <script>             -> phải chặn ngay ở bước lọc kiểu
 *   - file khổng lồ (bom nén)             -> phải chặn trước khi giải mã
 *   - dữ liệu lạ nhét thẳng vào localStorage -> phải KHÔNG được đem đi hiển thị
 */
import { describe, expect, it, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AnhKhongHopLe, useAvatar } from './useAvatar';

/** File giả với nội dung byte tuỳ ý — đúng cách trình duyệt đưa file vào `<input>`. */
function taoFile(ten: string, kieu: string, byte: number[]): File {
  return new File([new Uint8Array(byte)], ten, { type: kieu });
}

const PNG_THAT = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 0];
const HTML = Array.from('<script>alert(1)</script>').map((c) => c.charCodeAt(0));

beforeEach(() => {
  localStorage.clear();
});

describe('useAvatar - chan file doc hai', () => {
  it('TU CHOI file HTML doi duoi thanh .png', async () => {
    const { result } = renderHook(() => useAvatar());
    // Kẻ tấn công đặt tên `avatar.png` và khai `type: image/png`; chỉ RUỘT file mới nói
    // thật. Đây là lý do phải đọc số ma thuật chứ không tin `file.type`.
    const doc_hai = taoFile('avatar.png', 'image/png', HTML);

    await expect(result.current.doiAvatar(doc_hai)).rejects.toBeInstanceOf(AnhKhongHopLe);
    expect(localStorage.getItem('moodbite.avatar')).toBeNull();
  });

  it('TU CHOI file SVG du no cung la "anh"', async () => {
    const { result } = renderHook(() => useAvatar());
    // SVG là XML, chạy được <script> bên trong -> không bao giờ nhận, dù trình duyệt coi
    // nó là ảnh hợp lệ.
    const svg = taoFile('avatar.svg', 'image/svg+xml', HTML);

    await expect(result.current.doiAvatar(svg)).rejects.toBeInstanceOf(AnhKhongHopLe);
  });

  it('TU CHOI file qua lon truoc khi giai ma (chong bom nen)', async () => {
    const { result } = renderHook(() => useAvatar());
    const qua_lon = new File([new Uint8Array(3 * 1024 * 1024)], 'to.png', {
      type: 'image/png',
    });

    await expect(result.current.doiAvatar(qua_lon)).rejects.toThrow(/2 MB/);
  });

  it('TU CHOI kieu file la (vd PDF)', async () => {
    const { result } = renderHook(() => useAvatar());
    const pdf = taoFile('cv.pdf', 'application/pdf', [0x25, 0x50, 0x44, 0x46]);

    await expect(result.current.doiAvatar(pdf)).rejects.toBeInstanceOf(AnhKhongHopLe);
  });

  it('KHONG doc du lieu la trong localStorage', async () => {
    // Người dùng (hoặc mã lạ) nhét chuỗi khác vào localStorage. Nếu ta tin và đem gắn vào
    // <img src>, `javascript:` hay `data:text/html` sẽ chạy được.
    localStorage.setItem('moodbite.avatar', 'javascript:alert(1)');

    const { result } = renderHook(() => useAvatar());

    await waitFor(() => {
      // Chỉ nhận data URL PNG do chính ta sinh ra.
      expect(result.current.avatar).toBeNull();
    });
  });

  it('NHAN anh PNG that va luu lai dang data URL do canvas ve lai', async () => {
    // jsdom không có bộ giải mã ảnh thật, nên giả lập `Image` + `canvas`: phần đang test ở
    // đây là LUỒNG XỬ LÝ (kiểm -> vẽ lại -> lưu), không phải khả năng giải mã của trình duyệt.
    class FakeImage {
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      width = 512;
      height = 512;
      set src(_v: string) {
        setTimeout(() => this.onload?.(), 0);
      }
    }
    vi.stubGlobal('Image', FakeImage);
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: () => 'blob:gia-lap',
      revokeObjectURL: () => undefined,
    });
    const toDataURL = vi.fn(() => 'data:image/png;base64,VE_LAI');
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      if (tag !== 'canvas') return document.createElementNS('http://www.w3.org/1999/xhtml', tag) as HTMLElement;
      return { width: 0, height: 0, getContext: () => ({ drawImage: vi.fn() }), toDataURL } as unknown as HTMLElement;
    });

    const { result } = renderHook(() => useAvatar());
    const png = taoFile('toi.png', 'image/png', PNG_THAT);

    await act(async () => {
      await result.current.doiAvatar(png);
    });

    // Thứ được lưu là ẢNH DO CANVAS VẼ LẠI, không phải byte gốc của file người dùng.
    expect(toDataURL).toHaveBeenCalledWith('image/png');
    expect(localStorage.getItem('moodbite.avatar')).toBe('data:image/png;base64,VE_LAI');

    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });
});
