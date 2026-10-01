/**
 * Gọi API "Bộ sưu tập của tôi" và đổi sang kiểu camelCase của giao diện.
 *
 * Đổi tên trường Ở ĐÂY, một lần: backend nói `snake_case` (CLAUDE.md mục 5), còn phần
 * còn lại của frontend quen `itemType`/`itemId` như `features/save-favorite`.
 */
import { myPlacesApi } from '@/shared/api';
import type { CollectionData } from '@/shared/api';

export type LoaiMuc = 'restaurant' | 'dish';

export interface MucBoSuuTap {
  itemType: LoaiMuc;
  itemId: string;
  name: string;
}

export interface BoSuuTap {
  id: string;
  name: string;
  itemCount: number;
  items: MucBoSuuTap[];
}

export function tuApi(bo: CollectionData): BoSuuTap {
  const items = (bo.items ?? []).map((m) => ({
    itemType: m.item_type as LoaiMuc,
    itemId: m.item_id,
    name: m.name,
  }));
  return { id: bo.collection_id, name: bo.name, itemCount: bo.item_count, items };
}

export async function taiBoSuuTap(): Promise<BoSuuTap[]> {
  const data = await myPlacesApi.collections();
  // `?? []`: phản hồi thiếu trường không được làm sập tab.
  return (data.collections ?? []).map(tuApi);
}

export async function taoBoSuuTap(name: string): Promise<BoSuuTap> {
  return tuApi(await myPlacesApi.createCollection(name));
}

export async function doiTenBoSuuTap(id: string, name: string): Promise<BoSuuTap> {
  return tuApi(await myPlacesApi.renameCollection(id, name));
}

export async function xoaBoSuuTap(id: string): Promise<void> {
  await myPlacesApi.deleteCollection(id);
}

export async function themVaoBoSuuTap(id: string, muc: MucBoSuuTap): Promise<BoSuuTap> {
  return tuApi(
    await myPlacesApi.addCollectionItem(id, {
      item_type: muc.itemType,
      item_id: muc.itemId,
      name: muc.name,
    }),
  );
}

export async function boKhoiBoSuuTap(id: string, itemType: LoaiMuc, itemId: string) {
  await myPlacesApi.removeCollectionItem(id, itemType, itemId);
}
