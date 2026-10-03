/**
 * Lấy vị trí người dùng qua Geolocation API của trình duyệt.
 * MIỄN PHÍ, không cần API key, không liên quan tới Google.
 *
 * Đề án mục 5: vị trí lấy trực tiếp từ thiết bị, KHÔNG hỏi người dùng
 * "bán kính 1km/3km" như một câu khảo sát trừu tượng.
 *
 * THỨ TỰ ƯU TIÊN (thêm 2026-09-29, cùng tính năng "Địa chỉ của tôi"):
 *
 *   1. Vị trí THẬT từ trình duyệt       — khi người dùng đã bấm "Vị trí của tôi" và cho phép
 *   2. Địa chỉ MẶC ĐỊNH đã lưu          — khi đã đăng nhập và có đặt một địa chỉ mặc định
 *   3. Trung tâm Hà Nội (Hồ Gươm)       — khi không có gì ở trên
 *
 * ⚠️ KHÔNG ĐỔI NGẦM: `source` + `label` nói rõ đang dùng điểm nào, và trang PHẢI hiện
 * `label` cạnh nút định vị. Gợi ý quán quanh "Nhà" trong khi người dùng đang ở công ty mà
 * không nói ra thì họ sẽ tưởng app định vị sai.
 */
import { useCallback, useMemo, useState } from 'react';
import { HANOI_CENTER } from '@/shared/config';
import { useUserSessionContext } from '@/entities/user';
import { useDefaultAddress } from '@/entities/address';
import { HAM_DICH_VI, useT } from '@/shared/i18n';
import type { HamDich, Khoa } from '@/shared/i18n';

export interface Coordinates {
  lat: number;
  lng: number;
}

/** Điểm đang dùng đến từ đâu. */
export type NguonViTri = 'browser' | 'saved' | 'center';

export interface DiemDuPhong extends Coordinates {
  label: string;
}

// Chỉ nói LÝ DO; câu "đang dùng điểm nào" ghép sau theo điểm dự phòng thật đang có.
const ERROR_MESSAGES: Record<number, Khoa> = {
  1: 'loc.err.denied',
  2: 'loc.err.unavailable',
  3: 'loc.err.timeout',
};

export interface UseUserLocationResult {
  position: Coordinates;
  /**
   * `true` = đang dùng TRUNG TÂM HÀ NỘI, tức không có điểm nào gắn với người dùng.
   * Địa chỉ đã lưu KHÔNG tính là mặc định: đó là một chỗ thật người dùng tự chọn.
   */
  isDefault: boolean;
  source: NguonViTri;
  /** Câu hiện cho người dùng: điểm nào đang được dùng. */
  label: string;
  error: string | null;
  loading: boolean;
  request: () => void;
}

/**
 * Chọn điểm theo thứ tự ưu tiên ở đầu file. Hàm THUẦN — tách ra để test được mà không
 * phải giả lập trình duyệt.
 */
export function chonViTri(
  browser: Coordinates | null,
  saved: DiemDuPhong | null,
  t: HamDich = HAM_DICH_VI,
): { position: Coordinates; source: NguonViTri; label: string } {
  if (browser) return { position: browser, source: 'browser', label: t('loc.yours') };
  if (saved) {
    return {
      position: { lat: saved.lat, lng: saved.lng },
      source: 'saved',
      label: t('loc.saved', { name: saved.label }),
    };
  }
  return { position: { ...HANOI_CENTER }, source: 'center', label: t('loc.center') };
}

export function useUserLocation(): UseUserLocationResult {
  const session = useUserSessionContext();
  const diaChi = useDefaultAddress(session.isLoggedIn);
  const t = useT();
  const [browser, setBrowser] = useState<Coordinates | null>(null);
  const [errorCode, setErrorCode] = useState<number | null>(null);
  const [unsupported, setUnsupported] = useState(false);
  const [loading, setLoading] = useState(false);

  // useMemo theo GIÁ TRỊ SỐ: trang truyền `position` vào deps của effect gọi API — tạo
  // object mới mỗi lần render là gọi API lặp vô hạn.
  const lat = diaChi?.lat;
  const lng = diaChi?.lng;
  const nhan = diaChi?.label;
  const chon = useMemo(
    () =>
      chonViTri(
        browser,
        lat !== undefined && lng !== undefined && nhan !== undefined
          ? { lat, lng, label: nhan }
          : null,
        t,
      ),
    [browser, lat, lng, nhan, t],
  );

  const request = useCallback(() => {
    if (!navigator.geolocation) {
      setUnsupported(true);
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setBrowser({ lat: coords.latitude, lng: coords.longitude });
        setErrorCode(null);
        setLoading(false);
      },
      (err) => {
        // Bị từ chối KHÔNG phải lỗi chặn đường: vẫn còn điểm dự phòng để tìm kiếm.
        setErrorCode(err.code);
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
    );
  }, []);

  // Không `toLowerCase()` cả câu: nhãn địa chỉ là chữ người dùng tự gõ, phải giữ nguyên.
  const dangDung =
    chon.source === 'saved'
      ? t('loc.usingSaved', { name: nhan ?? '' })
      : chon.source === 'browser'
        ? t('loc.usingLast')
        : t('loc.usingCenter');
  let error: string | null = null;
  if (unsupported) {
    error = `${t('loc.err.unsupported')} ${dangDung}`;
  } else if (errorCode !== null) {
    const lyDo = t(ERROR_MESSAGES[errorCode] ?? 'loc.err.generic');
    error = `${lyDo} ${dangDung}`;
  }

  return {
    position: chon.position,
    isDefault: chon.source === 'center',
    source: chon.source,
    label: chon.label,
    error,
    loading,
    request,
  };
}
