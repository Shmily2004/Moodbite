/**
 * Cầu nối giữa provider và cây route con.
 *
 * `AdminSessionProvider` nhận `children`, còn react-router cắm route con qua `<Outlet />`.
 * Component bé xíu này ghép hai thứ đó lại, để `routes.tsx` đọc vẫn rõ ràng.
 */
import { Outlet } from 'react-router-dom';

export function SessionBoundary() {
  return <Outlet />;
}
