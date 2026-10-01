/**
 * Ô "Thêm vào bộ sưu tập" gắn dưới mỗi thẻ ở tab Yêu thích.
 *
 * Gọn: một nút mở ra ô chọn bộ + nút Thêm. Chọn "+ Bộ sưu tập mới" thì hiện ô gõ tên —
 * người dùng không phải rời tab để đi tạo bộ trước.
 *
 * Chỉ JSX + state giao diện; thao tác dữ liệu đi qua `UseCollectionsResult`.
 */
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useT } from '@/shared/i18n';
import { IconFolder } from '@/shared/ui';
import type { UseCollectionsResult } from '../model/useCollections';
import type { MucBoSuuTap } from '../api/collectionsApi';

const BO_MOI = '__moi__';

export interface AddToCollectionProps {
  boSuuTap: UseCollectionsResult;
  muc: MucBoSuuTap;
}

export function AddToCollection({ boSuuTap, muc }: AddToCollectionProps) {
  const t = useT();
  const [mo, setMo] = useState(false);
  const [chon, setChon] = useState<string>(BO_MOI);
  const [tenMoi, setTenMoi] = useState('');
  const [daThem, setDaThem] = useState<string | null>(null);

  if (!mo) {
    return (
      <button
        type="button"
        className="linkish bst-add__open"
        onClick={() => {
          // Chọn sẵn LÚC MỞ (không phải lúc dựng): danh sách bộ có thể tải xong sau khi
          // thẻ đã hiện. Chưa có bộ nào thì mặc định "bộ mới" — không bắt chọn ô rỗng.
          setChon(boSuuTap.collections[0]?.id ?? BO_MOI);
          setMo(true);
        }}
      >
        <IconFolder /> {t('collections.addTo')}
      </button>
    );
  }

  const gui = async (e: FormEvent) => {
    e.preventDefault();
    setDaThem(null);
    if (chon === BO_MOI) {
      const ten = tenMoi;
      if (await boSuuTap.createAndAdd(ten, muc)) {
        setDaThem(ten.trim());
        setTenMoi('');
      }
      return;
    }
    const bo = boSuuTap.collections.find((x) => x.id === chon);
    if (bo && (await boSuuTap.addItem(bo.id, muc))) setDaThem(bo.name);
  };

  return (
    <form className="bst-add" onSubmit={(e) => void gui(e)}>
      <select
        className="mp-input"
        value={chon}
        onChange={(e) => setChon(e.target.value)}
        aria-label={t('collections.pick')}
      >
        {boSuuTap.collections.map((bo) => (
          <option key={bo.id} value={bo.id}>
            {bo.name}
          </option>
        ))}
        <option value={BO_MOI}>{t('collections.newOption')}</option>
      </select>
      {chon === BO_MOI && (
        <input
          className="mp-input"
          value={tenMoi}
          onChange={(e) => setTenMoi(e.target.value)}
          placeholder={t('collections.newPlaceholder')}
          aria-label={t('collections.newPlaceholder')}
        />
      )}
      <button
        type="submit"
        className="btn btn--sm"
        disabled={boSuuTap.busy || (chon === BO_MOI && tenMoi.trim() === '')}
      >
        {t('collections.add')}
      </button>
      {daThem && (
        <span className="muted small" role="status">
          {t('collections.added', { name: daThem })}
        </span>
      )}
    </form>
  );
}
