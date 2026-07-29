export interface UserContext {
  session_id: string;
  query_text?: string | null;
  latitude: number;
  longitude: number;
  budget_constraint?: number | null;
  dietary_constraint?: string[] | null;
  hours_constraint?: string | null;
  searched_at: string;
  weather_signal?: string | null;
  traffic_signal?: string | null;
  time_signal?: string | null;
  experience_cluster_id?: number | null;
  review_summary?: string | null;
}
