/**
 * VIEWMODEL của trang `/recommend` — giữ state + điều phối, KHÔNG có JSX.
 *
 * Tách khỏi `RecommendPage.tsx` (2026-09-16) khi trang chuyển sang bố cục cột lọc bên trái
 * theo `design/Filler.png`: phần điều phối (URL, sắp xếp, lưu món) cộng phần JSX đã vượt
 * xa ngưỡng ~300 dòng một file.
 *
 * BỘ LỌC NẰM TRÊN URL — xem `features/suggest-dishes/model/boLocTuUrl.ts`.
 */
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { DishItem } from '@/shared/api';
import type { ChipDangBat } from '@/features/suggest-dishes';
import {
  chipDangBat,
  docBoLocTuUrl,
  ghiBoLocLenUrl,
  useDishSuggestions,
} from '@/features/suggest-dishes';
import { useUserLocation } from '@/features/pick-location';
import { useFavorites } from '@/features/save-favorite';
import type { LoaiDanhSach } from '@/features/save-favorite';
import { useUserSessionContext } from '@/entities/user';
import { DEFAULT_RADIUS_KM, dishRoute } from '@/shared/config';
import { useT } from '@/shared/i18n';
import { sapXepMon } from './sapXepMon';
import type { KieuSapXepMon } from './sapXepMon';

/**
 * Số món hiện lúc đầu: 3 hàng của lưới 3 cột.
 *
 * Chủ dự án từng chê trang này "đang hiển thị quá nhiều" (2026-08-26) khi 30 món đổ ra một
 * lượt. Lưới theo `Filler.png` giữ lại, nhưng cắt ở 9 món kèm nút "Xem thêm N món" — cùng
 * cách trang chi tiết món cắt danh sách quán.
 */
export const SO_MON_BAN_DAU = 9;

export function useRecommendPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useUserLocation();
  const session = useUserSessionContext();
  const t = useT();

  // Đọc bộ lọc từ URL đúng MỘT LẦN lúc dựng. Sau đó state trong hook là nguồn sự thật;
  // đọc lại mỗi lần URL đổi sẽ ghi đè thứ người dùng vừa bấm.
  const [boLocBanDau] = useState(() => docBoLocTuUrl(searchParams));
  const suggestions = useDishSuggestions(location.position, boLocBanDau);
  const savedDishes = useFavorites();
  const [moBoLoc, setMoBoLoc] = useState(false);
  const [sapXep, setSapXep] = useState<KieuSapXepMon>('phu-hop');
  const [xemHet, setXemHet] = useState(false);

  // Bộ lọc đổi -> ghi ngược lên URL. `replace` để mỗi lần bấm chip KHÔNG tạo một mục mới
  // trong lịch sử: bấm 5 chip rồi phải bấm Back 5 lần mới ra khỏi trang là rất khó chịu.
  useEffect(() => {
    setSearchParams(ghiBoLocLenUrl(suggestions.filters), { replace: true });
  }, [suggestions.filters, setSearchParams]);

  const dishes = useMemo(
    () => sapXepMon(suggestions.dishes ?? [], sapXep),
    [suggestions.dishes, sapXep],
  );
  const monHien = xemHet ? dishes : dishes.slice(0, SO_MON_BAN_DAU);

  const chips = chipDangBat(suggestions.filters, t);
  const goChip = (chip: ChipDangBat) => {
    if (chip.nhomNhieu) suggestions.toggle(chip.nhomNhieu, chip.giaTri);
    else if (chip.nhomMot) suggestions.setSingle(chip.nhomMot, null);
    // Gỡ chip bán kính = về MẶC ĐỊNH (xem `ChipDangBat.khoangCach`).
    else if (chip.khoangCach) suggestions.setMaxDistanceKm(DEFAULT_RADIUS_KM);
    else if (chip.chiCoGia) suggestions.setOnlyWithPrice(false);
  };

  // Sang trang món MANG THEO bộ lọc: nút "Chỉnh sửa" ở đó mở lại đúng những gì đang chọn.
  const moMon = (dish: DishItem) =>
    navigate({
      pathname: dishRoute(dish.dish_id),
      search: ghiBoLocLenUrl(suggestions.filters).toString(),
    });

  // HAI danh sách tách bạch: trái tim ("Món yêu thích") và dấu trang ("Đã lưu").
  const daLuu = (dish: DishItem, listType: LoaiDanhSach) =>
    savedDishes.isSaved('dish', dish.dish_id, listType);
  const doiLuu = (dish: DishItem, listType: LoaiDanhSach) =>
    savedDishes.toggle({ itemType: 'dish', itemId: dish.dish_id, name: dish.name, listType });

  const keoToiKetQua = () =>
    document.getElementById('ket-qua')?.scrollIntoView({ behavior: 'smooth', block: 'start' });

  return {
    location,
    suggestions,
    savedDishes,
    daDangNhap: session.isLoggedIn,
    tongSoMon: dishes.length,
    monHien,
    conLai: dishes.length - monHien.length,
    xemThem: () => setXemHet(true),
    sapXep,
    setSapXep,
    chips,
    goChip,
    moMon,
    daLuu,
    doiLuu,
    moBoLoc,
    setMoBoLoc,
    keoToiKetQua,
  };
}

export type UseRecommendPageResult = ReturnType<typeof useRecommendPage>;
