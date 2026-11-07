/**
 * Chia sẻ phiên đăng nhập cho MỌI route.
 *
 * VÌ SAO CẦN CONTEXT: trước khi có router, `App.tsx` giữ state đăng nhập rồi truyền
 * xuống bằng props. Có router rồi thì trang đăng nhập, layout và trang quản lý là ba
 * route ANH EM — không còn cha chung để truyền props xuống nữa.
 *
 * VÌ SAO ĐẶT Ở `features/admin-login` CHỨ KHÔNG PHẢI `app/`:
 * luật import của FSD chỉ cho đi XUỐNG (`app → pages → features`). Nếu để context ở
 * `app/` thì `pages/` phải import NGƯỢC LÊN - vi phạm, và `steiger` sẽ chặn.
 * Feature nào sở hữu khái niệm thì giữ context của khái niệm đó; `app/` chỉ lắp vào.
 */
import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useAdminSession } from './useAdminSession';
import type { UseAdminSessionResult } from './useAdminSession';

const AdminSessionContext = createContext<UseAdminSessionResult | null>(null);

export function AdminSessionProvider({ children }: { children: ReactNode }) {
  const session = useAdminSession();
  return (
    <AdminSessionContext.Provider value={session}>{children}</AdminSessionContext.Provider>
  );
}

export function useAdminSessionContext(): UseAdminSessionResult {
  const session = useContext(AdminSessionContext);
  if (session === null) {
    // Ném lỗi rõ ràng ngay lúc phát triển, thay vì để `null.isLoggedIn` nổ ở tận đâu đó.
    throw new Error(
      'useAdminSessionContext phải nằm trong <AdminSessionProvider>. ' +
        'Kiểm lại app/routes.tsx đã bọc provider quanh route chưa.',
    );
  }
  return session;
}
