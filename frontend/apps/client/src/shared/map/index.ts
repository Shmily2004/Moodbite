/**
 * Segment RIÊNG cho thứ dính tới Leaflet, KHÔNG gộp vào `shared/ui`: barrel `shared/ui`
 * được import ở gần như mọi trang, gộp vào đó là kéo `react-leaflet` vào file JS chính và
 * phá mất việc tách code (2026-10-02: 532 kB -> 313 kB nhờ để Leaflet tải sau).
 */
export { NenBanDo, NGUON_NEN, nguonTiepTheo, SO_ANH_LOI_DE_DOI_NGUON } from './NenBanDo';
export type { NguonNen } from './NenBanDo';
