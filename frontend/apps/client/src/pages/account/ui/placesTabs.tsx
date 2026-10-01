/**
 * Ba tab dùng tính năng mới (duyệt 2026-09-29): "Bộ sưu tập của tôi", "Địa chỉ của tôi",
 * và tab Yêu thích có thêm ô "Thêm vào bộ sưu tập".
 *
 * VÌ SAO HOOK ĐƯỢC GỌI Ở ĐÂY chứ không ở `AccountPage`: gọi ở trang thì mỗi lần mở trang
 * tài khoản — kể cả tab Tổng quan — đều tốn thêm hai lượt gọi API không ai xem. Mỗi tab tự
 * gọi hook của mình và chỉ chạy khi đang mở.
 *
 * GHÉP HAI FEATURE Ở TẦNG TRANG: `save-favorite` (thẻ đã lưu) và `manage-collections` (ô
 * thêm vào bộ) không được import nhau theo FSD — trang là nơi duy nhất được biết cả hai.
 */
import { AddToCollection, CollectionsPanel, useCollections } from '@/features/manage-collections';
import { AddressesPanel, useAddressForm, useAddresses } from '@/features/manage-addresses';
import type { UseFavoritesResult } from '@/features/save-favorite';
import type { AnhMon } from '@/entities/dish';
import { SavedTab } from './savedTabs';

export function CollectionsTab() {
  const boSuuTap = useCollections();
  return <CollectionsPanel boSuuTap={boSuuTap} />;
}

export function AddressesTab() {
  const diaChi = useAddresses();
  const form = useAddressForm();
  return <AddressesPanel diaChi={diaChi} form={form} />;
}

export function SavedTabWithCollections(props: { favorites: UseFavoritesResult; anh: AnhMon }) {
  const boSuuTap = useCollections();
  return (
    <SavedTab
      favorites={props.favorites}
      anh={props.anh}
      renderFooter={(muc) => (
        <AddToCollection
          boSuuTap={boSuuTap}
          muc={{ itemType: muc.itemType, itemId: muc.itemId, name: muc.name }}
        />
      )}
    />
  );
}
