/**
 * VIEW tab "Địa chỉ của tôi" (design/profile.png, mục thanh bên).
 *
 * Chỉ JSX + state giao diện (đang mở form không, địa chỉ nào đang hỏi xác nhận xoá).
 * Dữ liệu và thao tác đến từ `useAddresses` + `useAddressForm` do trang truyền vào.
 *
 * Toạ độ hiện ra để người dùng kiểm được điểm mình vừa chọn — KHÔNG hiện một "địa chỉ"
 * suy ra từ toạ độ, vì ta không tra ngược (không geocoding).
 */
import { useState } from 'react';
import type { FormEvent } from 'react';
import { IconPin, IconStar } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import type { UseAddressesResult } from '../model/useAddresses';
import type { UseAddressFormResult } from '../model/useAddressForm';
import { PointPickerMap } from './PointPickerMap';

export interface AddressesPanelProps {
  diaChi: UseAddressesResult;
  form: UseAddressFormResult;
}

/** 5 chữ số thập phân ≈ 1 mét — đủ để người dùng thấy điểm đã đổi, không rối mắt. */
function toaDo(x: number): string {
  return x.toFixed(5);
}

export function AddressesPanel({ diaChi, form }: AddressesPanelProps) {
  const t = useT();
  const [moForm, setMoForm] = useState(false);
  const [hoiXoa, setHoiXoa] = useState<string | null>(null);

  const luu = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.point) return;
    const ok = await diaChi.add({
      label: form.label,
      addressText: form.addressText,
      lat: form.point.lat,
      lng: form.point.lng,
    });
    if (ok) {
      form.reset();
      setMoForm(false);
    }
  };

  return (
    <section className="panel">
      <div className="results__head">
        <h2 className="panel__title">
          <IconPin /> {t('addresses.title')}
        </h2>
        {!moForm && (
          <button type="button" className="btn btn--primary" onClick={() => setMoForm(true)}>
            {t('addresses.add')}
          </button>
        )}
      </div>
      <p className="section-sub">{t('addresses.sub')}</p>

      {diaChi.error && (
        <p className="notice notice--error" role="alert">
          {diaChi.error}
        </p>
      )}

      {moForm && (
        <form className="dc-form" onSubmit={(e) => void luu(e)}>
          <label className="dc-form__field">
            <span>{t('addresses.label')}</span>
            <input
              className="mp-input"
              value={form.label}
              onChange={(e) => form.setLabel(e.target.value)}
              placeholder={t('addresses.labelPlaceholder')}
            />
          </label>
          <label className="dc-form__field">
            <span>{t('addresses.text')}</span>
            <input
              className="mp-input"
              value={form.addressText}
              onChange={(e) => form.setAddressText(e.target.value)}
              placeholder={t('addresses.textPlaceholder')}
            />
          </label>

          <div className="dc-form__row">
            <button
              type="button"
              className="btn"
              onClick={form.locateMe}
              disabled={form.locating}
            >
              <IconPin className="icon-inline" />{' '}
              {form.locating ? t('addresses.locating') : t('addresses.useCurrent')}
            </button>
            <span className="muted small">{t('addresses.pickHint')}</span>
          </div>
          {form.geoFailed && <p className="notice notice--warn">{t('addresses.geoFailed')}</p>}

          <PointPickerMap point={form.point} onPick={form.setPoint} />
          <p className="muted small" role="status">
            {form.point
              ? t('addresses.picked', {
                  lat: toaDo(form.point.lat),
                  lng: toaDo(form.point.lng),
                })
              : t('addresses.notPicked')}
          </p>

          <div className="dc-form__row">
            <button
              type="submit"
              className="btn btn--primary"
              disabled={diaChi.busy || !form.point || form.label.trim() === ''}
            >
              {t('addresses.save')}
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => {
                form.reset();
                setMoForm(false);
              }}
            >
              {t('addresses.cancel')}
            </button>
          </div>
        </form>
      )}

      {!diaChi.loading && diaChi.addresses.length === 0 && !moForm ? (
        <p className="section-sub">{t('addresses.empty')}</p>
      ) : (
        <ul className="dc-list">
          {diaChi.addresses.map((dc) => (
            <li key={dc.address_id} className="dc-item">
              <div className="dc-item__main">
                <strong>{dc.label}</strong>{' '}
                {dc.is_default && (
                  <span className="dc-item__badge">
                    <IconStar className="icon-inline" /> {t('addresses.default')}
                  </span>
                )}
                <p className="muted small">{dc.address_text ?? t('addresses.noText')}</p>
                <p className="muted small">
                  {toaDo(dc.lat)}, {toaDo(dc.lng)}
                </p>
              </div>
              <div className="dc-item__actions">
                <button
                  type="button"
                  className="linkish"
                  disabled={diaChi.busy}
                  onClick={() => void diaChi.setDefault(dc.address_id, !dc.is_default)}
                >
                  {dc.is_default ? t('addresses.unsetDefault') : t('addresses.setDefault')}
                </button>
                <button
                  type="button"
                  className="linkish"
                  onClick={() => setHoiXoa(dc.address_id)}
                >
                  {t('addresses.delete')}
                </button>
              </div>
              {hoiXoa === dc.address_id && (
                <div className="notice notice--warn bst-confirm" role="alertdialog">
                  <p>{t('addresses.confirmDelete', { name: dc.label })}</p>
                  <button
                    type="button"
                    className="btn btn--primary"
                    disabled={diaChi.busy}
                    onClick={() => void diaChi.remove(dc.address_id)}
                  >
                    {t('addresses.confirmYes')}
                  </button>
                  <button type="button" className="btn" onClick={() => setHoiXoa(null)}>
                    {t('addresses.cancel')}
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
