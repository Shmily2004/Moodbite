/**
 * Số liệu cho biểu đồ radar "Khẩu vị của bạn" ở trang tài khoản.
 *
 * MỖI TRỤC = MỘT NHÓM SỞ THÍCH CÓ THẬT trong `SO_THICH` (cách chế biến, nóng/mát, tâm
 * trạng…). Giá trị = số ô người dùng đã chọn / số ô của nhóm đó.
 *
 * ⚠️ CHỈ LÀ ĐẾM ĐỂ VẼ, KHÔNG PHẢI ĐIỂM KHẨU VỊ. Bản thiết kế vẽ các trục "Cay · Ngọt · Đậm
 * đà · Lành mạnh" như thể hệ thống đo được khẩu vị — ta KHÔNG có dữ liệu đó. Biểu đồ chỉ
 * phản chiếu lại đúng những ô người dùng tự bấm, và câu phụ dưới tiêu đề nói rõ như vậy.
 *
 * Nhóm KHÔNG có ô nào (hiện là `cuisines`) thì bỏ trục, không vẽ một trục luôn bằng 0.
 */
import { SO_THICH } from './danh_sach';
import type { NhomLoc } from './danh_sach';

export interface TrucRadar {
  nhom: NhomLoc;
  daChon: number;
  tong: number;
}

/** Thứ tự trục cố định, để hình không xoay lung tung khi thêm/bớt sở thích. */
const THU_TU_TRUC: NhomLoc[] = ['cookingMethods', 'temperatures', 'mood', 'cuisines'];

export function trucRadar(idsDaChon: string[]): TrucRadar[] {
  return THU_TU_TRUC.map((nhom) => {
    const trongNhom = SO_THICH.filter((x) => x.nhom === nhom);
    return {
      nhom,
      tong: trongNhom.length,
      daChon: trongNhom.filter((x) => idsDaChon.includes(x.id)).length,
    };
  }).filter((truc) => truc.tong > 0);
}
