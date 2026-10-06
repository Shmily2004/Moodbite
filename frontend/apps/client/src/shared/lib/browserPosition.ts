/**
 * Vị trí THẬT từ trình duyệt, giữ trong `sessionStorage` cho cả phiên (tab) hiện tại.
 *
 * VÌ SAO: mỗi trang gọi `useUserLocation()` riêng, toạ độ trình duyệt từng chỉ là state
 * cục bộ của trang đó. Người dùng bấm "Vị trí của tôi" ở trang chủ rồi mở một món → trang
 * món lặng lẽ quay về địa chỉ đã lưu / Hồ Gươm mà vẫn ghi "Quán gần bạn" (audit 2026-10-06).
 *
 * `sessionStorage` chứ không phải `localStorage`: vị trí là dữ liệu nhạy cảm và đổi theo
 * chỗ người dùng đang đứng — đóng tab là quên, không mang sang hôm sau.
 */
const KHOA = 'moodbite.browser_position';

export interface ToaDo {
  lat: number;
  lng: number;
}

export function readBrowserPosition(): ToaDo | null {
  try {
    const raw = sessionStorage.getItem(KHOA);
    if (!raw) return null;
    const v = JSON.parse(raw) as Partial<ToaDo>;
    if (typeof v.lat !== 'number' || typeof v.lng !== 'number') return null;
    if (!Number.isFinite(v.lat) || !Number.isFinite(v.lng)) return null;
    return { lat: v.lat, lng: v.lng };
  } catch {
    // Kho bị chặn (chế độ riêng tư) hoặc dữ liệu hỏng → coi như chưa có vị trí.
    return null;
  }
}

export function writeBrowserPosition(pos: ToaDo): void {
  try {
    sessionStorage.setItem(KHOA, JSON.stringify({ lat: pos.lat, lng: pos.lng }));
  } catch {
    // Không ghi được thì chỉ mất việc chia sẻ giữa các trang; trang hiện tại vẫn đúng.
  }
}
