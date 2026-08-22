/** VIEW: đổi ảnh đại diện. Mọi phép kiểm an toàn nằm ở `model/useAvatar.ts`. */
import { useId, useRef, useState } from 'react';
import { UserAvatar } from '@/entities/user';
import { AnhKhongHopLe, useAvatar } from '../model/useAvatar';

export interface AvatarPickerProps {
  name: string | null;
  size?: number;
}

export function AvatarPicker({ name, size = 96 }: AvatarPickerProps) {
  const { avatar, doiAvatar, xoaAvatar } = useAvatar();
  const [loi, setLoi] = useState<string | null>(null);
  const [dangXuLy, setDangXuLy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const idInput = useId();

  const chon = async (file: File | undefined) => {
    if (!file) return;
    setLoi(null);
    setDangXuLy(true);
    try {
      await doiAvatar(file);
    } catch (err) {
      // Câu của `AnhKhongHopLe` viết sẵn cho người dùng đọc; lỗi lạ thì nói chung chung
      // chứ KHÔNG đổ nguyên thông báo kỹ thuật ra màn hình.
      setLoi(
        err instanceof AnhKhongHopLe ? err.message : 'Không xử lý được ảnh này.',
      );
    } finally {
      setDangXuLy(false);
      // Xoá giá trị input để chọn LẠI ĐÚNG file vừa rồi vẫn kích hoạt `onChange`.
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  return (
    <div className="avatar-picker">
      <UserAvatar name={name} src={avatar} size={size} />

      <div className="avatar-picker__actions">
        {/* Nút thật là <label>: input file mặc định của trình duyệt không tạo kiểu được. */}
        <label className="btn btn--sm" htmlFor={idInput}>
          {dangXuLy ? 'Đang xử lý…' : avatar ? 'Đổi ảnh' : 'Tải ảnh lên'}
        </label>
        <input
          ref={inputRef}
          id={idInput}
          className="sr-only"
          type="file"
          // `accept` chỉ LỌC HỘP THOẠI cho tiện, KHÔNG phải phép kiểm bảo mật: người dùng
          // đổi được sang "All files" trong hộp thoại của hệ điều hành. Phần kiểm thật
          // nằm ở `useAvatar` (MIME + số ma thuật + vẽ lại qua canvas).
          accept="image/png,image/jpeg,image/webp"
          onChange={(event) => void chon(event.target.files?.[0])}
        />

        {avatar && (
          <button type="button" className="linkish" onClick={xoaAvatar}>
            Dùng ảnh mặc định
          </button>
        )}
      </div>

      <p className="avatar-picker__hint">
        PNG, JPG hoặc WEBP, tối đa 2 MB. Ảnh chỉ lưu trên máy bạn, không gửi lên máy chủ.
      </p>

      {loi && (
        <p className="auth-card__error" role="alert">
          {loi}
        </p>
      )}
    </div>
  );
}
