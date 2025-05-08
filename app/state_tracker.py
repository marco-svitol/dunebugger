class StateTracker:
    def __init__(self):
        # Dictionary to track state changes
        self.state_changes = {
            "gpios": False,
            "random_actions": False,
            "cycle_start_stop": False,
            "config": False,
            "start_button": False,
            "playing_time": False,
            "sequence": False,
        }

    def notify_update(self, attribute):
        if attribute in self.state_changes:
            self.state_changes[attribute] = True

    def clear_update(self, attribute):
        if attribute in self.state_changes:
            self.state_changes[attribute] = False

    def force_update(self):
        for key in self.state_changes:
            self.state_changes[key] = True

    def has_changes(self):
        return any(self.state_changes.values())

    def get_changes(self):
        return [key for key, value in self.state_changes.items() if value]

    def reset_changes(self):
        for key in self.state_changes:
            self.state_changes[key] = False


state_tracker = StateTracker()
