class DecisionEngine:
    def __init__(self, quiet_mode: bool = False):
        self.quiet_mode = quiet_mode
        self.event_counts = {}
        self.threshold = 3

    def record_event(self, file_path: str, event_type: str):
        key = f"{file_path}:{event_type}"
        self.event_counts[key] = self.event_counts.get(key, 0) + 1

    def should_intervene(self, file_path: str) -> bool:
        if self.quiet_mode:
            return False

        total = 0
        for key, count in self.event_counts.items():
            if key.startswith(f"{file_path}:"):
                total += count

        return total >= self.threshold
