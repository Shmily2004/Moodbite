/**
 * Đại diện một phân khúc trải nghiệm nhà hàng — kết quả đầu ra của KMeans.
 * cluster_id chỉ có ý nghĩa khi đối chiếu đúng model_version_tag đang active.
 */
export interface ExperienceCluster {
  cluster_id: number;
  label?: string | null;
  model_version_tag: string;
  centroid?: number[] | null;
  k_clusters?: number | null;
}
