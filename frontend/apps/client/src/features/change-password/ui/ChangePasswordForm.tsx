/**
 * Đổi mật khẩu khi ĐANG đăng nhập (tab Cài đặt của trang tài khoản).
 *
 * Khác trang "quên mật khẩu": ở đó người dùng KHÔNG vào được tài khoản nên phải qua email.
 * Ở đây họ đã ở trong tài khoản, chỉ muốn đổi — không có lý do gì bắt đi vòng qua hộp thư.
 *
 * ⚠️ VẪN HỎI MẬT KHẨU HIỆN TẠI dù người dùng đã đăng nhập. Token nằm trong trình duyệt và
 * sống 24 giờ; ai mượn được máy lúc chủ máy đi pha cà phê là đổi mật khẩu rồi chiếm luôn
 * tài khoản. Hỏi lại biến "mượn được máy" thành "phải biết mật khẩu".
 *
 * HIỆN NGUYÊN VĂN CÂU TRẢ VỀ CỦA SERVER: nó nói rõ máy khác đã bị đăng xuất.
 *
 * ⚠️ PHẢI LƯU TOKEN MỚI. Từ 2026-09-29 đổi mật khẩu thu hồi MỌI token, kể cả token của máy
 * đang gọi; server trả token mới cho máy này. Quên lưu thì lần gọi kế tiếp 401 và người
 * dùng bị đá ra ngay sau khi đổi mật khẩu thành công.
 */
import { useState } from 'react';
import type { FormEvent } from 'react';
import { authApi } from '@/shared/api';
import { replaceToken } from '@/shared/lib';

export function ChangePasswordForm() {
  const [cu, setCu] = useState('');
  const [moi, setMoi] = useState('');
  const [dangGui, setDangGui] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [xong, setXong] = useState<string | null>(null);

  const gui = async (su_kien: FormEvent) => {
    su_kien.preventDefault();
    setDangGui(true);
    setLoi(null);
    setXong(null);
    try {
      const ket_qua = await authApi.changePassword({
        current_password: cu,
        new_password: moi,
      });
      replaceToken(ket_qua.token);
      setXong(ket_qua.message);
      setCu('');
      setMoi('');
    } catch (err) {
      // Luật độ dài mật khẩu nằm ở backend (`domain/entities/user.py`) và câu lỗi cũng
      // từ đó ra. KHÔNG chép luật xuống frontend — hai bản luật sẽ có ngày lệch nhau.
      setLoi(err instanceof Error ? err.message : 'Không đổi được mật khẩu.');
    } finally {
      setDangGui(false);
    }
  };

  return (
    <form className="pwform" onSubmit={gui}>
      <label className="pwform__row">
        <span>Mật khẩu hiện tại</span>
        <input
          type="password"
          autoComplete="current-password"
          value={cu}
          onChange={(e) => setCu(e.target.value)}
          required
        />
      </label>
      <label className="pwform__row">
        <span>Mật khẩu mới</span>
        <input
          type="password"
          autoComplete="new-password"
          value={moi}
          onChange={(e) => setMoi(e.target.value)}
          required
        />
      </label>

      {loi && <p className="notice notice--error">{loi}</p>}
      {xong && <p className="notice">{xong}</p>}

      <button
        type="submit"
        className="btn btn--sm"
        disabled={dangGui || cu === '' || moi === ''}
      >
        {dangGui ? 'Đang đổi…' : 'Đổi mật khẩu'}
      </button>
    </form>
  );
}
