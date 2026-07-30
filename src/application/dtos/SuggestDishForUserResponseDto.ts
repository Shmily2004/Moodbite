export interface SuggestDishForUserResponseDto {
  userId: string;
  context: {
    sessionId: string;
    queryText?: string | null;
    latitude: number;
    longitude: number;
    budgetConstraint?: number | null;
    dietaryConstraints?: string[] | null;
    hoursConstraint?: string | null;
    weatherSignal?: string | null;
    trafficSignal?: string | null;
    timeSignal?: string | null;
    experienceClusterId?: number | null;
    reviewSummary?: string | null;
  } | null;
  suggestedDishes: Array<{
    id: string;
    name: string;
    category?: string | null;
    spiceLevel?: number | null;
    temperature?: "hot" | "cold" | "neutral" | null;
    portionSize?: "light" | "regular" | "heavy" | null;
    moodKeywords?: string[] | null;
    price?: number | null;
  }>;
}
