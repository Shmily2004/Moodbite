/**
 * VIEWMODEL của màn "Cần xử lý" — `GET /admin/issues` + mở chi tiết + đánh dấu xong.
 *
 * Chỉ điều phối. Việc phân loại mức gấp và định nghĩa từng loại vấn đề nằm ở
 * `domain/services/data_issues.py`; ở đây không có một quy tắc nghiệp vụ nào.
 *
 * ⚠️ NĂM THẺ SỐ Ở ĐẦU TRANG LUÔN LẤY TỪ LƯỢT GỌI KHÔNG LỌC.
 * Bấm tab "Nghiêm trọng" mà ba thẻ kia tụt về 0 là hiểu sai con số — người quản trị sẽ
 * tưởng vừa xử lý xong hết. Backend đã trả về bộ đếm toàn cục kể cả khi có `priority`,
 * nên chỉ cần dùng đúng thứ nó trả về, đừng cộng lại từ `groups` đã lọc.
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type {
  AdminIssueDetailData,
  AdminIssuesData,
  UuTienVanDe,
} from '@/shared/api';

function loiThanhChu(err: unknown): string {
  return err instanceof ApiError ? err.message : (err as Error).message;
}

export interface UseIssuesResult {
  data: AdminIssuesData | null;
  loading: boolean;
  error: string | null;
  /** `null` = xem tất cả. */
  uuTien: UuTienVanDe | null;
  chonUuTien: (muc: UuTienVanDe | null) => void;
  reload: () => void;
}

export function useIssues(): UseIssuesResult {
  const [data, setData] = useState<AdminIssuesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uuTien, setUuTien] = useState<UuTienVanDe | null>(null);
  const [lan, setLan] = useState(0);

  useEffect(() => {
    let conSong = true;
    setLoading(true);

    adminApi
      .issues({ priority: uuTien })
      .then((kq) => {
        if (!conSong) return;
        setData(kq);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!conSong) return;
        setError(loiThanhChu(err));
      })
      .finally(() => {
        if (conSong) setLoading(false);
      });

    return () => {
      conSong = false;
    };
  }, [uuTien, lan]);

  return {
    data,
    loading,
    error,
    uuTien,
    chonUuTien: setUuTien,
    reload: useCallback(() => setLan((n) => n + 1), []),
  };
}

export interface UseIssueDetailResult {
  data: AdminIssueDetailData | null;
  loading: boolean;
  error: string | null;
  /** Đang gửi yêu cầu đánh dấu cho `target_id` nào. `null` = không có. */
  dangGui: string | null;
  danhDau: (targetId: string, dat: boolean) => Promise<void>;
}

/**
 * Chi tiết MỘT nhóm vấn đề. `khoa === null` thì không gọi API.
 *
 * Sau khi đánh dấu, tải LẠI cả danh sách thay vì tự sửa trạng thái trong bộ nhớ: thao
 * tác có thể hỏng ở server (kho đầy, mất quyền ghi) và một giao diện tự tô "đã xong"
 * trước khi server xác nhận sẽ nói dối người quản trị về việc mình vừa làm.
 */
export function useIssueDetail(khoa: string | null): UseIssueDetailResult {
  const [data, setData] = useState<AdminIssueDetailData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dangGui, setDangGui] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  useEffect(() => {
    if (!khoa) {
      setData(null);
      setError(null);
      return;
    }
    let conSong = true;
    setLoading(true);

    adminApi
      .issueDetail(khoa)
      .then((kq) => {
        if (!conSong) return;
        setData(kq);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!conSong) return;
        setError(loiThanhChu(err));
      })
      .finally(() => {
        if (conSong) setLoading(false);
      });

    return () => {
      conSong = false;
    };
  }, [khoa, lan]);

  const danhDau = useCallback(
    async (targetId: string, dat: boolean) => {
      if (!khoa) return;
      setDangGui(targetId);
      try {
        if (dat) {
          await adminApi.resolveIssue({ key: khoa, target_id: targetId });
        } else {
          await adminApi.unresolveIssue(khoa, targetId);
        }
        setError(null);
        setLan((n) => n + 1);
      } catch (err: unknown) {
        setError(loiThanhChu(err));
      } finally {
        setDangGui(null);
      }
    },
    [khoa],
  );

  return { data, loading, error, dangGui, danhDau };
}
