/**
 * Quy tắc ĐỔI NGUỒN ảnh nền bản đồ (2026-10-02): máy chủ dự án bị DNS chặn
 * `tile.openstreetmap.org` -> bản đồ nền xám. Đổi nguồn khi nguồn chính hỏng HẲN, không đổi
 * vì vài ảnh lỗi lẻ tẻ.
 */
import { describe, expect, it } from 'vitest';
import { NGUON_NEN, SO_ANH_LOI_DE_DOI_NGUON, nguonTiepTheo } from './NenBanDo';

describe('nguonTiepTheo', () => {
  it('đủ số ảnh lỗi mà chưa ảnh nào tải được -> sang nguồn dự phòng', () => {
    expect(nguonTiepTheo(0, SO_ANH_LOI_DE_DOI_NGUON, 0)).toBe(1);
  });

  it('chưa đủ số ảnh lỗi -> giữ nguồn chính', () => {
    expect(nguonTiepTheo(0, SO_ANH_LOI_DE_DOI_NGUON - 1, 0)).toBe(0);
  });

  it('ĐÃ có ảnh tải được thì lỗi lẻ tẻ không làm đổi nguồn', () => {
    expect(nguonTiepTheo(0, 50, 1)).toBe(0);
  });

  it('hết nguồn dự phòng thì đứng yên, không quay vòng', () => {
    const cuoi = NGUON_NEN.length - 1;
    expect(nguonTiepTheo(cuoi, 99, 0)).toBe(cuoi);
  });

  it('mọi nguồn đều ghi công OpenStreetMap (bắt buộc theo ODbL)', () => {
    for (const n of NGUON_NEN) expect(n.attribution).toMatch(/OpenStreetMap/);
  });
});
