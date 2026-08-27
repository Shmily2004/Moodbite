/**
 * VIEWMODEL của màn "Quản lý món ăn".
 *
 * Chỉ điều phối: giữ từ khoá + bộ lọc, gọi API, giữ trạng thái tải/lỗi. Không lọc và
 * không xếp lại ở đây — backend đã làm (`list_dishes_admin.py`). Lọc thêm ở frontend sẽ
 * lệch với con số `total` mà chính backend trả về.
 *
 * ⚠️ TÌM KIẾM CÓ HOÃN (debounce). Gõ "bún chả" là 7 lần đổi state; không hoãn thì thành
 * 7 request, và request về sau có thể tới TRƯỚC request trước đó khiến bảng nhảy về kết
 * quả cũ. `LUOT_HOAN_MS` đủ ngắn để không thấy giật, đủ dài để gộp một lần gõ.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type { AdminDishRow, LocMon } from '@/shared/api';

const LUOT_HOAN_MS = 300;
/** Bảng chỉ hiện tối đa ngần này; `total` cho biết bộ lọc khớp bao nhiêu. */
const SO_DONG = 50;

export interface UseDishAdminResult {
  rows: AdminDishRow[];
  /** Tổng khớp bộ lọc — có thể LỚN HƠN `rows.length`. */
  total: number;
  query: string;
  setQuery: (q: string) => void;
  filter: LocMon;
  setFilter: (f: LocMon) => void;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useDishAdmin(): UseDishAdminResult {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<LocMon>('all');
  const [rows, setRows] = useState<AdminDishRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  // Đánh số mỗi lần gọi. Chỉ nhận kết quả của lần gọi MỚI NHẤT — chống chuyện response
  // của từ khoá cũ về sau và ghi đè kết quả đúng.
  const soLuot = useRef(0);

  useEffect(() => {
    const luot = ++soLuot.current;
    let conSong = true;
    setLoading(true);

    const hen = setTimeout(() => {
      adminApi
        .listDishes({ q: query || null, filter, limit: SO_DONG })
        .then((kq) => {
          if (!conSong || luot !== soLuot.current) return;
          setRows(kq.results);
          setTotal(kq.total);
          setError(null);
        })
        .catch((err: unknown) => {
          if (!conSong || luot !== soLuot.current) return;
          setError(err instanceof ApiError ? err.message : (err as Error).message);
        })
        .finally(() => {
          if (conSong && luot === soLuot.current) setLoading(false);
        });
    }, LUOT_HOAN_MS);

    return () => {
      conSong = false;
      clearTimeout(hen);
    };
  }, [query, filter, lan]);

  const reload = useCallback(() => setLan((n) => n + 1), []);

  return { rows, total, query, setQuery, filter, setFilter, loading, error, reload };
}
