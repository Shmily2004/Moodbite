/**
 * Lọc theo LOẠI + sắp xếp bảng nhóm vấn đề — phía trình duyệt, trên dữ liệu ĐÃ TẢI.
 *
 * VÌ SAO KHÔNG PHẢI NGHIỆP VỤ: bảng chỉ có 7 nhóm, và cả hai thao tác chỉ đổi CÁCH HIỆN
 * những dòng backend đã trả về — không đổi con số nào, không định nghĩa lại "nghiêm trọng"
 * là gì. Thứ tự ưu tiên mặc định vẫn là thứ tự backend gửi (`manage_issues.py`).
 */
import type { VanDeNhom } from '@/shared/api';

export type LoaiVanDe = 'quan_an' | 'mon_an' | 'du_lieu';

export type CachSap = 'uu_tien' | 'so_luong' | 'xu_ly_gan_nhat';

export const NHAN_CACH_SAP: Record<CachSap, string> = {
  uu_tien: 'Ưu tiên (mặc định)',
  so_luong: 'Số lượng nhiều nhất',
  xu_ly_gan_nhat: 'Xử lý gần nhất',
};

export function locVaSapNhom(
  nhom: VanDeNhom[],
  loai: LoaiVanDe | null,
  cachSap: CachSap,
): VanDeNhom[] {
  const daLoc = loai ? nhom.filter((v) => v.target_type === loai) : [...nhom];
  if (cachSap === 'so_luong') {
    return daLoc.sort((a, b) => b.count - a.count);
  }
  if (cachSap === 'xu_ly_gan_nhat') {
    // Nhóm chưa ai đánh dấu (`null`) xuống cuối — không coi "chưa biết" là "cũ nhất".
    const moc = (v: VanDeNhom) =>
      v.last_resolved_at ? new Date(v.last_resolved_at).getTime() : -Infinity;
    return daLoc.sort((a, b) => moc(b) - moc(a));
  }
  // `sort` ổn định: giữ nguyên thứ tự ưu tiên backend đã xếp.
  return daLoc;
}
