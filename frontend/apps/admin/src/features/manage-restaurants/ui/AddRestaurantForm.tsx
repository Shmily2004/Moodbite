/**
 * Form THÊM QUÁN MỚI bằng tay.
 *
 * VÌ SAO ĐÁNG LÀM: đây là con đường bổ sung dữ liệu miễn phí và chất lượng cao nhất còn
 * lại — người thật tới tận nơi hoặc gọi điện xác minh. Overture/OSM cho số lượng nhưng
 * không có giá, giờ mở cửa, đánh giá; Apify thì tốn tiền.
 *
 * ⚠️ FORM ĐÓNG SẴN. Việc thường xuyên nhất ở trang này là TÌM và SỬA quán đã có; mở sẵn
 * một form 9 ô sẽ đẩy danh sách xuống dưới màn hình mỗi lần vào trang.
 *
 * ⚠️ KHÔNG CÓ Ô NHẬP ĐÁNH GIÁ / SỐ REVIEW, cố ý. Chúng đến từ nguồn thu thập; gõ tay vào
 * là làm sai lệch chính những con số dùng để xếp hạng (CLAUDE.md mục 4). Backend cũng
 * không nhận hai trường đó — form chỉ đang nói đúng sự thật đó ra.
 *
 * ⚠️ LUẬT KIỂM TRA NẰM Ở BACKEND (`domain/value_objects/restaurant_new.py`), không chép
 * xuống đây. Ô toạ độ chỉ ghi CHÚ THÍCH về phạm vi Hà Nội để người nhập biết trước; còn
 * việc từ chối là do server. Hai bản luật sẽ có ngày lệch nhau.
 */
import { useState } from 'react';
import type { FormEvent } from 'react';
import type { AdminCreateRestaurantRequest } from '@moodbite/api-client';

export interface AddRestaurantFormProps {
  onCreate: (body: AdminCreateRestaurantRequest) => Promise<boolean>;
}

/** Trạng thái rỗng của form. Tách ra để "dọn form sau khi lưu" chỉ có một nguồn. */
const RONG = {
  name: '',
  lat: '',
  lng: '',
  category: '',
  cuisine: '',
  address: '',
  district: '',
  price: '',
  phone: '',
  website: '',
};

export function AddRestaurantForm({ onCreate }: AddRestaurantFormProps) {
  const [mo, setMo] = useState(false);
  const [form, setForm] = useState({ ...RONG });
  const [dangGui, setDangGui] = useState(false);

  const dat = (khoa: keyof typeof RONG) => (su_kien: { target: { value: string } }) =>
    setForm((cu) => ({ ...cu, [khoa]: su_kien.target.value }));

  const gui = async (su_kien: FormEvent) => {
    su_kien.preventDefault();
    setDangGui(true);
    try {
      // Ô để trống -> KHÔNG gửi trường đó lên (thay vì gửi chuỗi rỗng). "Chưa có dữ
      // liệu" và "dữ liệu là chuỗi rỗng" là hai chuyện khác nhau, và cột rỗng trong CSDL
      // phải là NULL.
      const body: Record<string, unknown> = {
        name: form.name.trim(),
        lat: Number(form.lat),
        lng: Number(form.lng),
      };
      for (const khoa of [
        'category', 'cuisine', 'address', 'district', 'price', 'phone', 'website',
      ] as const) {
        const gia_tri = form[khoa].trim();
        if (gia_tri) body[khoa] = gia_tri;
      }

      const xong = await onCreate(body as AdminCreateRestaurantRequest);
      if (xong) {
        setForm({ ...RONG });
        setMo(false);
      }
    } finally {
      setDangGui(false);
    }
  };

  if (!mo) {
    return (
      <button type="button" className="btn" onClick={() => setMo(true)}>
        + Thêm quán mới
      </button>
    );
  }

  const thieu = form.name.trim() === '' || form.lat === '' || form.lng === '';

  return (
    <form className="addform" onSubmit={gui}>
      <div className="addform__head">
        <h3>Thêm quán mới</h3>
        <button type="button" className="linkish" onClick={() => setMo(false)}>
          Đóng
        </button>
      </div>

      <div className="addform__grid">
        <label>
          <span>Tên quán *</span>
          <input value={form.name} onChange={dat('name')} required />
        </label>
        <label>
          <span>Vĩ độ (lat) *</span>
          <input
            value={form.lat}
            onChange={dat('lat')}
            inputMode="decimal"
            placeholder="21.0285"
            required
          />
        </label>
        <label>
          <span>Kinh độ (lng) *</span>
          <input
            value={form.lng}
            onChange={dat('lng')}
            inputMode="decimal"
            placeholder="105.8542"
            required
          />
        </label>
        <label>
          <span>Loại hình</span>
          <input value={form.category} onChange={dat('category')} placeholder="Nhà hàng" />
        </label>
        <label>
          <span>Ẩm thực</span>
          <input value={form.cuisine} onChange={dat('cuisine')} placeholder="Việt Nam" />
        </label>
        <label>
          <span>Địa chỉ</span>
          <input value={form.address} onChange={dat('address')} />
        </label>
        <label>
          <span>Phường / quận</span>
          <input value={form.district} onChange={dat('district')} />
        </label>
        <label>
          {/* Giá là CHUỖI khoảng giá, KHÔNG phải số — ép về số làm hỏng response.
              Đây là bug đã từng xảy ra, nên placeholder nói rõ định dạng mong đợi. */}
          <span>Giá (chuỗi)</span>
          <input value={form.price} onChange={dat('price')} placeholder="30-60.000 ₫" />
        </label>
        <label>
          <span>Điện thoại</span>
          <input value={form.phone} onChange={dat('phone')} />
        </label>
        <label>
          <span>Website</span>
          <input value={form.website} onChange={dat('website')} />
        </label>
      </div>

      <p className="muted small">
        Toạ độ phải nằm trong Hà Nội (20.85–21.40 vĩ độ, 105.70–106.05 kinh độ) — phạm vi
        dữ liệu của dự án. Lấy toạ độ nhanh: mở Google Maps, bấm chuột phải vào vị trí
        quán, số đầu là vĩ độ. Ô để trống nghĩa là <strong>chưa có dữ liệu</strong>, không
        phải giá trị rỗng.
      </p>

      <button type="submit" className="btn btn--primary" disabled={dangGui || thieu}>
        {dangGui ? 'Đang lưu…' : 'Lưu quán mới'}
      </button>
    </form>
  );
}
