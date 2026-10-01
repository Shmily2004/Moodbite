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
const ERROR_MESSAGES: Record<number, string> = {
  1: 'Bạn đã từ chối chia sẻ vị trí.',
  2: 'Không xác định được vị trí.',
  3: 'Quá thời gian chờ định vị.',
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
): { position: Coordinates; source: NguonViTri; label: string } {
  if (browser) return { position: browser, source: 'browser', label: 'Vị trí của bạn' };
  if (saved) {
    return {
      position: { lat: saved.lat, lng: saved.lng },
      source: 'saved',
      label: `Địa chỉ đã lưu: ${saved.label}`,
    };
  }
  return { position: { ...HANOI_CENTER }, source: 'center', label: 'Trung tâm Hà Nội' };
}

export function useUserLocation(): UseUserLocationResult {
  const session = useUserSessionContext();
  const diaChi = useDefaultAddress(session.isLoggedIn);
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
      ),
    [browser, lat, lng, nhan],
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
      ? `địa chỉ đã lưu "${nhan}"`
      : chon.source === 'browser'
        ? 'vị trí lấy được lần trước'
        : 'trung tâm Hà Nội';
  let error: string | null = null;
  if (unsupported) {
    error = `Trình duyệt không hỗ trợ định vị. Đang dùng ${dangDung}.`;
  } else if (errorCode !== null) {
    const lyDo = ERROR_MESSAGES[errorCode] ?? 'Không lấy được vị trí.';
    error = `${lyDo} Đang dùng ${dangDung}.`;
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
