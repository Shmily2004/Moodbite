/** VIEW: đổi ảnh đại diện. Mọi phép kiểm an toàn nằm ở `model/useAvatar.ts`. */
import { useId, useRef, useState } from 'react';
import { UserAvatar } from '@/entities/user';
import { IconCamera } from '@/shared/ui';
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

  const goiY = 'PNG, JPG hoặc WEBP, tối đa 2 MB. Ảnh chỉ lưu trên máy bạn, không gửi lên máy chủ.';
  const nhanNut = dangXuLy ? 'Đang xử lý…' : avatar ? 'Đổi ảnh đại diện' : 'Tải ảnh đại diện lên';

  return (
    <div className="avatar-picker">
      {/*
        NÚT MÁY ẢNH ĐÈ LÊN GÓC ẢNH (2026-10-02, như `design/profile.png`), thay cho nút
        chữ + đoạn giải thích 4 dòng nằm dưới ảnh. Lời giải thích KHÔNG mất: nó là
        `title` (rê chuột) và là mô tả của ô chọn file (`aria-describedby`) cho trình đọc
        màn hình.

        Ô <input type="file"> đứng TRƯỚC nhãn để CSS `input:focus-visible + label` vẽ được
        vòng tiêu điểm lên nút máy ảnh khi người dùng Tab tới (ô thật bị ẩn bằng mắt).
      */}
      <div className="avatar-picker__khung">
        <UserAvatar name={name} src={avatar} size={size} />
        <input
          ref={inputRef}
          id={idInput}
          className="sr-only"
          type="file"
          // `accept` chỉ LỌC HỘP THOẠI cho tiện, KHÔNG phải phép kiểm bảo mật: người dùng
          // đổi được sang "All files" trong hộp thoại của hệ điều hành. Phần kiểm thật
          // nằm ở `useAvatar` (MIME + số ma thuật + vẽ lại qua canvas).
          accept="image/png,image/jpeg,image/webp"
          aria-describedby={`${idInput}-goi-y`}
          disabled={dangXuLy}
          onChange={(event) => void chon(event.target.files?.[0])}
        />
        {/* Nút thật là <label>: input file mặc định của trình duyệt không tạo kiểu được. */}
        <label className="avatar-picker__cam" htmlFor={idInput} title={goiY}>
          <IconCamera />
          <span className="sr-only">{nhanNut}</span>
        </label>
      </div>

      <p id={`${idInput}-goi-y`} className="sr-only">
        {goiY}
      </p>

      {avatar && (
        <button type="button" className="linkish avatar-picker__mac-dinh" onClick={xoaAvatar}>
          Dùng ảnh mặc định
        </button>
      )}

      {loi && (
        <p className="auth-card__error" role="alert">
          {loi}
        </p>
      )}
    </div>
  );
}
