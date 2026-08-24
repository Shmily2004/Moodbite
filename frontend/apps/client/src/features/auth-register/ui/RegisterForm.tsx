/**
 * VIEW: form đăng ký. Chỉ JSX + state của riêng các ô nhập.
 *
 * MỘT thứ duy nhất được kiểm ở đây: HAI Ô MẬT KHẨU CÓ KHỚP NHAU KHÔNG. Đó không phải
 * quy tắc nghiệp vụ — backend không bao giờ nhìn thấy ô "nhập lại", nó chỉ tồn tại để
 * người dùng khỏi gõ nhầm. Còn độ dài mật khẩu, ký tự cho phép trong tên đăng nhập… thì
 * ĐỂ BACKEND TRẢ LỜI: chép luật xuống đây là tạo nơi thứ hai chứa nghiệp vụ, và chắc
 * chắn có ngày hai nơi lệch nhau (CLAUDE.md mục 1b).
 *
 * Dòng gợi ý dưới ô tên đăng nhập chỉ là CHỮ MÔ TẢ cho người dùng đọc, không phải chỗ
 * cưỡng chế luật — nội dung của nó bám theo `src/domain/entities/user.py`.
 *
 * ⚠️ GIỮ CHO THẺ FORM VỪA MỘT MÀN HÌNH (chủ dự án yêu cầu 2026-08-22): bản thiết kế không
 * bắt cuộn. Mỗi dòng gợi ý là ~48px chiều cao, nên chỉ giữ đúng dòng cần thiết nhất (luật
 * đặt tên đăng nhập — thứ backend sẽ từ chối nếu gõ sai); phần còn lại dồn vào placeholder
 * và `title`. Thêm ô mới thì phải cân lại chỗ này.
 */
import { useId, useState } from 'react';
import type { ReactNode } from 'react';
import { IconEye, IconEyeOff, IconLock, IconMail, IconUser } from '@/shared/ui';

export interface RegisterFormProps {
  loading: boolean;
  /** Lỗi từ server (tên đã có người dùng, sai định dạng, mất mạng…). */
  error: string | null;
  onSubmit: (
    username: string,
    password: string,
    displayName: string,
    email: string,
  ) => void;
  /** Nội dung xếp dưới đường kẻ "hoặc" — thường là link về trang đăng nhập. */
  footer?: ReactNode;
}

