from utils import waituntil
from audio_handler import audioPlayer
from gpio_handler import RPiwrite, RPiToggle
import random
from dunebugger_settings import settings
import motor

def execute_command(command):
    # Ignore comments (commands starting with #)
    if command.startswith("#"):
        return

    parts = command.split()
    if len(parts) < 3:
        print("Invalid command:", command)
        return

    verb = parts[0].lower()
    if verb == "motor" and parts[1].lower() == "start":
        motor_number = int(parts[2])
        direction = parts[3].lower()
        speed = int(parts[4])

        # Check motor enabled settings before starting the motor
        motor_enabled = getattr(settings, f"motor{motor_number}Enabled", False)
        if motor_enabled:
            motor.start(motor_number, direction, speed)
    else:
        # Handle other commands
        device_name = parts[1]
        action = parts[2]

        if verb == "switch":
            if action.lower() == "on":
                RPiwrite(device_name, 1)
            elif action.lower() == "off":
                RPiwrite(device_name, 0)
            else:
                print("Unknown action:", action)
        elif verb == "waituntil":
            if len(parts) < 4:
                print("Invalid waituntil command:", command)
                return
            duration = int(parts[3])
            waituntil(duration)
        elif verb == "audio" and len(parts) >= 4 and action.lower() == "fadeout":
            fadeout_duration = int(parts[3])
            audioPlayer.vstopaudio(fadeout_duration)
        else:
            print("Unknown command:", command)

def read_sequence_file(file_path):
    """
    Reads commands from the specified file and executes them.

    Args:
        file_path (str): The path to the sequence file.
    """
    with open(file_path, "r") as file:
        for line in file:
            command = line.strip()
            if command:
                execute_command(command)

def random_sequence_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            randomizable = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return

    if not randomizable:
        print("No randomizable elements found in the file.")
        return

    rand_elem = random.choice(randomizable)
    RPiToggle(rand_elem)

# Example usage
read_sequence_file("presepe.seq")
random_sequence_from_file("random.seq")