/**
 * VIEWMODEL "Bộ sưu tập của tôi": giữ danh sách + điều phối gọi API.
 *
 * KHÔNG cập nhật lạc quan (khác `useFavorites`): mọi thao tác ở đây đều có thể bị server
 * từ chối vì một LUẬT (tên quá dài, đã đủ 50 bộ, bộ đầy 200 mục) — luật đó chỉ nằm ở
 * backend (CLAUDE.md mục 1b). Đợi server trả lời rồi mới đổi giao diện thì không bao giờ
 * phải "rút lại" một thay đổi đã hiện ra, và câu lỗi tiếng Việt của server hiện nguyên văn.
 *
 * Mỗi hàm trả `true`/`false` (hoặc bộ vừa tạo) để giao diện biết có nên xoá ô nhập hay không.
 */
import { useCallback, useEffect, useState } from 'react';
import { useUserSessionContext } from '@/entities/user';
import {
  boKhoiBoSuuTap,
  doiTenBoSuuTap,
  taiBoSuuTap,
  taoBoSuuTap,
  themVaoBoSuuTap,
  xoaBoSuuTap,
} from '../api/collectionsApi';
import type { BoSuuTap, LoaiMuc, MucBoSuuTap } from '../api/collectionsApi';

export interface UseCollectionsResult {
  collections: BoSuuTap[];
  loading: boolean;
  error: string | null;
  /** Đang gửi một thao tác — giao diện khoá nút để không bấm hai lần. */
  busy: boolean;
  create: (name: string) => Promise<BoSuuTap | null>;
  rename: (id: string, name: string) => Promise<boolean>;
  remove: (id: string) => Promise<boolean>;
  addItem: (id: string, muc: MucBoSuuTap) => Promise<boolean>;
  /** Tạo bộ mới rồi thêm luôn mục vào — ô "+ Bộ sưu tập mới" trên thẻ đã lưu. */
  createAndAdd: (name: string, muc: MucBoSuuTap) => Promise<boolean>;
  removeItem: (id: string, itemType: LoaiMuc, itemId: string) => Promise<boolean>;
  reload: () => void;
}

function thongBaoLoi(err: unknown, macDinh: string): string {
  return err instanceof Error && err.message ? err.message : macDinh;
}

export function useCollections(): UseCollectionsResult {
  const session = useUserSessionContext();
  const [collections, setCollections] = useState<BoSuuTap[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  const reload = useCallback(() => setLan((n) => n + 1), []);

  useEffect(() => {
    // Khách không có bộ sưu tập — tính năng này cần tài khoản (dữ liệu nằm ở server).
    if (!session.isLoggedIn) {
      setCollections([]);
      return;
    }
    let con_song = true;
    setLoading(true);
    taiBoSuuTap()
      .then((ds) => {
        if (!con_song) return;
        setCollections(ds);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!con_song) return;
        setError(thongBaoLoi(err, 'Không tải được bộ sưu tập.'));
      })
      .finally(() => {
        if (con_song) setLoading(false);
      });
    return () => {
      con_song = false;
    };
  }, [session.isLoggedIn, lan]);

  /** Chạy một thao tác: khoá nút, bắt lỗi thành câu cho người dùng đọc. */
  const chay = useCallback(async <T,>(viec: () => Promise<T>, loi: string) => {
    setBusy(true);
    try {
      const kq = await viec();
      setError(null);
      return kq;
    } catch (err) {
      setError(thongBaoLoi(err, loi));
      return null;
    } finally {
      setBusy(false);
    }
  }, []);

  /** Thay đúng một bộ bằng bản server vừa trả về, giữ nguyên thứ tự. */
  const thay = (bo: BoSuuTap) =>
    setCollections((ds) => ds.map((x) => (x.id === bo.id ? bo : x)));

  const create = useCallback(
    async (name: string) => {
      const bo = await chay(() => taoBoSuuTap(name), 'Không tạo được bộ sưu tập.');
      if (bo) setCollections((ds) => [bo, ...ds]); // server sắp mới nhất lên đầu
      return bo;
    },
    [chay],
  );

  const rename = useCallback(
    async (id: string, name: string) => {
      const bo = await chay(() => doiTenBoSuuTap(id, name), 'Không đổi được tên.');
      if (bo) thay(bo);
      return bo !== null;
    },
    [chay],
  );

  const remove = useCallback(
    async (id: string) => {
      const ok = await chay(async () => {
        await xoaBoSuuTap(id);
        return true;
      }, 'Không xoá được bộ sưu tập.');
      if (ok) setCollections((ds) => ds.filter((x) => x.id !== id));
      return ok === true;
    },
    [chay],
  );

  const addItem = useCallback(
    async (id: string, muc: MucBoSuuTap) => {
      const bo = await chay(() => themVaoBoSuuTap(id, muc), 'Không thêm được vào bộ.');
      if (bo) thay(bo);
      return bo !== null;
    },
    [chay],
  );

  const createAndAdd = useCallback(
    async (name: string, muc: MucBoSuuTap) => {
      const bo = await create(name);
      if (!bo) return false;
      return addItem(bo.id, muc);
    },
    [create, addItem],
  );

  const removeItem = useCallback(
    async (id: string, itemType: LoaiMuc, itemId: string) => {
      const ok = await chay(async () => {
        await boKhoiBoSuuTap(id, itemType, itemId);
        return true;
      }, 'Không bỏ được mục khỏi bộ.');
      if (ok) {
        setCollections((ds) =>
          ds.map((x) => {
            if (x.id !== id) return x;
            const items = x.items.filter(
              (m) => !(m.itemType === itemType && m.itemId === itemId),
            );
            return { ...x, items, itemCount: items.length };
          }),
        );
      }
      return ok === true;
    },
    [chay],
  );

  return {
    collections,
    loading,
    error,
    busy,
    create,
    rename,
    remove,
    addItem,
    createAndAdd,
    removeItem,
    reload,
  };
}
