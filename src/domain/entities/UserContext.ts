import type { ContextSignal } from "../value_objects/ContextSignal";
import type { ContextVector } from "../value_objects/ContextVector";
import type { Location } from "../value_objects/Location";

export interface UserContext {
  session_id: string;
  query_text?: string | null;
  latitude: number;
  longitude: number;
  /** Optional composed value object; scalar latitude/longitude remain the source of truth for persistence. */
  location?: Location | null;
  /** Optional composed context signals (weather, traffic, time). */
  context_signals?: ContextSignal | null;
  /** Optional runtime context vector for cluster matching. */
  context_vector?: ContextVector | null;
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
