from command_interpreter import CommandInterpreter
from terminal_interpreter import TerminalInterpreter
from state_tracker import state_tracker
from sequence import SequencesHandler
from modes_handler import ModesHandler
from dunebugger_settings import settings
from mqueue import NATSComm, NullNATSComm
from mqueue_handler import MessagingQueueHandler
from gpio_handler import GPIOHandler, GPIO
from audio_handler import AudioPlayer
from motor import MotorController
from dmx_handler import DMXController
from random_actions_handler import RandomActions
from cycle_handler import CycleHandler
from analytics import LogAnalytics
from dunebugger_logging import get_log_file_path

mygpio_handler = GPIOHandler(state_tracker)
cycle_handler = CycleHandler(mygpio_handler, state_tracker, GPIO)
audio_handler = AudioPlayer()
motor_handler = MotorController(mygpio_handler, GPIO)
dmx_handler = DMXController(settings.dmxSerialPort, settings.dmxBaudRate)
analytics_handler = LogAnalytics("dunebugger.service", get_log_file_path())

command_interpreter = CommandInterpreter(mygpio_handler, dmx_handler, motor_handler, audio_handler, cycle_handler, analytics_handler)
random_actions_handler = RandomActions(mygpio_handler, state_tracker)
sequence_handler = SequencesHandler(random_actions_handler, state_tracker, command_interpreter, cycle_handler)
modes_handler = ModesHandler(state_tracker, command_interpreter)
terminal_interpreter = TerminalInterpreter(command_interpreter)
mqueue_handler = MessagingQueueHandler(sequence_handler, mygpio_handler, command_interpreter, cycle_handler)

# Only create NATS connection if enabled
if settings.mQueueEnabled:
    mqueue = NATSComm(
        nat_servers=settings.mQueueServers,
        client_id=settings.mQueueClientID,
        subject_root=settings.mQueueSubjectRoot,
        mqueue_handler=mqueue_handler,
    )
    mqueue_handler.mqueue_sender = mqueue
else:
    mqueue = NullNATSComm()
    
command_interpreter.sequence_handler = sequence_handler
command_interpreter.modes_handler = modes_handler
command_interpreter.mqueue_handler = mqueue_handler
state_tracker.mqueue_handler = mqueue_handler
cycle_handler.sequence_handler = sequence_handler