from command_interpreter import CommandInterpreter
from terminal_interpreter import TerminalInterpreter
from state_tracker import state_tracker
from sequence import SequencesHandler
from dunebugger_settings import settings
from mqueue import NATSComm, NullNATSComm
from mqueue_handler import MessagingQueueHandler
from gpio_handler import GPIOHandler, GPIO
from audio_handler import AudioPlayer
from motor import MotorController
from dmx_handler import DMXController
from initialization_handler import InitializationHandler

mygpio_handler = GPIOHandler(state_tracker)
audio_handler = AudioPlayer()

# Only create motor controller if enabled
if settings.motorEnabled:
    motor_handler = MotorController(mygpio_handler, GPIO)
else:
    motor_handler = None

dmx_handler = DMXController(settings.dmxSerialPort, settings.dmxBaudRate)
sequence_handler = SequencesHandler(mygpio_handler, GPIO, audio_handler, state_tracker, motor_handler, dmx_handler)
command_interpreter = CommandInterpreter(mygpio_handler, sequence_handler)
initialization_handler = InitializationHandler(command_interpreter)
terminal_interpreter = TerminalInterpreter(command_interpreter)
mqueue_handler = MessagingQueueHandler(sequence_handler, mygpio_handler, command_interpreter)

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
    # Don't set mqueue_sender for disabled NATS

command_interpreter.mqueue_handler = mqueue_handler
state_tracker.mqueue_handler = mqueue_handler
