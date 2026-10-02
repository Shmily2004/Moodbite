/**
 * Trạng thái cuộn NGANG của dải thẻ món (thêm 2026-10-02, theo `design/Home.jpg` có nút ›
 * ở mép phải dải món).
 *
 * VÌ SAO CẦN NÚT dù dải đã vuốt được: trên máy tính dùng chuột thường, KHÔNG có cử chỉ
 * cuộn ngang — người dùng thấy thẻ thứ năm bị cắt ở mép mà không biết làm sao xem tiếp.
 *
 * Chỉ báo `tranTrai`/`tranPhai` khi THẬT SỰ còn nội dung bị khuất. Dải vừa khít màn hình
 * thì không vẽ nút nào — một nút bấm không làm gì là nút chết.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

/** Mỗi lần bấm cuộn ~80% bề rộng đang thấy: chừa lại một phần thẻ cũ để mắt còn bám được. */
const TI_LE_MOI_LAN_CUON = 0.8;

export function useHorizontalScroll<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [tranTrai, setTranTrai] = useState(false);
  const [tranPhai, setTranPhai] = useState(false);

  const doLai = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    // Sai số 1px: trình duyệt làm tròn `scrollLeft` theo pixel thiết bị.
    setTranTrai(el.scrollLeft > 1);
    setTranPhai(el.scrollLeft + el.clientWidth < el.scrollWidth - 1);
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    doLai();
    el.addEventListener('scroll', doLai, { passive: true });
    // `ResizeObserver` không có trong jsdom và vài trình duyệt cũ -> lui về sự kiện resize.
    const quanSat =
      typeof ResizeObserver !== 'undefined' ? new ResizeObserver(doLai) : null;
    quanSat?.observe(el);
    window.addEventListener('resize', doLai);
    return () => {
      el.removeEventListener('scroll', doLai);
      quanSat?.disconnect();
      window.removeEventListener('resize', doLai);
    };
  }, [doLai]);

  const cuon = useCallback((huong: -1 | 1) => {
    const el = ref.current;
    if (!el) return;
    const giamChuyenDong =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollBy?.({
      left: huong * el.clientWidth * TI_LE_MOI_LAN_CUON,
      behavior: giamChuyenDong ? 'auto' : 'smooth',
    });
  }, []);

  return { ref, tranTrai, tranPhai, cuon, doLai };
}
