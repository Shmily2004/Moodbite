/**
 * Nhãn CUỐI của breadcrumb trên thanh đầu ("Quản lý món ăn › Bún chả").
 *
 * VÌ SAO LÀ CONTEXT Ở `shared/`: khung (`app/layout`) vẽ breadcrumb nhưng không biết tên
 * món — chỉ trang chi tiết biết sau khi tải xong. Luật FSD cấm `pages/` import ngược lên
 * `app/`, nên cầu nối phải nằm ở tầng thấp nhất mà cả hai cùng được import.
 *
 * Không có Provider (VD render một trang lẻ trong test) thì `useDatNhanBreadcrumb` không
 * làm gì — trang vẫn chạy bình thường.
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

interface BreadcrumbCtx {
  nhan: string | null;
  datNhan: (nhan: string | null) => void;
}

const Ctx = createContext<BreadcrumbCtx | null>(null);

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [nhan, datNhan] = useState<string | null>(null);
  return <Ctx.Provider value={{ nhan, datNhan }}>{children}</Ctx.Provider>;
}

/** Khung đọc nhãn hiện tại. */
export function useNhanBreadcrumb(): string | null {
  return useContext(Ctx)?.nhan ?? null;
}

/** Trang đặt nhãn; rời trang thì tự gỡ để trang khác không mang nhãn cũ. */
export function useDatNhanBreadcrumb(nhan: string | null): void {
  const ctx = useContext(Ctx);
  const datNhan = ctx?.datNhan;
  useEffect(() => {
    if (!datNhan) return undefined;
    datNhan(nhan);
    return () => datNhan(null);
  }, [datNhan, nhan]);
}
