import asyncio
import json
from dunebugger_logging import logger
from dunebugger_settings import settings


class MessagingQueueHandler:
    """Class to handle messaging queue operations."""

    def __init__(self, state_tracker, sequence_handler, mygpio_handler, terminal_interpreter):
        self.mqueue_sender = None
        self.state_tracker = state_tracker
        self.sequence_handler = sequence_handler
        self.mygpio_handler = mygpio_handler
        self.terminal_interpreter = terminal_interpreter
        self.check_interval = int(settings.mQueueStateCheckIntervalSecs)
        self.running = True
        self.monitor_task = None

    async def process_mqueue_message(self, mqueue_message):
        """Callback method to process received messages."""
        # Parse the JSON string back into a dictionary
        try:
            data = mqueue_message.data.decode()
            message_json = json.loads(data)
        except (AttributeError, UnicodeDecodeError) as decode_error:
            logger.error(f"Failed to decode message data: {decode_error}. Raw message: {mqueue_message.data}")
            return
        except json.JSONDecodeError as json_error:
            logger.error(f"Failed to parse message as JSON: {json_error}. Raw message: {data}")
            return

        try:
            subject = (mqueue_message.subject).split(".")[2]
            logger.debug(f"Processing message: {str(message_json)[:20]}. Subject: {subject}. Reply to: {mqueue_message.reply}")

            if subject in ["dunebugger_set"]:
                command = message_json["body"]
                return await self.terminal_interpreter.process_terminal_input(command)
            elif subject in ["refresh"]:
                self.state_tracker.force_update()
            else:
                logger.warning(f"Unknown subjcet: {subject}. Ignoring message.")
        except KeyError as key_error:
            logger.error(f"KeyError: {key_error}. Message: {message_json}")
        except Exception as e:
            logger.error(f"Error processing message: {e}. Message: {message_json}")

    async def send_gpio_state(self):
        await self.dispatch_message(self.mygpio_handler.get_gpio_status(), "gpio_state", "remote")

    async def send_sequence_state(self):
        await self.dispatch_message(self.sequence_handler.get_state(), "sequence_state", "remote")

    async def send_playing_time(self):
        await self.dispatch_message(self.sequence_handler.get_playing_time(), "playing_time", "remote")

    async def send_sequence(self, sequence="main"):
        await self.dispatch_message(self.sequence_handler.get_sequence(sequence), "sequence", "remote")

    async def dispatch_message(self, message_body, subject, recipient, reply_subject=None):
        message = {
            "body": message_body,
            "subject": subject,
            "source": settings.mQueueClientID,
        }
        await self.mqueue_sender.send(message, recipient, reply_subject)

    async def start_monitoring(self):
        """Start the state monitoring task"""
        self.monitor_task = asyncio.create_task(self._monitor_states())

    async def stop_monitoring(self):
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
            if self.state_tracker.has_changes():
                changed_states = self.state_tracker.get_changes()
                for state in changed_states:
                    if state == "gpios":
                        # React to GPIO state changes
                        await self.send_gpio_state()
                    elif state in ["random_actions", "cycle_start_stop", "start_button"]:
                        # Handle random actions state change
                        await self.send_sequence_state()
                    elif state == "playing_time":
                        # Handle playing time changes
                        await self.send_playing_time()
                    elif state == "sequence":
                        # Handle sequence changes
                        await self.send_sequence()
                    elif state == "config":
                        # Handle configuration changes
                        logger.info("Configuration changed. Reloading settings...")
                # Reset the state tracker after handling changes
                self.state_tracker.reset_changes()
            await asyncio.sleep(self.check_interval)
