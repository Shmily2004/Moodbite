/**
 * VIEWMODEL của ngăn kéo bộ lọc ở trang chi tiết món.
 *
 * ⚠️ LỖI THẬT, sửa 2026-09-16: bấm "Chỉnh sửa" mở ra một ngăn kéo RỖNG (chỉ có một câu
 * chữ), và "Xem kết quả" nhảy sang `/recommend` TRẮNG TRƠN — mọi điều kiện người dùng
 * đang có đều rơi mất. Nguyên nhân: state bộ lọc dính chung với lượt gọi API trong
 * `useDishSuggestions`, nên trang này không có state nào để hiện hay để mang đi.
 *
 * Nay:
 *   1. Bộ lọc BAN ĐẦU = điều kiện trên URL (đi từ trang gợi ý sang), còn nếu URL không có
 *      điều kiện nào thì suy từ chính món đang xem (Nóng · Nướng) — xem `boLocTuMon`.
 *   2. "Xem kết quả" -> `/recommend?<bộ lọc>` qua đúng `ghiBoLocLenUrl` mà trang đó đọc.
 *
 * Hook này chỉ được gọi khi ngăn kéo ĐANG MỞ (component chứa nó mount lúc mở): bộ lọc ban
 * đầu phải tính từ món ĐÃ TẢI XONG, mà `useState` chỉ đọc giá trị khởi tạo đúng một lần.
 */
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { DishItem } from '@/shared/api';
import {
  boLocTuMon,
  docBoLocTuUrl,
  ghiBoLocLenUrl,
  urlCoBoLoc,
  useDishFilterState,
} from '@/features/suggest-dishes';
import type { UseDishFilterStateResult } from '@/features/suggest-dishes';
import { ROUTES } from '@/shared/config';

export interface UseDishFilterPanelResult extends UseDishFilterStateResult {
  apply: () => void;
}

export function useDishFilterPanel(dish: DishItem | null): UseDishFilterPanelResult {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();

  const tuUrl = docBoLocTuUrl(params);
  // Bán kính trên URL luôn được giữ; phần ĐIỀU KIỆN thì URL thắng, không có mới lấy từ món.
  const banDau = urlCoBoLoc(params) ? tuUrl : { ...boLocTuMon(dish), ...tuUrl };
  const boLoc = useDishFilterState(banDau);

  const apply = () =>
    navigate({
      pathname: ROUTES.recommend,
      search: ghiBoLocLenUrl(boLoc.filters).toString(),
    });

  /**
   * Công tắc "chỉ quán có ghi giá" áp NGAY TẠI TRANG NÀY, khác mọi ô lọc còn lại.
   *
   * Không phải sự thiếu nhất quán vô cớ — hai thứ khác nhau về bản chất:
   *   - Các ô lọc khác chọn XEM MÓN NÀO, mà trang này đã khoá vào một món rồi; chúng chỉ
   *     có nghĩa khi sang `/recommend`, nên vẫn đợi nút "Xem kết quả".
   *   - Công tắc giá lọc DANH SÁCH QUÁN đang hiện ngay dưới tay người dùng. Bắt họ bấm
   *     "Xem kết quả" để rồi bị đẩy sang một trang KHÁC (lưới món) là không đưa họ tới
   *     thứ họ vừa yêu cầu.
   *
   * Ghi vào URL chứ không giữ trong state: trang chi tiết món đọc `gia=1` từ URL để gọi
   * API (xem `DishPage`). URL là nguồn sự thật duy nhất, nên không có hai bản lệch nhau,
   * và nút Back vẫn đúng.
   */
  const setOnlyWithPrice = (value: boolean) => {
    boLoc.setOnlyWithPrice(value);
    const moi = new URLSearchParams(params);
    if (value) moi.set('gia', '1');
    else moi.delete('gia');
    setParams(moi, { replace: true });
  };

  return { ...boLoc, setOnlyWithPrice, apply };
}
