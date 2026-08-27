/**
 * TRANG CÀI ĐẶT HỆ THỐNG — cấu hình đang chạy + trạng thái từng kho dữ liệu.
 *
 * ⚠️ CHỈ ĐỌC, VÀ ĐÓ LÀ CHỦ ĐÍCH — không phải làm dở.
 * Cấu hình nằm ở biến môi trường / `.env.local`. Cho sửa qua HTTP nghĩa là một lỗ hổng
 * ở trang quản trị đổi được cả khoá ký token và địa chỉ máy chủ thư. Đổi cấu hình là
 * việc của người có quyền vào máy chủ, không phải của một phiên đăng nhập trình duyệt.
 * Backend cũng KHÔNG có endpoint ghi, nên chỗ này không thể "quên" mà thành ghi được.
 *
 * ⚠️ KHÔNG HIỂN THỊ SECRET NÀO. Backend chỉ trả cờ "đã cấu hình hay chưa"
 * (`email_configured`), không trả mật khẩu SMTP hay khoá ký. Có test backend chặn.
 */
import { useSystem } from '@/features/view-system';
import type { AdminSystemService } from '@/shared/api';

function gio(giay: number): string {
  if (giay >= 3600) return `${Math.round(giay / 3600)} giờ`;
  if (giay >= 60) return `${Math.round(giay / 60)} phút`;
  return `${giay} giây`;
}

export function SystemPage() {
  const { data, loading, error, reload } = useSystem();

  return (
    <div className="tong-quan">
      <header className="bang__dau">
        <h2 className="panel__tieu-de">Cài đặt hệ thống</h2>
        <button className="ghost" onClick={reload} disabled={loading}>
          {loading ? 'Đang tải…' : '⟳ Tải lại'}
        </button>
      </header>

      {error && <p className={data ? 'notice notice--warn' : 'panel panel--error'}>{error}</p>}
      {loading && !data && <p className="panel muted">Đang đọc cấu hình…</p>}

      {data && (
        <>
          <section className="panel">
            <h3 className="panel__tieu-de">Cấu hình đang chạy</h3>
            <dl className="cau-hinh">
              <Muc nhan="Kho dữ liệu" gia_tri={data.storage_backend} />
              <Muc
                nhan="Thời tiết theo ngữ cảnh"
                gia_tri={data.weather_enabled ? 'Đang bật' : 'Đang tắt'}
                ghi_chu={
                  data.weather_enabled
                    ? undefined
                    : 'Tắt là mặc định. Bật bằng MOODBITE_ENABLE_WEATHER=1 khi đã deploy.'
                }
              />
              <Muc
                nhan="Gửi thư (SMTP)"
                gia_tri={data.email_configured ? 'Đã cấu hình' : 'Chưa cấu hình'}
                ghi_chu={
                  data.email_configured
                    ? undefined
                    : 'Chưa có MOODBITE_SMTP_* — quên mật khẩu và xác minh email sẽ không gửi được.'
                }
              />
              <Muc nhan="Phiên quản trị hết hạn sau" gia_tri={gio(data.admin_token_ttl_seconds)} />
              <Muc nhan="Phiên người dùng hết hạn sau" gia_tri={gio(data.user_token_ttl_seconds)} />
              <Muc nhan="Địa chỉ web (dựng link trong thư)" gia_tri={data.app_base_url || '—'} />
            </dl>
            {/* Nói thẳng vì sao không có nút Lưu, thay vì để người dùng đi tìm. */}
            <p className="muted panel__ghi-chu">
              Chỉ xem. Cấu hình nằm ở <code>.env.local</code> trên máy chủ — sửa xong phải
              khởi động lại backend. Cho sửa qua đây thì một lỗ hổng ở trang quản trị đổi
              được cả khoá ký token.
            </p>
          </section>

          <section className="panel">
            <h3 className="panel__tieu-de">Trạng thái kho dữ liệu</h3>
            <ul className="kho">
              {data.services.map((s: AdminSystemService) => (
                <li key={s.key} className="kho__dong">
                  <span
                    className={s.ready ? 'nhan nhan--ok' : 'nhan nhan--loi'}
                    aria-label={s.ready ? 'Sẵn sàng' : 'Lỗi'}
                  >
                    {s.ready ? 'Sẵn sàng' : 'Lỗi'}
                  </span>
                  <span className="kho__ten">{s.label}</span>
                  <span className="muted kho__chi-tiet">{s.detail || '—'}</span>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}

function Muc({
  nhan,
  gia_tri,
  ghi_chu,
}: {
  nhan: string;
  gia_tri: string;
  ghi_chu?: string;
}) {
  return (
    <div className="cau-hinh__muc">
      <dt>{nhan}</dt>
      <dd>
        {gia_tri}
        {ghi_chu && <span className="muted cau-hinh__ghi-chu">{ghi_chu}</span>}
      </dd>
    </div>
  );
}
