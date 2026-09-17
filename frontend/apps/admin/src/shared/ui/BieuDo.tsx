/**
 * Ba hình vẽ SVG nhỏ dùng ở khu quản trị: vòng tiến độ, biểu đồ vành khuyên, sparkline.
 *
 * SVG TỰ VẼ, không thư viện biểu đồ: cả khu quản trị chỉ cần ba hình đơn giản này, thêm
 * một thư viện vài chục KB cho chúng là không đáng — cùng lý do `QualityPage` đã chọn.
 *
 * Mọi hình đều có `role="img"` + `aria-label` nói bằng CHỮ đúng con số đang vẽ. Số liệu
 * vẫn luôn được in ra cạnh hình — hình chỉ để liếc nhanh.
 */

/** Bán kính cho chu vi = 100, để `strokeDasharray` tính thẳng theo phần trăm. */
const R_CHU_VI_100 = 15.915;

/** Vòng tiến độ nhỏ cạnh thẻ số ("298 (34,9%)"). `phan/tong` do backend đếm. */
export function VongTienDo({
  phan,
  tong,
  nhan,
  coPx = 44,
}: {
  phan: number;
  tong: number;
  nhan: string;
  coPx?: number;
}) {
  const pt = tong > 0 ? Math.max(0, Math.min(100, (phan / tong) * 100)) : 0;
  return (
    <svg
      className="vong-tien-do"
      viewBox="0 0 36 36"
      width={coPx}
      height={coPx}
      role="img"
      aria-label={nhan}
    >
      <circle
        className="vong-tien-do__nen"
        cx="18"
        cy="18"
        r={R_CHU_VI_100}
        fill="none"
        strokeWidth="4"
      />
      <circle
        className="vong-tien-do__day"
        cx="18"
        cy="18"
        r={R_CHU_VI_100}
        fill="none"
        strokeWidth="4"
        strokeDasharray={`${pt} ${100 - pt}`}
        strokeDashoffset="25"
      />
    </svg>
  );
}

export interface PhanVanhKhuyen {
  nhan: string;
  giaTri: number;
}

/**
 * Biểu đồ vành khuyên. Màu lấy theo THỨ TỰ phần (`.mau-bieu-do-1..6` trong styles.css),
 * để chú thích bên cạnh dùng đúng cùng lớp màu — không truyền mã màu qua props.
 */
export function VanhKhuyen({
  phan,
  chuGiua,
  chuPhu,
  nhan,
}: {
  phan: PhanVanhKhuyen[];
  chuGiua: string;
  chuPhu?: string;
  nhan: string;
}) {
  const tong = phan.reduce((s, p) => s + p.giaTri, 0);
  // Tính trước điểm bắt đầu của từng phần, thay vì cộng dồn trong lúc render.
  const batDau = phan.map((_, i) =>
    phan.slice(0, i).reduce((s, p) => s + (tong > 0 ? (p.giaTri / tong) * 100 : 0), 0),
  );
  return (
    <svg className="vanh-khuyen" viewBox="0 0 42 42" role="img" aria-label={nhan}>
      <circle
        className="vanh-khuyen__nen"
        cx="21"
        cy="21"
        r={R_CHU_VI_100}
        fill="none"
        strokeWidth="6"
      />
      {tong > 0 &&
        phan.map((p, i) => {
          const pt = (p.giaTri / tong) * 100;
          return (
            <circle
              key={p.nhan}
              className={`vanh-khuyen__phan mau-bieu-do-${(i % 6) + 1}`}
              cx="21"
              cy="21"
              r={R_CHU_VI_100}
              fill="none"
              strokeWidth="6"
              strokeDasharray={`${pt} ${100 - pt}`}
              // Bắt đầu từ 12 giờ (offset 25) rồi lùi dần theo phần đã vẽ.
              strokeDashoffset={25 - batDau[i]}
            />
          );
        })}
      <text x="21" y={chuPhu ? 20.5 : 22.5} textAnchor="middle" className="vanh-khuyen__so">
        {chuGiua}
      </text>
      {chuPhu && (
        <text x="21" y="26" textAnchor="middle" className="vanh-khuyen__phu">
          {chuPhu}
        </text>
      )}
    </svg>
  );
}

/**
 * Đường sparkline. Mọi điểm = 0 thì vẽ đường thẳng ở ĐÁY — không chia cho 0, không tự bịa
 * dao động cho "đẹp".
 */
export function Sparkline({ giaTri, nhan }: { giaTri: number[]; nhan: string }) {
  const rong = 100;
  const cao = 28;
  const lon = Math.max(0, ...giaTri);
  const buoc = giaTri.length > 1 ? rong / (giaTri.length - 1) : 0;
  const diem = giaTri
    .map((v, i) => {
      const y = lon > 0 ? cao - 2 - (v / lon) * (cao - 4) : cao - 2;
      return `${(i * buoc).toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');
  return (
    <svg
      className="sparkline"
      viewBox={`0 0 ${rong} ${cao}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={nhan}
    >
      <polyline points={diem} />
    </svg>
  );
}
