/**
 * ẢNH NỀN BẢN ĐỒ dùng chung cho mọi bản đồ Leaflet - có NGUỒN DỰ PHÒNG.
 *
 * VÌ SAO (đo thật 2026-10-02): trên máy chủ dự án, DNS trả `tile.openstreetmap.org` về
 * 127.0.0.1 (bộ lọc DNS của mạng/router chặn đúng máy chủ ảnh nền OSM). Bản đồ vẫn có
 * ghim, có nút zoom, nhưng nền XÁM TRƠN - và chẳng có gì báo lỗi. Mang đúng mạng đó đi
 * bảo vệ là hội đồng nhìn thấy một ô xám.
 *
 * Cách làm: dùng nguồn chính, nếu vài ảnh ĐẦU TIÊN đều lỗi mà chưa ảnh nào tải được thì
 * chuyển sang nguồn kế tiếp. Chỉ xét lúc chưa có ảnh nào tải được: mạng chập chờn làm hỏng
 * lẻ tẻ vài ảnh giữa chừng không phải lý do để đổi cả nguồn.
 *
 * Cả hai nguồn đều MIỄN PHÍ, KHÔNG cần key/thẻ (CLAUDE.md mục 1b) và đều là dữ liệu
 * OpenStreetMap - ghi công theo giấy phép ODbL là BẮT BUỘC, nên `attribution` đi theo nguồn.
 */
import { useRef, useState } from 'react';
import { TileLayer } from 'react-leaflet';

export interface NguonNen {
  ten: string;
  url: string;
  attribution: string;
}

const GHI_CONG_OSM =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

export const NGUON_NEN: readonly NguonNen[] = [
  {
    // Không dùng `{s}.tile...`: OSM đã khuyến nghị bỏ tên miền phụ a/b/c.
    ten: 'OpenStreetMap',
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: GHI_CONG_OSM,
  },
  {
    // Đo 2026-10-02 trên đúng mạng chặn OSM: trả ảnh thật (~23 KB). CARTO cũng trả 200
    // nhưng ảnh chỉ 2 KB (nghi ảnh trống) nên không chọn.
    ten: 'OpenStreetMap France',
    url: 'https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png',
    attribution: `${GHI_CONG_OSM} · nền: <a href="https://www.openstreetmap.fr/">OpenStreetMap France</a>`,
  },
];

// Số ảnh lỗi LIÊN TIẾP từ đầu (chưa ảnh nào tải được) thì coi nguồn là hỏng. Một khung
// bản đồ tải ~9-12 ảnh cùng lúc; 4 ảnh đều lỗi đủ chắc là cả nguồn bị chặn, mà vẫn đổi
// kịp trước khi người dùng nhận ra.
export const SO_ANH_LOI_DE_DOI_NGUON = 4;

/** Thuần, để test được: đang dùng nguồn `chiSo`, đã lỗi `soLoi` ảnh, tải được `soTai` ảnh. */
export function nguonTiepTheo(chiSo: number, soLoi: number, soTai: number): number {
  const conNguonKhac = chiSo < NGUON_NEN.length - 1;
  return soTai === 0 && soLoi >= SO_ANH_LOI_DE_DOI_NGUON && conNguonKhac ? chiSo + 1 : chiSo;
}

export function NenBanDo() {
  const [chiSo, setChiSo] = useState(0);
  // Ref chứ không phải state: đếm theo từng ảnh, không cần vẽ lại mỗi lần đếm.
  const dem = useRef({ loi: 0, tai: 0 });
  const nguon = NGUON_NEN[chiSo];

  return (
    <TileLayer
      // Đổi `key` = dựng lại lớp ảnh nền với URL mới, bộ đếm cũng làm lại từ đầu.
      key={nguon.url}
      url={nguon.url}
      attribution={nguon.attribution}
      eventHandlers={{
        tileload: () => {
          dem.current.tai += 1;
        },
        tileerror: () => {
          dem.current.loi += 1;
          const ke = nguonTiepTheo(chiSo, dem.current.loi, dem.current.tai);
          if (ke !== chiSo) {
            dem.current = { loi: 0, tai: 0 };
            setChiSo(ke);
          }
        },
      }}
    />
  );
}
