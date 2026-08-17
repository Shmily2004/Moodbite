/** Nơi DUY NHẤT biết URL backend của app quản trị. */
export const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? 'http://localhost:8001/api/v1';

/** Số quán tải về mỗi lần. Backend chặn trên ở 200. */
export const ADMIN_PAGE_SIZE = 50;
