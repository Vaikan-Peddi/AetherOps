from collections import Counter, defaultdict
from dataclasses import dataclass, field


@dataclass
class InMemoryMetrics:
    counters: Counter = field(default_factory=Counter)
    latencies: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))

    def increment(self, name: str, labels: dict[str, str] | None = None, value: int = 1) -> None:
        self.counters[self._key(name, labels)] += value

    def observe_latency(self, name: str, latency_ms: int, labels: dict[str, str] | None = None) -> None:
        self.latencies[self._key(name, labels)].append(latency_ms)

    def prometheus(self) -> str:
        lines: list[str] = []
        for key, value in self.counters.items():
            lines.append(f"{key} {value}")
        for key, values in self.latencies.items():
            if values:
                lines.append(f"{key}_avg_ms {sum(values) / len(values):.2f}")
        return "\n".join(lines) + "\n"

    def _key(self, name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_text = "_".join(f"{key}_{value}" for key, value in sorted(labels.items()))
        return f"{name}_{label_text}"


metrics = InMemoryMetrics()
