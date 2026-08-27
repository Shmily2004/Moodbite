/**
 * Ô CHI TIẾT MÓN — trượt ra khi bấm "Xem chi tiết" trên bảng món.
 *
 * VÌ SAO LÀ Ô TRƯỢT CHỨ KHÔNG PHẢI TRANG RIÊNG: xem chi tiết ở đây là việc LẶP — admin
 * dò xuống bảng, mở một món, đóng, mở món kế. Tách sang trang riêng là mỗi lần xem phải
 * đi và quay lại, mất luôn vị trí cuộn và bộ lọc đang bật.
 *
 * ⚠️ CHỈ ĐỌC. Không có nút Sửa vì `dish_catalog.json` là file do
 * `scripts/build_dish_catalog.py` SINH RA — sửa qua đây sẽ bị lần chạy sau ghi đè. Bày
 * một nút "Sửa" rồi báo lỗi còn tệ hơn là nói thẳng.
 */
import { useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type { AdminDishDetail } from '@/shared/api';

export interface DishDetailPanelProps {
  dishId: string;
  onClose: () => void;
}

export function DishDetailPanel({ dishId, onClose }: DishDetailPanelProps) {
  const [data, setData] = useState<AdminDishDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let conSong = true;
    setLoading(true);
    setData(null);
    setError(null);

    adminApi
      .getDish(dishId)
      .then((kq) => {
        if (conSong) setData(kq);
      })
      .catch((err: unknown) => {
        if (!conSong) return;
        setError(err instanceof ApiError ? err.message : (err as Error).message);
      })
      .finally(() => {
        if (conSong) setLoading(false);
      });

    return () => {
      conSong = false;
    };
  }, [dishId]);

  // Esc để đóng: ô này che mất bảng, và bàn phím là đường thoát mà người dùng luôn thử
  // trước khi đi tìm nút X.
  useEffect(() => {
    const nghe = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', nghe);
    return () => window.removeEventListener('keydown', nghe);
  }, [onClose]);

  return (
    <aside className="chi-tiet" aria-label="Chi tiết món">
      <div className="chi-tiet__dau">
        <h3 className="panel__tieu-de">{data?.name ?? 'Chi tiết món'}</h3>
        <button className="ghost" onClick={onClose} aria-label="Đóng chi tiết">
          Đóng
        </button>
      </div>

      {loading && <p className="muted">Đang tải…</p>}
      {error && <p className="notice notice--warn">{error}</p>}

      {data && (() => {
        // `match_keywords`/`meal_times` có `default_factory` ở backend nên kiểu sinh ra là
        // optional. Chuẩn hoá một lần ở đây thay vì rải `?? []` khắp phần dựng.
        const tuKhoa = data.match_keywords ?? [];
        const bua = data.meal_times ?? [];
        return (
        <>
          <div className="chi-tiet__than">
            {data.image_url ? (
              <img
                className="chi-tiet__anh"
                src={data.image_url}
                alt=""
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            ) : (
              <p className="notice notice--warn">
                Chưa có ảnh. Ảnh món lấy từ Wikimedia Commons — món không có bài Wikipedia
                thì chưa tra được.
              </p>
            )}

            <div className="chi-tiet__nhan-hang">
              {data.is_category && <span className="nhan nhan--tin">danh mục</span>}
              <span className={data.is_active ? 'nhan nhan--ok' : 'nhan nhan--tat'}>
                {data.is_active ? 'Có quán bán' : 'Chưa tìm được quán'}
              </span>
              {data.cuisine && <span className="nhan nhan--tin">{data.cuisine}</span>}
            </div>

            <h4 className="chi-tiet__nhan">Giới thiệu</h4>
            {data.description ? (
              <p className="chi-tiet__mo-ta">{data.description}</p>
            ) : (
              <p className="muted">Chưa tra được giới thiệu cho món này.</p>
            )}

            {/* Từ khoá đối chiếu là thứ QUYẾT ĐỊNH món này ra quán nào. Với admin đang đi
                tìm "vì sao món X không ra quán nào", đây là thông tin quan trọng nhất
                trên cả ô này. */}
            <h4 className="chi-tiet__nhan">Từ khoá đối chiếu tên quán</h4>
            {tuKhoa.length > 0 ? (
              <ul className="chip-hang">
                {tuKhoa.map((k) => (
                  <li key={k} className="chip">
                    {k}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">
                Không có từ khoá nào — đây thường là lý do món chưa khớp được quán.
              </p>
            )}

            <h4 className="chi-tiet__nhan">Thuộc tính</h4>
            <dl className="cau-hinh">
              <Muc nhan="Mã món" gia_tri={data.dish_id} />
              <Muc nhan="Nhiệt độ" gia_tri={data.temperature ?? '—'} />
              <Muc nhan="Cách chế biến" gia_tri={data.cooking_method ?? '—'} />
              <Muc
                nhan="Độ cay"
                // `null` là CHƯA BIẾT, khác hẳn `0` là KHÔNG CAY (CLAUDE.md mục 4).
                gia_tri={data.spice_level == null ? 'chưa biết' : String(data.spice_level)}
              />
              <Muc
                nhan="Bữa phù hợp"
                gia_tri={bua.length ? bua.join(', ') : '—'}
              />
              <Muc nhan="Nguồn" gia_tri={data.source ?? '—'} />
              <Muc nhan="Cập nhật" gia_tri={data.last_updated ?? '—'} />
            </dl>

            {data.source_url && (
              <p>
                <a href={data.source_url} target="_blank" rel="noreferrer">
                  Xem nguồn gốc →
                </a>
              </p>
            )}
          </div>

          <p className="muted panel__ghi-chu">
            Chỉ xem. Danh mục món là file do <code>build_dish_catalog.py</code> sinh ra —
            sửa qua đây sẽ bị lần chạy sau ghi đè.
          </p>
        </>
        );
      })()}
    </aside>
  );
}

function Muc({ nhan, gia_tri }: { nhan: string; gia_tri: string }) {
  return (
    <div className="cau-hinh__muc">
      <dt>{nhan}</dt>
      <dd>{gia_tri}</dd>
    </div>
  );
}
