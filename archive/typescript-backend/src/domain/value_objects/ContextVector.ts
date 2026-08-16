import { DomainError } from "../errors/DomainError";

export class ContextVector {
  readonly values: readonly number[];

  private constructor(values: readonly number[]) {
    this.values = values;
  }

  static create(values: number[]): ContextVector {
    if (values.length === 0) {
      throw new DomainError("Context vector must contain at least one dimension");
    }
    if (values.some((value) => !Number.isFinite(value))) {
      throw new DomainError("Context vector values must be finite numbers");
    }
    return new ContextVector([...values]);
  }

  dimension(): number {
    return this.values.length;
  }
}
