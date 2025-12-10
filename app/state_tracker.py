import asyncio
from dunebugger_settings import settings
from dunebugger_logging import logger
class StateTracker:
    def __init__(self):
        # Dictionary to track state changes
        self.state_changes = {
            "gpios": False,
            "random_actions": False,
            "cycle_start_stop": False,
            "sequences_validated": False,
            "config": False,
            "start_button": False,
            "playing_time": False,
            "sequence": False,
        }
        self.mqueue_handler = None
        self.monitor_task = None
        self.running = True
        self.check_interval = int(settings.mQueueStateCheckIntervalSecs)

    def notify_update(self, attribute):
        if attribute in self.state_changes:
            self.state_changes[attribute] = True

    def clear_update(self, attribute):
        if attribute in self.state_changes:
            self.state_changes[attribute] = False

    def has_changes(self):
        return any(self.state_changes.values())

    def get_changes(self):
        return [key for key, value in self.state_changes.items() if value]

    def reset_changes(self):
        for key in self.state_changes:
            self.state_changes[key] = False

    async def start_state_monitoring(self):
        """Start the state monitoring task"""
        self.monitor_task = asyncio.create_task(self._monitor_states())

    async def stop_state_monitoring(self):
        """Stop the state monitoring task"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_states(self):
        """
        Monitor the state tracker for changes and react accordingly.
        """
        while self.running:
            if self.has_changes():
                changed_states = self.get_changes()
                for state in changed_states:
                    if state == "gpios":
                        # React to GPIO state changes
                        await self.mqueue_handler.send_gpio_state()
                    elif state in ["random_actions", "cycle_start_stop", "start_button", "sequences_validated"]:
                        # Handle random actions state change
                        await self.mqueue_handler.send_sequence_state()
                    elif state == "playing_time":
                        # Handle playing time changes
                        await self.mqueue_handler.send_playing_time()
                    elif state == "sequence":
                        # Handle sequence changes
                        await self.mqueue_handler.send_sequence()
                    elif state == "config":
                        # Handle configuration changes
                        logger.debug("Configuration changed. Reloading settings...")
                # Reset the state tracker after handling changes
                self.reset_changes()
            await asyncio.sleep(self.check_interval)


state_tracker = StateTracker()
