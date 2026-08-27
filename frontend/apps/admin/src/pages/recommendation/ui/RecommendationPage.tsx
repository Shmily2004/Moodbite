/**
 * TRANG "GỢI Ý & HỆ THỐNG" — soi NĂM LỚP MÔ HÌNH của đề án (CLAUDE.md mục 4c).
 *
 * Đây là màn để XEM và KIỂM TRA hệ gợi ý, KHÔNG phải để chỉnh nó. Không có ô nhập trọng
 * số, không có nút "lưu cấu hình mô hình" — công thức xếp hạng là quy tắc nghiệp vụ và
 * chỉ được nằm ở `domain/services/`. Cho chỉnh qua giao diện thì mỗi lần deploy lại một
 * kết quả khác nhau và không ai tái hiện được để bảo vệ đồ án.
 *
 * ⚠️ NÓI ĐÚNG ĐỘ PHỦ, KỂ CẢ KHI XẤU. Lớp 1 chỉ phủ ~2,3% quán vì phân cụm cần tín hiệu
 * rating/giá/review mà rất ít quán có. Con số đó phải hiện ra, chứ không được giấu sau
 * một dấu "✅ Xong" như tài liệu từng làm.
 */
import { useRecommendation } from '@/features/view-recommendation';
import type { LopMoHinh } from '@/shared/api';

const NHAN_TRANG_THAI: Record<string, { chu: string; lop: string }> = {
  chay: { chu: 'Đang chạy', lop: 'nhan nhan--ok' },
  mot_phan: { chu: 'Chạy một phần', lop: 'nhan nhan--canh-bao' },
  chua_lam: { chu: 'Chưa làm', lop: 'nhan nhan--tat' },
};

export function RecommendationPage() {
  const { data, loading, error, reload } = useRecommendation();

  return (
    <div className="tong-quan">
      <header className="bang__dau">
        <h2 className="panel__tieu-de">Gợi ý &amp; Hệ thống</h2>
        <button className="ghost" onClick={reload} disabled={loading}>
          {loading ? 'Đang tải…' : '⟳ Tải lại'}
        </button>
      </header>
      <p className="muted">
        Năm lớp mô hình của MoodBite. Màn này chỉ để xem và kiểm tra — trọng số xếp hạng
        nằm trong mã nguồn, cố ý không chỉnh được qua giao diện.
      </p>

      {error && <p className={data ? 'notice notice--warn' : 'panel panel--error'}>{error}</p>}
      {loading && !data && <p className="panel muted">Đang đọc trạng thái mô hình…</p>}

      {data && (
        <>
          {/* `cluster_labels` có giá trị mặc định ở backend nên kiểu sinh ra là optional.
              Chuẩn hoá một lần ở đây thay vì rải `?? []` khắp phần dựng. */}
          <ul className="lop-mo-hinh">
            {data.layers.map((L: LopMoHinh) => {
              const tt = NHAN_TRANG_THAI[L.status] ?? NHAN_TRANG_THAI.chua_lam;
              return (
                <li key={L.layer} className="panel lop-mo-hinh__o">
                  <div className="lop-mo-hinh__dau">
                    <span className="lop-mo-hinh__so">Lớp {L.layer}</span>
                    <span className={tt.lop}>{tt.chu}</span>
                  </div>
                  <h3 className="lop-mo-hinh__ten">{L.name}</h3>
                  {L.method && <p className="muted lop-mo-hinh__cach">{L.method}</p>}
                  {L.coverage && <p className="lop-mo-hinh__phu">{L.coverage}</p>}
                  {L.note && <p className="muted lop-mo-hinh__ghi">{L.note}</p>}
                </li>
              );
            })}
          </ul>

          <section className="panel">
            <h3 className="panel__tieu-de">Nhãn cụm trải nghiệm</h3>
            {(data.cluster_labels ?? []).length === 0 ? (
              <p className="muted">Chưa có quán nào được phân cụm.</p>
            ) : (
              <ul className="nguon">
                {(data.cluster_labels ?? []).map((c: { label?: string; count?: number }) => (
                  <li key={c.label} className="nguon__dong">
                    <span className="nguon__ten">{c.label}</span>
                    <div className="do-phu__thanh">
                      <div
                        className="do-phu__day do-phu__day--tot"
                        style={{
                          width: `${((c.count ?? 0) / Math.max(1, data.clustered_restaurants)) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="nguon__so">{(c.count ?? 0).toLocaleString('vi-VN')}</span>
                  </li>
                ))}
              </ul>
            )}
            <p className="muted panel__ghi-chu">
              {data.clustered_restaurants.toLocaleString('vi-VN')}/
              {data.restaurants_total.toLocaleString('vi-VN')} quán có cụm. Quán chưa phân
              cụm <strong>không</strong> bị coi là quán dở — hệ dùng điểm trung tính 0,5
              (Cold Start).
            </p>
          </section>

          <section className="panel">
            <h3 className="panel__tieu-de">Dữ liệu để huấn luyện</h3>
            <p>
              Đã ghi <strong>{data.interactions_total.toLocaleString('vi-VN')}</strong>{' '}
              lượt tương tác của người dùng.
            </p>
            {/* Nói thẳng con số nhỏ thay vì vẽ biểu đồ trống. Đây là nút thắt thật của
                cả dự án, không phải chi tiết phụ. */}
            <p className="muted">
              Đây là nút thắt lớn nhất còn lại: chưa đủ dữ liệu thì chưa huấn luyện được
              mô hình xếp hạng, và cũng chưa đo được NDCG hay Precision@K. Lớp 3 hiện là
              công thức trọng số do người đặt, chưa phải mô hình học từ dữ liệu.
            </p>
          </section>
        </>
      )}
    </div>
  );
}
