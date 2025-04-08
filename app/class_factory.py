from terminal_interpreter import TerminalInterpreter
from state_tracker import state_tracker
from sequence import SequencesHandler
from dunebugger_settings import settings
from mqueue import ZeroMQComm
from mqueue_handler import MessagingQueueHandler
from gpio_handler import GPIOHandler, GPIO
from audio_handler import AudioPlayer
from motor import MotorController

mygpio_handler = GPIOHandler(state_tracker)
audio_handler = AudioPlayer()
motor_handler = MotorController(mygpio_handler, GPIO)
sequence_handler = SequencesHandler(mygpio_handler, GPIO,  audio_handler, state_tracker, motor_handler)
terminal_interpreter = TerminalInterpreter(mygpio_handler, sequence_handler, motor_handler)
mqueue_handler = MessagingQueueHandler(state_tracker, sequence_handler, mygpio_handler, terminal_interpreter)
mqueue_listener = ZeroMQComm(
    mode="REP",
    address=settings.mQueueListenerAddress,
    mqueue_handler=mqueue_handler,
)
mqueue_sender = ZeroMQComm(
    mode="REQ",
    address=settings.mQueueSenderAddress,
    mqueue_handler=mqueue_handler,
)

mqueue_handler.mqueue_sender = mqueue_sender
terminal_interpreter.mqueue_handler = mqueue_handler
mqueue_handler.monitor_thread.start()
