/**
 * Chia sẻ phiên tài khoản cho MỌI route.
 *
 * VÌ SAO CẦN CONTEXT: trang đăng nhập, trang đăng ký và các trang còn lại là những route
 * ANH EM — không có cha chung nào để truyền props xuống. Provider lắp ở `RootLayout`.
 *
 * VÌ SAO Ở `entities/user` CHỨ KHÔNG PHẢI `app/`: luật import của FSD chỉ cho đi XUỐNG
 * (`app → pages → widgets → features → entities`). Để context ở `app/` thì `pages/` phải
 * import NGƯỢC LÊN — vi phạm, và `steiger` sẽ chặn.
 */
import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useUserSession } from './useUserSession';
import type { UseUserSessionResult } from './useUserSession';

const UserSessionContext = createContext<UseUserSessionResult | null>(null);

export function UserSessionProvider({ children }: { children: ReactNode }) {
  const session = useUserSession();
  return (
    <UserSessionContext.Provider value={session}>{children}</UserSessionContext.Provider>
  );
}

export function useUserSessionContext(): UseUserSessionResult {
  const session = useContext(UserSessionContext);
  if (session === null) {
    // Ném lỗi rõ ràng ngay lúc phát triển, thay vì để `null.isLoggedIn` nổ ở tận đâu đó.
    throw new Error(
      'useUserSessionContext phải nằm trong <UserSessionProvider>. ' +
        'Kiểm lại app/layout/RootLayout.tsx đã bọc provider chưa.',
    );
  }
  return session;
}
