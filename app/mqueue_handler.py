import asyncio
import json
from dunebugger_logging import enable_queue_logging, logger
from dunebugger_settings import settings


class MessagingQueueHandler:
    """Class to handle messaging queue operations."""

    def __init__(self, sequence_handler, mygpio_handler, command_interpreter):
        self.mqueue_sender = None
        self.sequence_handler = sequence_handler
        self.mygpio_handler = mygpio_handler
        self.command_interpreter = command_interpreter
        
        if settings.sendLogsToQueue:
            enable_queue_logging(self)
            
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
            #TODO: too much verbosity
            # logger.debug(f"Processing message: {str(message_json)[:20]}. Subject: {subject}. Reply to: {mqueue_message.reply}")

            if subject in ["dunebugger_set"]:
                command = message_json["body"]
                return await self.command_interpreter.process_command(command)
            elif subject in ["refresh"]:
                self.sequence_handler.state_tracker.force_update()
            elif subject in ["terminal_command"]:
                command = message_json["body"]
                if command in ["s"]:
                    gpio_status = self.command_interpreter.gpio_handler.get_gpio_status()
                    await self.dispatch_message(gpio_status, "show_gpio_status", "terminal") #TODO , mqueue_message.reply)
                elif command in ["t"]:
                    settings_list = settings.get_settings()
                    random_actions_status = True if self.command_interpreter.sequence_handler.get_random_actions_state() else False
                    music_volume_status = self.command_interpreter.sequence_handler.audio_handler.get_music_volume()
                    sfx_volume_status = self.command_interpreter.sequence_handler.audio_handler.get_sfx_volume()
                    settings_list.append ({'random_actions_status':random_actions_status})
                    settings_list.append ({'music_volume_status':music_volume_status})
                    settings_list.append ({'sfx_volume_status':sfx_volume_status})
                    await self.dispatch_message(settings_list, "show_configuration", "terminal") #TODO , mqueue_message.reply)
                else:
                    reply_message = await self.command_interpreter.process_command(command)
                    await self.dispatch_message(reply_message, "terminal_command_reply", "terminal") #TODO , mqueue_message.reply)
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
