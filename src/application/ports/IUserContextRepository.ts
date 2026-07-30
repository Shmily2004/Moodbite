import type { UserContext } from "../../domain/entities/UserContext";

export interface IUserContextRepository {
  save(context: UserContext): Promise<UserContext>;
  findByUserId(userId: string): Promise<UserContext | null>;
  findBySessionId(sessionId: string): Promise<UserContext | null>;
  findRecentBySession(sessionId: string, limit: number): Promise<UserContext[]>;
  findRecentByLocation(
    latitude: number,
    longitude: number,
    radiusKm: number,
    limit: number
  ): Promise<UserContext[]>;
  findByBudgetConstraint(maxBudget: number): Promise<UserContext[]>;
  findByDietaryConstraint(dietaryConstraints: string[]): Promise<UserContext[]>;
  deleteBySessionId(sessionId: string): Promise<void>;
}
