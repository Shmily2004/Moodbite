import type { Restaurant } from "../entities/Restaurant";

/**
 * Handles restaurants without an assigned experience cluster (Cold Start).
 * NULL cluster_id must not propagate as 0 or NULL into ranking formulas.
 */
export class RestaurantColdStartPolicy {
  isColdStart(restaurant: Pick<Restaurant, "experience_cluster_id">): boolean {
    return restaurant.experience_cluster_id == null;
  }

  resolveClusterScore(
    clusterScore: number | null | undefined,
    systemAverageScore: number
  ): number {
    if (clusterScore == null) {
      return systemAverageScore;
    }
    return clusterScore;
  }
}
