import type { UserContext } from "../../domain/entities/UserContext";
import type { IUserContextRepository } from "../../application/ports/IUserContextRepository";

export class InMemoryUserContextRepository implements IUserContextRepository {
  private readonly contexts: UserContext[] = [
    {
      session_id: "user-1",
      query_text: "món gì ấm bụng cho hôm nay",
      latitude: 21.0285,
      longitude: 105.8542,
      budget_constraint: 50000,
      dietary_constraint: [],
      hours_constraint: null,
      searched_at: "2026-07-31T09:00:00.000Z",
      weather_signal: "rainy",
      traffic_signal: null,
      time_signal: "morning",
      experience_cluster_id: null,
      review_summary: "muốn món gì đó comfort, cozy, ấm bụng vì trời mưa",
    },
  ];

  async save(context: UserContext): Promise<UserContext> {
    const existingIndex = this.contexts.findIndex((item) => item.session_id === context.session_id);
    if (existingIndex >= 0) {
      this.contexts[existingIndex] = context;
      return context;
    }

    this.contexts.push(context);
    return context;
  }

  async findByUserId(userId: string): Promise<UserContext | null> {
    return this.contexts.find((context) => context.session_id === userId) ?? null;
  }

  async findBySessionId(sessionId: string): Promise<UserContext | null> {
    return this.contexts.find((context) => context.session_id === sessionId) ?? null;
  }

  async findRecentBySession(sessionId: string, limit: number): Promise<UserContext[]> {
    return this.contexts.filter((context) => context.session_id === sessionId).slice(0, limit);
  }

  async findRecentByLocation(latitude: number, longitude: number, radiusKm: number, limit: number): Promise<UserContext[]> {
    return this.contexts
      .filter((context) => Math.abs(context.latitude - latitude) <= radiusKm / 111 && Math.abs(context.longitude - longitude) <= radiusKm / 111)
      .slice(0, limit);
  }

  async findByBudgetConstraint(maxBudget: number): Promise<UserContext[]> {
    return this.contexts.filter((context) => (context.budget_constraint ?? Number.POSITIVE_INFINITY) <= maxBudget);
  }

  async findByDietaryConstraint(dietaryConstraints: string[]): Promise<UserContext[]> {
    return this.contexts.filter((context) => {
      const constraints = context.dietary_constraint ?? [];
      return dietaryConstraints.every((constraint) => constraints.includes(constraint));
    });
  }

  async deleteBySessionId(sessionId: string): Promise<void> {
    const nextContexts = this.contexts.filter((context) => context.session_id !== sessionId);
    this.contexts.splice(0, this.contexts.length, ...nextContexts);
  }
}