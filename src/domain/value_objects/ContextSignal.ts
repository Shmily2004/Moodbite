export interface ContextSignalProps {
  weather?: string | null;
  traffic?: string | null;
  time?: string | null;
}

export class ContextSignal {
  readonly weather: string | null;
  readonly traffic: string | null;
  readonly time: string | null;

  private constructor(props: ContextSignalProps) {
    this.weather = props.weather ?? null;
    this.traffic = props.traffic ?? null;
    this.time = props.time ?? null;
  }

  static create(props: ContextSignalProps): ContextSignal {
    return new ContextSignal(props);
  }

  static fromScalars(
    weather?: string | null,
    traffic?: string | null,
    time?: string | null
  ): ContextSignal {
    return new ContextSignal({ weather, traffic, time });
  }

  hasAnySignal(): boolean {
    return this.weather !== null || this.traffic !== null || this.time !== null;
  }
}
