class StateTracker:
    def __init__(self):
        # Dictionary to track state changes
        self.state_changes = {
            "gpios": False,
            "random_actions": False,
            "cycle_start_stop": False,
            "config": False,
            "start_button": False,
        }

    def notify_update(self, attribute):
        """
        Notify that a specific attribute's state has changed.

        Parameters:
        - attribute (str): The name of the attribute to mark as changed.
        """
        if attribute in self.state_changes:
            self.state_changes[attribute] = True

    def clear_update(self, attribute):
        """
        Set the state of a specific attribute to False.

        Parameters:
        - attribute (str): The name of the attribute to set to False.
        """
        if attribute in self.state_changes:
            self.state_changes[attribute] = False
            
    def has_changes(self):
        """
        Check if any attribute's state has changed.

        Returns:
        - bool: True if any state has changed, False otherwise.
        """
        return any(self.state_changes.values())

    def get_changes(self):
        """
        Get a list of attributes whose states have changed.

        Returns:
        - list: A list of attribute names with state changes.
        """
        return [key for key, value in self.state_changes.items() if value]

    def reset_changes(self):
        """
        Reset the state change flags for all attributes.
        """
        for key in self.state_changes:
            self.state_changes[key] = False

state_tracker = StateTracker()