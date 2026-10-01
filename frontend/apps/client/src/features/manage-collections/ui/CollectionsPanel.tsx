/**
 * VIEW tab "Bộ sưu tập của tôi" (design/profile.png, mục thanh bên).
 *
 * Chỉ JSX + state GIAO DIỆN (ô đang gõ, bộ nào đang mở, bộ nào đang hỏi xác nhận xoá).
 * Mọi thao tác dữ liệu đi qua `UseCollectionsResult` do trang truyền vào.
 *
 * Quán KHÔNG có link: quán chưa có trang riêng (chi tiết nằm trong trang bản đồ) — cùng
 * quyết định với thẻ ở tab Yêu thích. Link chết tệ hơn không có link.
 */
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { IconClose, IconDining, IconFolder, IconPin } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { dishRoute } from '@/shared/config';
import type { UseCollectionsResult } from '../model/useCollections';
import type { BoSuuTap } from '../api/collectionsApi';

export interface CollectionsPanelProps {
  boSuuTap: UseCollectionsResult;
}

export function CollectionsPanel({ boSuuTap }: CollectionsPanelProps) {
  const t = useT();
  const [tenMoi, setTenMoi] = useState('');

  const tao = async (e: FormEvent) => {
    e.preventDefault();
    // Không tự kiểm độ dài ở đây: luật nằm ở backend, câu lỗi của server hiện nguyên văn.
    const bo = await boSuuTap.create(tenMoi);
    if (bo) setTenMoi('');
  };

  return (
    <section className="panel">
      <div className="results__head">
        <h2 className="panel__title">
          <IconFolder /> {t('collections.title')}
        </h2>
      </div>
      <p className="section-sub">{t('collections.sub')}</p>

      <form className="bst-form" onSubmit={(e) => void tao(e)}>
        <input
          className="mp-input"
          value={tenMoi}
          onChange={(e) => setTenMoi(e.target.value)}
          placeholder={t('collections.newPlaceholder')}
          aria-label={t('collections.newPlaceholder')}
        />
        <button
          type="submit"
          className="btn btn--primary"
          disabled={boSuuTap.busy || tenMoi.trim() === ''}
        >
          {t('collections.create')}
        </button>
      </form>

      {boSuuTap.error && (
        <p className="notice notice--error" role="alert">
          {boSuuTap.error}
        </p>
      )}

      {!boSuuTap.loading && boSuuTap.collections.length === 0 ? (
        <p className="section-sub">{t('collections.empty')}</p>
      ) : (
        <ul className="bst-list">
          {boSuuTap.collections.map((bo) => (
            <MotBo key={bo.id} bo={bo} boSuuTap={boSuuTap} />
          ))}
        </ul>
      )}
    </section>
  );
}

function MotBo({ bo, boSuuTap }: { bo: BoSuuTap; boSuuTap: UseCollectionsResult }) {
  const t = useT();
  const [mo, setMo] = useState(false);
  const [dangSua, setDangSua] = useState(false);
  const [tenSua, setTenSua] = useState(bo.name);
  const [hoiXoa, setHoiXoa] = useState(false);

  const luuTen = async (e: FormEvent) => {
    e.preventDefault();
    if (await boSuuTap.rename(bo.id, tenSua)) setDangSua(false);
  };

  return (
    <li className="bst-item">
      <div className="bst-item__head">
        {dangSua ? (
          <form className="bst-form" onSubmit={(e) => void luuTen(e)}>
            <input
              className="mp-input"
              value={tenSua}
              onChange={(e) => setTenSua(e.target.value)}
              aria-label={t('collections.rename')}
              autoFocus
            />
            <button type="submit" className="btn btn--primary" disabled={boSuuTap.busy}>
              {t('collections.save')}
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => {
                setDangSua(false);
                setTenSua(bo.name);
              }}
            >
              {t('collections.cancel')}
            </button>
          </form>
        ) : (
          <>
            <button
              type="button"
              className="bst-item__name"
              aria-expanded={mo}
              onClick={() => setMo((x) => !x)}
            >
              <IconFolder /> {bo.name}{' '}
              <span className="muted small">{t('collections.count', { n: bo.itemCount })}</span>
            </button>
            <span className="bst-item__actions">
              <button type="button" className="linkish" onClick={() => setMo((x) => !x)}>
                {mo ? t('collections.hide') : t('collections.show')}
              </button>
              <button type="button" className="linkish" onClick={() => setDangSua(true)}>
                {t('collections.rename')}
              </button>
              <button type="button" className="linkish" onClick={() => setHoiXoa(true)}>
                {t('collections.delete')}
              </button>
            </span>
          </>
        )}
      </div>

      {/* Xác nhận NGAY TẠI CHỖ, không dùng window.confirm: hộp thoại trình duyệt không
          dịch được và chặn cả trang. */}
      {hoiXoa && (
        <div className="notice notice--warn bst-confirm" role="alertdialog">
          <p>{t('collections.confirmDelete', { name: bo.name })}</p>
          <button
            type="button"
            className="btn btn--primary"
            disabled={boSuuTap.busy}
            onClick={() => void boSuuTap.remove(bo.id)}
          >
            {t('collections.confirmYes')}
          </button>
          <button type="button" className="btn" onClick={() => setHoiXoa(false)}>
            {t('collections.cancel')}
          </button>
        </div>
      )}

      {mo &&
        (bo.items.length === 0 ? (
          <p className="section-sub">{t('collections.itemsEmpty')}</p>
        ) : (
          <ul className="bst-items">
            {bo.items.map((m) => (
              <li key={`${m.itemType}:${m.itemId}`} className="bst-items__row">
                {m.itemType === 'dish' ? <IconDining /> : <IconPin />}{' '}
                {m.itemType === 'dish' ? (
                  <Link to={dishRoute(m.itemId)}>{m.name}</Link>
                ) : (
                  <span>{m.name}</span>
                )}{' '}
                <span className="muted small">
                  {m.itemType === 'dish' ? t('account.item.dish') : t('account.item.restaurant')}
                </span>
                <button
                  type="button"
                  className="bst-items__remove"
                  aria-label={t('collections.removeItem', { name: m.name })}
                  disabled={boSuuTap.busy}
                  onClick={() => void boSuuTap.removeItem(bo.id, m.itemType, m.itemId)}
                >
                  <IconClose />
                </button>
              </li>
            ))}
          </ul>
        ))}
    </li>
  );
}
