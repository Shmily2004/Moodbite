import { DomainError } from "../errors/DomainError";

export class Location {
  readonly latitude: number;
  readonly longitude: number;

  private constructor(latitude: number, longitude: number) {
    this.latitude = latitude;
    this.longitude = longitude;
  }

  static create(latitude: number, longitude: number): Location {
    if (latitude < -90 || latitude > 90) {
      throw new DomainError(`Latitude must be between -90 and 90, got ${latitude}`);
    }
    if (longitude < -180 || longitude > 180) {
      throw new DomainError(`Longitude must be between -180 and 180, got ${longitude}`);
    }
    return new Location(latitude, longitude);
  }

  equals(other: Location): boolean {
    return this.latitude === other.latitude && this.longitude === other.longitude;
  }
}
