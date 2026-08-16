/**
 * Cấu hình đọc từ biến môi trường. MỘT nơi duy nhất - không rải `import.meta.env`
 * khắp nơi, vì khi đổi tên biến sẽ phải đi tìm từng chỗ.
 */
export const API_BASE: string =
  import.meta.env.VITE_API_BASE ?? 'http://localhost:8001/api/v1';

/** Hồ Hoàn Kiếm - phải khớp HANOI_CENTER ở src/domain/value_objects/location.py */
export const HANOI_CENTER = { lat: 21.0285, lng: 105.8542 } as const;

export const DEFAULT_SEARCH_LIMIT = 10;
export const DEFAULT_RADIUS_KM = 10;