export function RegisterForm({ loading, error, onSubmit, footer }: RegisterFormProps) {
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [hienMatKhau, setHienMatKhau] = useState(false);
  const [dongY, setDongY] = useState(false);
  const [hienGhiChuDieuKhoan, setHienGhiChuDieuKhoan] = useState(false);
  const [loiKhop, setLoiKhop] = useState<string | null>(null);

  const idTen = useId();
  const idHienThi = useId();
  const idEmail = useId();
  const idMatKhau = useId();
  const idNhapLai = useId();
  const idDongY = useId();

  return (
    <form
      className="auth-card"
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        // Form đặt `noValidate`, nên thuộc tính `required` của ô email KHÔNG tự chặn —
        // nó chỉ còn tác dụng gợi ý cho trình duyệt/trình đọc màn hình. Phải kiểm ở đây,
        // đúng cách đã làm với hai ô mật khẩu ngay bên dưới.
        if (email.trim() === '') {
          setLoiKhop('Bạn cần nhập email để xác minh tài khoản và lấy lại mật khẩu.');
          return;
        }
        if (password !== confirm) {
          // Không gọi API khi đã biết chắc là gõ nhầm: đỡ một vòng mạng, và quan trọng
          // hơn là người dùng nhận phản hồi ngay lập tức.
          setLoiKhop('Hai ô mật khẩu chưa giống nhau. Kiểm tra lại giúp mình nhé.');
          return;
        }
        setLoiKhop(null);
        onSubmit(username, password, displayName, email);
      }}
    >
      <h1 className="auth-card__title">Tạo tài khoản mới</h1>
      <p className="auth-card__sub">
        Bắt đầu hành trình khám phá ẩm thực Hà Nội.
      </p>

      <label className="field__label" htmlFor={idTen}>
        Tên đăng nhập
      </label>
      <div className="field field--tight">
        <IconUser className="field__icon" />
        <input
          id={idTen}
          className="field__input"
          value={username}
          placeholder="Chọn tên đăng nhập"
          autoComplete="username"
          autoFocus
          required
          onChange={(event) => setUsername(event.target.value)}
        />
      </div>
      <p className="field__hint">3–32 ký tự: chữ thường không dấu, số, dấu - và _</p>

      <label className="field__label" htmlFor={idHienThi}>
        Tên hiển thị
      </label>
      <div className="field field--tight">
        <IconUser className="field__icon" />
        <input
          id={idHienThi}
          className="field__input"
          value={displayName}
          // Lời giải thích dồn vào placeholder + `title` thay vì một dòng gợi ý riêng:
          // bản thiết kế chỉ có MỘT dòng gợi ý (dưới ô tên đăng nhập), và mỗi dòng gợi ý
          // thừa đẩy thẻ form dài thêm ~48px — đủ để tràn xuống dưới màn hình.
          placeholder="Tên hiển thị (có thể bỏ trống)"
          title="Được dùng tiếng Việt có dấu. Bỏ trống thì hiển thị theo tên đăng nhập."
          autoComplete="nickname"
          onChange={(event) => setDisplayName(event.target.value)}
        />
      </div>

      {/*
        Ô EMAIL — bản thiết kế KHÔNG có ô này, thêm vào có chủ đích (2026-08-22).

        BẮT BUỘC từ 2026-08-24 (trước đó tuỳ chọn). Chủ dự án đổi sau khi luồng XÁC MINH
        EMAIL hoàn thành. Lý lẽ cũ ("bắt buộc thì làm rơi người đăng ký") chỉ đúng khi
        email chưa dùng vào việc gì ngoài phòng xa; nay nó là thứ duy nhất chứng minh tài
        khoản thuộc về người có thật, và là đường DUY NHẤT lấy lại mật khẩu — quên mật
        khẩu mà không có email thì mất hẳn tài khoản, không ai cứu được.

        `required` để trình duyệt chặn ngay tại chỗ, khỏi phải đi một vòng lên server rồi
        mới báo lỗi. Backend vẫn kiểm lại — `required` của HTML sửa được bằng DevTools.
      */}
      <label className="field__label" htmlFor={idEmail}>
        Email
      </label>
      <div className="field field--tight">
        <IconMail className="field__icon" />
        <input
          id={idEmail}
          className="field__input"
          type="email"
          value={email}
          placeholder="email@cua-ban.com"
          autoComplete="email"
          required
          onChange={(event) => setEmail(event.target.value)}
        />
      </div>
      {/* `--phu`: dòng này bị ẩn trên màn hình thấp để thẻ form vừa một viewport. Ẩn được
          vì nội dung đã có ở nhãn "(không bắt buộc)"; còn dòng gợi ý của TÊN ĐĂNG NHẬP thì
          KHÔNG ẩn — sai luật đặt tên là backend từ chối, phải cho người dùng biết trước. */}
      <p className="field__hint field__hint--phu">
        Dùng để xác minh tài khoản và lấy lại mật khẩu khi bạn quên.
      </p>

      <label className="field__label" htmlFor={idMatKhau}>
        Mật khẩu
      </label>
      <div className="field">
        <IconLock className="field__icon" />
        <input
          id={idMatKhau}
          className="field__input"
          type={hienMatKhau ? 'text' : 'password'}
          value={password}
          placeholder="Ít nhất 8 ký tự"
          autoComplete="new-password"
          required
          onChange={(event) => setPassword(event.target.value)}
        />
        <button
          type="button"
          className="field__eye"
          onClick={() => setHienMatKhau((cu) => !cu)}
          aria-label={hienMatKhau ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
          aria-pressed={hienMatKhau}
          tabIndex={-1}
        >
          {hienMatKhau ? <IconEyeOff /> : <IconEye />}
        </button>
      </div>

      <label className="field__label" htmlFor={idNhapLai}>
        Xác nhận mật khẩu
      </label>
      <div className="field">
        <IconLock className="field__icon" />
        <input
          id={idNhapLai}
          className="field__input"
          // Cùng bật/tắt che chữ với ô trên: hai ô mật khẩu mà một ô hiện một ô che thì
          // người dùng không đối chiếu được, trong khi đối chiếu chính là việc của ô này.
          type={hienMatKhau ? 'text' : 'password'}
          value={confirm}
          placeholder="Nhập lại mật khẩu"
          autoComplete="new-password"
          required
          onChange={(event) => setConfirm(event.target.value)}
        />
      </div>

      <div className="auth-card__row auth-card__row--start">
        <label className="checkbox" htmlFor={idDongY}>
          <input
            id={idDongY}
            type="checkbox"
            checked={dongY}
            required
            onChange={(event) => setDongY(event.target.checked)}
          />
          <span>
            Tôi đồng ý với{' '}
            {/*
              KHÔNG phải thẻ <a>: chưa có trang điều khoản nào để dẫn tới. Link trỏ vào hư
              vô còn tệ hơn là nói thẳng ra - giống nút "Quên mật khẩu?" bên trang đăng nhập.
            */}
            <button
              type="button"
              className="linkish"
              onClick={() => setHienGhiChuDieuKhoan((cu) => !cu)}
              aria-expanded={hienGhiChuDieuKhoan}
            >
              Điều khoản sử dụng
            </button>
          </span>
        </label>
      </div>

      {hienGhiChuDieuKhoan && (
        <p className="auth-card__note">
          Điều khoản sử dụng chưa được soạn. MoodBite là đồ án tốt nghiệp: tài khoản chỉ
          dùng để lưu tương tác của bạn trong phạm vi đồ án, không chia sẻ cho bên nào khác.
        </p>
      )}

      {(loiKhop || error) && (
        <p className="auth-card__error" role="alert">
          {loiKhop ?? error}
        </p>
      )}

      <button type="submit" className="btn btn--accent" disabled={loading}>
        {loading ? 'Đang tạo tài khoản…' : 'Tạo tài khoản'}
      </button>

      {/*
        KHÔNG có đường kẻ "hoặc" như thẻ đăng nhập — bản thiết kế `design/Register.png`
        đi thẳng từ nút xuống dòng "Đã có tài khoản?". Bỏ nó vừa đúng mẫu, vừa tiết kiệm
        ~34px chiều cao, giúp thẻ 5 ô này vừa một màn hình 900px mà không phải cuộn.
      */}
      {footer && <p className="auth-card__footer auth-card__footer--tight">{footer}</p>}
    </form>
  );
}
