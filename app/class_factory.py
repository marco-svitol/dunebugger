from command_interpreter import CommandInterpreter
from terminal_interpreter import TerminalInterpreter
from state_tracker import state_tracker
from sequence import SequencesHandler
from dunebugger_settings import settings
from mqueue import NATSComm
from mqueue_handler import MessagingQueueHandler
from gpio_handler import GPIOHandler, GPIO
from audio_handler import AudioPlayer
from motor import MotorController
from initialization_handler import InitializationHandler

mygpio_handler = GPIOHandler(state_tracker)
audio_handler = AudioPlayer()
motor_handler = MotorController(mygpio_handler, GPIO)
sequence_handler = SequencesHandler(mygpio_handler, GPIO, audio_handler, state_tracker, motor_handler)
command_interpreter = CommandInterpreter(mygpio_handler, sequence_handler)
initialization_handler = InitializationHandler(command_interpreter)
terminal_interpreter = TerminalInterpreter(command_interpreter)
mqueue_handler = MessagingQueueHandler(sequence_handler, mygpio_handler, command_interpreter)
mqueue = NATSComm(
    nat_servers=settings.mQueueServers,
    client_id=settings.mQueueClientID,
    subject_root=settings.mQueueSubjectRoot,
    mqueue_handler=mqueue_handler,
)

mqueue_handler.mqueue_sender = mqueue
command_interpreter.mqueue_handler = mqueue_handler
state_tracker.mqueue_handler = mqueue_handler
