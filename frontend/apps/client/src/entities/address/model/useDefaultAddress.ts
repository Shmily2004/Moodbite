/**
 * Địa chỉ MẶC ĐỊNH của người đang đăng nhập — hoặc `null`.
 *
 * `enabled` do nơi gọi truyền vào (thường là `session.isLoggedIn`) thay vì tự đọc phiên:
 * `entities/address` không được import `entities/user` (FSD cấm import ngang giữa hai
 * slice cùng tầng).
 *
 * Lỗi mạng -> `null`, KHÔNG ném: đây chỉ là điểm dự phòng vị trí. Không tải được thì lui
 * về trung tâm Hà Nội như trước, lượt tìm kiếm không được hỏng vì nó (CLAUDE.md mục 4.7).
 */
import { useEffect, useState } from 'react';
import { taiDiaChi } from '../api/addressApi';

export interface DiaChiMacDinh {
  addressId: string;
  label: string;
  lat: number;
  lng: number;
}

export function useDefaultAddress(enabled: boolean): DiaChiMacDinh | null {
  const [macDinh, setMacDinh] = useState<DiaChiMacDinh | null>(null);

  useEffect(() => {
    if (!enabled) {
      setMacDinh(null);
      return;
    }
    let con_song = true;
    taiDiaChi()
      .then((ds) => {
        if (!con_song) return;
        const dc = ds.find((x) => x.is_default);
        setMacDinh(
          dc ? { addressId: dc.address_id, label: dc.label, lat: dc.latitude, lng: dc.longitude } : null,
        );
      })
      .catch(() => {
        if (con_song) setMacDinh(null);
      });
    return () => {
      con_song = false;
    };
  }, [enabled]);

  return macDinh;
}
