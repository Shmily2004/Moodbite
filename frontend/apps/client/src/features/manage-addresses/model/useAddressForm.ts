/**
 * State của ô "Thêm địa chỉ": nhãn · mô tả · điểm đã chọn · định vị trình duyệt.
 *
 * Tách khỏi `useAddresses` vì đây là state của MỘT LẦN NHẬP (xoá sạch sau khi lưu), còn
 * kia là dữ liệu đã lưu. Gộp lại thì mỗi lần tải lại danh sách lại phải cẩn thận không
 * xoá mất chữ người dùng đang gõ.
 *
 * ⚠️ KHÔNG có geocoding: điểm chỉ đến từ trình duyệt hoặc cú bấm trên bản đồ. Không có
 * nút "tìm theo địa chỉ" — dịch vụ tra địa chỉ miễn phí (Nominatim) cấm dùng kiểu này
 * theo điều khoản, còn Google cần thẻ thanh toán.
 */
import { useCallback, useState } from 'react';

export interface DiemChon {
  lat: number;
  lng: number;
}

export interface UseAddressFormResult {
  label: string;
  setLabel: (v: string) => void;
  addressText: string;
  setAddressText: (v: string) => void;
  point: DiemChon | null;
  setPoint: (p: DiemChon) => void;
  locating: boolean;
  /** `true` khi trình duyệt không cho/không lấy được vị trí — gợi ý bấm bản đồ. */
  geoFailed: boolean;
  locateMe: () => void;
  reset: () => void;
}

export function useAddressForm(): UseAddressFormResult {
  const [label, setLabel] = useState('');
  const [addressText, setAddressText] = useState('');
  const [point, setPointState] = useState<DiemChon | null>(null);
  const [locating, setLocating] = useState(false);
  const [geoFailed, setGeoFailed] = useState(false);

  const setPoint = useCallback((p: DiemChon) => {
    setPointState(p);
    setGeoFailed(false);
  }, []);

  const locateMe = useCallback(() => {
    if (!navigator.geolocation) {
      setGeoFailed(true);
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setPointState({ lat: coords.latitude, lng: coords.longitude });
        setGeoFailed(false);
        setLocating(false);
      },
      () => {
        setGeoFailed(true);
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  }, []);

  const reset = useCallback(() => {
    setLabel('');
    setAddressText('');
    setPointState(null);
    setGeoFailed(false);
  }, []);

  return {
    label,
    setLabel,
    addressText,
    setAddressText,
    point,
    setPoint,
    locating,
    geoFailed,
    locateMe,
    reset,
  };
}
