/**
 * Gọi API "Địa chỉ của tôi". Ở `entities/` vì HAI nơi cần tới: `features/manage-addresses`
 * (thêm/sửa/xoá) và `features/pick-location` (lấy địa chỉ mặc định làm điểm dự phòng).
 * FSD cấm hai feature import nhau, nên phần dùng chung phải nằm ở tầng dưới.
 */
import { myPlacesApi } from '@/shared/api';
import type { UserAddressData } from '@/shared/api';

export type DiaChi = UserAddressData;

export async function taiDiaChi(): Promise<DiaChi[]> {
  const data = await myPlacesApi.addresses();
  // `?? []`: phản hồi thiếu trường (server cũ, mock trong test) không được làm sập trang.
  return data.addresses ?? [];
}

export function themDiaChi(body: {
  label: string;
  lat: number;
  lng: number;
  address_text?: string | null;
  is_default?: boolean | null;
}): Promise<DiaChi> {
  return myPlacesApi.createAddress(body);
}

export function suaDiaChi(
  addressId: string,
  body: { label?: string | null; address_text?: string | null; is_default?: boolean | null },
): Promise<DiaChi> {
  return myPlacesApi.updateAddress(addressId, body);
}

export function xoaDiaChi(addressId: string): Promise<unknown> {
  return myPlacesApi.deleteAddress(addressId);
}
