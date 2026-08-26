/**
 * NỘI DUNG TỪNG TAB của trang tài khoản.
 *
 * Tách khỏi `AccountPage.tsx` để mỗi file giữ đúng một trách nhiệm: file kia lo KHUNG
 * (thanh bên, thẻ đầu trang, chọn tab), file này lo NỘI DUNG. Gộp lại thì một file phải
 * dài hơn 400 dòng và mỗi lần sửa một tab là phải cuộn qua sáu tab khác.
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import {
  IconBookmark,
  IconClock,
  IconClose,
  IconCompass,
  IconDining,
  IconHeart,
  IconMap,
  IconPin,
  IconShield,
  IconThumbUp,
} from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { dishRoute, ROUTES } from '@/shared/config';
import type { UserSelf, UserStatsData } from '@/shared/api';
import type { MucYeuThich, UseFavoritesResult } from '@/features/save-favorite';
import { LevelCard, BadgeGrid } from '@/widgets/user-progress';

/** "05/2024" từ chuỗi ISO. Sai định dạng thì thà không hiện gì còn hơn hiện "Invalid Date". */
export function thangNam(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
}

// ---------------------------------------------------------------------------
// Món & quán YÊU THÍCH (đổi tên 2026-08-25 — trái tim = "yêu thích")
// ---------------------------------------------------------------------------

export interface SavedTabProps {
  favorites: UseFavoritesResult;
}

export function SavedTab({ favorites }: SavedTabProps) {
  const t = useT();

  return (
    <section className="panel">
      <div className="results__head">
        <h2 className="panel__title">
          <IconHeart /> {t('account.saved.title')}
        </h2>
        {favorites.items.length > 0 && (
          <p className="results__count">
            {t('account.saved.count', { n: favorites.items.length })}
          </p>
        )}
      </div>

      {/* Nói ĐÚNG dữ liệu đang nằm ở đâu. Khách lưu trên máy, đăng nhập thì ở tài khoản —
          im lặng về chuyện đó là để người dùng tự phát hiện lúc mất dữ liệu. */}
      <p className="section-sub">
        {favorites.dongBo ? t('account.saved.synced') : t('account.saved.local')}
      </p>

      {favorites.error && <p className="notice notice--warn">{favorites.error}</p>}

      {favorites.items.length === 0 ? (
        <p className="section-sub">
          {t('account.saved.empty')} <Link to={ROUTES.home}>MoodBite</Link>
        </p>
      ) : (
        <>
          {/* HAI DANH SÁCH TÁCH BẠCH (2026-08-26). Khác trang chủ ở chỗ: ở ĐÂY danh sách
              rỗng VẪN hiện, kèm câu hướng dẫn. Người dùng vào tab này là ĐANG đi tìm nó,
              nên "chưa có gì" cũng là một câu trả lời họ cần. */}
          <NhomDaLuuUI
            nhan={t('forYou.favorites')}
            icon={<IconHeart filled />}
            goiY={t('account.saved.hintFavorite')}
            muc={favorites.favorite.items}
            onBo={favorites.toggle}
          />
          <NhomDaLuuUI
            nhan={t('forYou.bookmarks')}
            icon={<IconBookmark filled />}
            goiY={t('account.saved.hintBookmark')}
            muc={favorites.bookmark.items}
            onBo={favorites.toggle}
          />
        </>
      )}
    </section>
  );
}

