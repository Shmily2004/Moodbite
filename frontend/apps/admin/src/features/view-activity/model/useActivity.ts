/**
 * VIEWMODEL của màn "Nhật ký hoạt động".
 *
 * `available` do BACKEND trả, không tự suy: danh sách rỗng có hai nghĩa hoàn toàn khác
 * nhau — "chưa ai làm gì" và "không mở được kho nhật ký". Suy ở frontend thì hai tình
 * huống đó thành một, và người quản trị sẽ yên tâm rằng không có hoạt động nào trong khi
 * thực ra nhật ký đang hỏng.
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type { AuditEntry } from '@/shared/api';

const SO_DONG = 50;

export interface UseActivityResult {
  entries: AuditEntry[];
  /** Kho nhật ký mở được không. Xem docstring — đừng suy từ `entries.length`. */
  available: boolean;
  action: string | null;
  setAction: (a: string | null) => void;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useActivity(): UseActivityResult {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [available, setAvailable] = useState(true);
  const [action, setAction] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  useEffect(() => {
    let conSong = true;
    setLoading(true);

    adminApi
      .activity({ limit: SO_DONG, action })
      .then((kq) => {
        if (!conSong) return;
        setEntries(kq.entries);
        setAvailable(kq.available);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!conSong) return;
        setError(err instanceof ApiError ? err.message : (err as Error).message);
      })
      .finally(() => {
        if (conSong) setLoading(false);
      });

    return () => {
      conSong = false;
    };
  }, [action, lan]);

  const reload = useCallback(() => setLan((n) => n + 1), []);

  return { entries, available, action, setAction, loading, error, reload };
}
