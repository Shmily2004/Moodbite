/**
 * Test cho bảng khai HÌNH ẢNH.
 *
 * Phần lớn file này là bảng khai do CHỦ DỰ ÁN tự điền, nên test ở đây không kiểm
 * "code chạy đúng không" mà kiểm "bảng khai có hợp lệ không" — nghĩa là nó sẽ đỏ
 * đúng lúc có người điền thiếu, thay vì để lỗi lộ ra trên trình duyệt.
 */
import { describe, expect, it } from 'vitest';
import { ANH_DU_PHONG, ANH_GIAO_DIEN, anhDuPhongCho, type AnhUI } from './images';

const MOI_ANH: Array<[string, AnhUI]> = [
  ...Object.entries(ANH_GIAO_DIEN).filter((e): e is [string, AnhUI] => e[1] !== null),
  ...Object.entries(ANH_DU_PHONG),
];

describe('bảng khai ảnh', () => {
  it('mọi ảnh đã khai đều phải có src và alt', () => {
    for (const [ten, anh] of MOI_ANH) {
      expect(anh.src, `ảnh "${ten}" thiếu src`).toBeTruthy();
      // `alt` rỗng là HỢP LỆ (ảnh trang trí), nhưng phải khai tường minh - thiếu hẳn
      // trường này thường là quên chứ không phải cố ý.
      expect(typeof anh.alt, `ảnh "${ten}" thiếu alt`).toBe('string');
    }
  });

  it('ảnh lấy trên mạng BẮT BUỘC ghi nguồn + giấy phép', () => {
    // Đây là chỗ dễ bị hỏi nhất khi bảo vệ đồ án: "ảnh này của ai?".
    for (const [ten, anh] of MOI_ANH) {
      if (/^https?:\/\//.test(anh.src)) {
        expect(anh.credit, `ảnh mạng "${ten}" chưa ghi credit`).toBeTruthy();
      }
    }
  });

  it('ảnh để trong máy phải bắt đầu bằng "/" để Vite phục vụ đúng', () => {
    for (const [ten, anh] of MOI_ANH) {
      if (!/^https?:\/\//.test(anh.src)) {
        expect(anh.src.startsWith('/'), `"${ten}" nên là "/anh/..."`).toBe(true);
      }
    }
  });
});

describe('anhDuPhongCho', () => {
  it('chưa khai ảnh dự phòng nào thì trả null - app chạy y như cũ', () => {
    expect(anhDuPhongCho('Phở Thìn', 'Nhà hàng phở')).toBeNull();
  });

  const BANG_GIA: Record<string, AnhUI> = {
    pho: { src: '/anh/pho.jpg', alt: '' },
    'bun cha': { src: '/anh/bun-cha.jpg', alt: '' },
  };

  it('khớp được cả tên CÓ DẤU lẫn KHÔNG DẤU', () => {
    // Quán thật trong dataset có cả "Phở Thìn" lẫn "Pho Bo" - không bỏ dấu thì một
    // nửa số quán không bao giờ khớp. Bug này đã xảy ra thật ở backend.
    expect(anhDuPhongCho('Phở Thìn', null, BANG_GIA)?.src).toBe('/anh/pho.jpg');
    expect(anhDuPhongCho('Pho Bo', null, BANG_GIA)?.src).toBe('/anh/pho.jpg');
  });

  it('khớp được cả ở LOẠI HÌNH quán, không chỉ ở tên', () => {
    expect(anhDuPhongCho('Quán Hương Liên', 'Bún chả', BANG_GIA)?.src).toBe(
      '/anh/bun-cha.jpg',
    );
  });

  it('không khớp gì thì trả null chứ không đoán bừa một tấm ảnh', () => {
    expect(anhDuPhongCho('Pizza 4P’s', 'Nhà hàng Ý', BANG_GIA)).toBeNull();
  });
});