/** Một danh sách trong tab "đã lưu". Rỗng thì hiện câu hướng dẫn thay vì biến mất. */
function NhomDaLuuUI({
  nhan,
  icon,
  goiY,
  muc,
  onBo,
}: {
  nhan: string;
  icon: ReactNode;
  goiY: string;
  muc: MucYeuThich[];
  onBo: (muc: MucYeuThich) => void;
}) {
  return (
    <div className="for-you__danh-sach">
      <p className="for-you__ten-danh-sach">
        {icon} {nhan}
      </p>

      {muc.length === 0 ? (
        <p className="section-sub">{goiY}</p>
      ) : (
        <ul className="saved-list">
          {muc.map((m) => (
            <li key={`${m.listType}:${m.itemType}:${m.itemId}`} className="saved-list__item">
              {m.itemType === 'dish' ? (
                <Link className="chip" to={dishRoute(m.itemId)}>
                  <IconDining /> {m.name}
                </Link>
              ) : (
                // Quán CHƯA có trang riêng — panel chi tiết nằm trong trang bản đồ. Làm
                // một link chết chỉ để "cho đủ" thì tệ hơn là không có link.
                <span className="chip chip--flat"><IconPin /> {m.name}</span>
              )}
              <button
                type="button"
                className="linkish"
                // Truyền NGUYÊN mục (kèm `listType`) chứ không dựng lại: thiếu `listType`
                // là bỏ nhầm khỏi danh sách kia.
                aria-label={`Bỏ ${m.name} khỏi ${nhan}`}
                onClick={() => onBo(m)}
              >
                <IconClose />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Đã xem gần đây
// ---------------------------------------------------------------------------

export interface RecentTabProps {
  recent: { recent: Array<{ dishId: string; name: string }>; clear: () => void };
}

export function RecentTab({ recent }: RecentTabProps) {
  const t = useT();

  return (
    <section className="panel">
      <div className="results__head">
        <h2 className="panel__title">
          <IconClock /> {t('account.recent.title')}
        </h2>
        {recent.recent.length > 0 && (
          <button type="button" className="linkish" onClick={recent.clear}>
            {t('account.recent.clear')}
          </button>
        )}
      </div>

      {recent.recent.length === 0 ? (
        <p className="section-sub">{t('account.recent.empty')}</p>
      ) : (
        <ul className="chip-row">
          {recent.recent.map((mon) => (
            <li key={mon.dishId}>
              <Link className="chip" to={dishRoute(mon.dishId)}>
                {mon.name}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Hồ sơ cá nhân
// ---------------------------------------------------------------------------

export interface ProfileTabProps {
  user: UserSelf | null;
}

export function ProfileTab({ user }: ProfileTabProps) {
  const t = useT();
  const thamGia = thangNam(user?.created_at);

  const dong = [
    { nhan: t('account.profile.username'), gia_tri: user?.username ?? '—' },
    { nhan: t('account.profile.displayName'), gia_tri: user?.display_name ?? '—' },
    { nhan: t('account.profile.email'), gia_tri: user?.email ?? null },
    { nhan: t('account.profile.joined'), gia_tri: thamGia ?? '—' },
    { nhan: t('account.profile.role'), gia_tri: user?.role ?? '—' },
  ];

  return (
    <section className="panel">
      <h2 className="panel__title">{t('account.profile.title')}</h2>

      <dl className="profile-grid">
        {dong.map((d) => (
          <div key={d.nhan} className="profile-grid__row">
            <dt>{d.nhan}</dt>
            <dd>
              {d.gia_tri ?? (
                <span className="account__line--warn">{t('account.noEmail')}</span>
              )}
            </dd>
          </div>
        ))}
      </dl>

      {/* Nói rõ VÌ SAO chưa sửa được, thay vì để một cái nút bấm không ăn thua. */}
      <p className="section-sub">{t('account.profile.readonly')}</p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Cấp độ & huy hiệu (tab riêng, ngoài cột phải của tab Tổng quan)
// ---------------------------------------------------------------------------

export interface BadgesTabProps {
  stats: UserStatsData | null;
  loading: boolean;
}

export function BadgesTab({ stats, loading }: BadgesTabProps) {
  const t = useT();

  return (
    <>
      <LevelCard stats={stats} loading={loading} />
      <BadgeGrid stats={stats} loading={loading} />
      <section className="panel">
        <h2 className="panel__title">{t('account.level.how')}</h2>
        {/* Bảng điểm KHÔNG viết cứng ở đây — mỗi con số dưới đây phải khớp với
            `domain/services/gamification.py`. Hiện chỉ có 5 dòng nên chép tay chấp nhận
            được; thêm loại điểm mới thì backend nên trả cả bảng điểm xuống. */}
        <ul className="rule-list">
          <li><IconCompass /> Xem chi tiết một quán mới — <strong>+2</strong></li>
          <li><IconMap /> Bấm chỉ đường tới một quán — <strong>+3</strong></li>
          <li><IconThumbUp /> Đánh giá thích / không thích — <strong>+3</strong></li>
          <li><IconHeart /> Lưu một món hoặc một quán — <strong>+5</strong></li>
          <li><IconShield /> Báo một quán đã đóng cửa — <strong>+10</strong></li>
        </ul>
        <p className="section-sub">
          Điểm tính theo số <strong>quán/món khác nhau</strong>, không theo số lần bấm —
          xem lại cùng một quán hai chục lần vẫn chỉ được tính một.
        </p>
      </section>
    </>
  );
}
