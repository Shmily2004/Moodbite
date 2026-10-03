/**
 * VIEWMODEL "Địa chỉ của tôi": danh sách + thêm / đặt mặc định / xoá.
 *
 * Sau mỗi thao tác ghi thì TẢI LẠI danh sách thay vì tự sửa state: đặt một địa chỉ làm
 * mặc định sẽ làm địa chỉ mặc định CŨ thôi làm mặc định — luật đó nằm ở backend (một giao
 * dịch). Tự mô phỏng lại ở đây là chép luật nghiệp vụ xuống frontend (CLAUDE.md mục 1b).
 * Danh sách tối đa 10 địa chỉ nên tải lại gần như không tốn gì.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useUserSessionContext } from '@/entities/user';
import { useT } from '@/shared/i18n';
import { suaDiaChi, taiDiaChi, themDiaChi, xoaDiaChi } from '@/entities/address';
import type { DiaChi } from '@/entities/address';

export interface DiaChiMoi {
  label: string;
  addressText: string;
  lat: number;
  lng: number;
}

export interface UseAddressesResult {
  addresses: DiaChi[];
  loading: boolean;
  busy: boolean;
  error: string | null;
  add: (dc: DiaChiMoi) => Promise<boolean>;
  setDefault: (addressId: string, isDefault: boolean) => Promise<boolean>;
  remove: (addressId: string) => Promise<boolean>;
}

function thongBaoLoi(err: unknown, macDinh: string): string {
  return err instanceof Error && err.message ? err.message : macDinh;
}

export function useAddresses(): UseAddressesResult {
  const session = useUserSessionContext();
  const [addresses, setAddresses] = useState<DiaChi[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Câu lỗi DỰ PHÒNG dịch theo ngôn ngữ; `t` qua ref để không phải đưa vào deps (đổi
  // ngôn ngữ không được làm tải lại dữ liệu).
  const t = useT();
  const tRef = useRef(t);
  tRef.current = t;
  const [lan, setLan] = useState(0);

  useEffect(() => {
    if (!session.isLoggedIn) {
      setAddresses([]);
      return;
    }
    let con_song = true;
    setLoading(true);
    taiDiaChi()
      .then((ds) => {
        if (!con_song) return;
        setAddresses(ds);
      })
      .catch((err: unknown) => {
        if (con_song) setError(thongBaoLoi(err, tRef.current('err.addrLoad')));
      })
      .finally(() => {
        if (con_song) setLoading(false);
      });
    return () => {
      con_song = false;
    };
  }, [session.isLoggedIn, lan]);

  const chay = useCallback(async (viec: () => Promise<unknown>, loi: string) => {
    setBusy(true);
    try {
      await viec();
      setError(null);
      setLan((n) => n + 1); // tải lại — xem ghi chú đầu file
      return true;
    } catch (err) {
      setError(thongBaoLoi(err, loi));
      return false;
    } finally {
      setBusy(false);
    }
  }, []);

  const add = useCallback(
    (dc: DiaChiMoi) =>
      chay(
        () =>
          themDiaChi({
            label: dc.label,
            latitude: dc.lat,
            longitude: dc.lng,
            // Chuỗi rỗng -> null: "không có mô tả", không phải mô tả rỗng.
            address_text: dc.addressText.trim() === '' ? null : dc.addressText,
          }),
        tRef.current('err.addrSave'),
      ),
    [chay],
  );

  const setDefault = useCallback(
    (addressId: string, isDefault: boolean) =>
      chay(() => suaDiaChi(addressId, { is_default: isDefault }), tRef.current('err.addrDefault')),
    [chay],
  );

  const remove = useCallback(
    (addressId: string) => chay(() => xoaDiaChi(addressId), tRef.current('err.addrDelete')),
    [chay],
  );

  return { addresses, loading, busy, error, add, setDefault, remove };
}
