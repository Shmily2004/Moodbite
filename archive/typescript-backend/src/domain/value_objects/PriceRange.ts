import { DomainError } from "../errors/DomainError";

export type PriceRangeLevel = 1 | 2 | 3 | 4;

export class PriceRange {
  readonly level: PriceRangeLevel;

  private constructor(level: PriceRangeLevel) {
    this.level = level;
  }

  static create(level: number): PriceRange {
    if (!Number.isInteger(level) || level < 1 || level > 4) {
      throw new DomainError(`Price range must be an integer from 1 to 4, got ${level}`);
    }
    return new PriceRange(level as PriceRangeLevel);
  }

  equals(other: PriceRange): boolean {
    return this.level === other.level;
  }
}
