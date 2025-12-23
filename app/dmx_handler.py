# dmx_handler.py
"""
DMX controller for ENTTEC DMX USB Pro (for Raspberry Pi)

Features:
- set_rgb(channel, r, g, b): Set RGB values for a PAR starting at channel
- fade_to_rgb(channel, r, g, b, duration): Fade RGB to target over duration (seconds)
- set_dimmer(channel, intensity): Set dimmer intensity (0.0-1.0) while maintaining color ratios
- fade_to_dimmer(channel, intensity, duration): Fade to dimmer intensity over time
- set_scene(scene_name): Set predefined scenes
- Non-blocking fades using threading

Example usage:
    dmx = DMXController('/dev/ttyUSB0')
    dmx.connect()
    dmx.set_rgb(1, 255, 100, 50)
    dmx.fade_to_rgb(1, 0, 0, 255, 2.0)
    dmx.set_dimmer(1, 0.5)  # 50% brightness
    dmx.fade_to_dimmer(1, 0.8, 3.0)  # Fade to 80% over 3 seconds
    dmx.set_scene('warm_white')
"""
import time
import threading
import serial
from dunebugger_logging import logger

SCENES = {
    'warm_white': (255, 180, 80),
    'cool_white': (180, 220, 255),
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'yellow': (255, 255, 0),
    'orange': (255, 165, 0),
}

class DMXController:
    def __init__(self, port, baudrate=57600, universe_size=512):
        self.port = port
        self.baudrate = baudrate
        self.universe = bytearray([0] * universe_size)
        self.serial_conn = None
        self._fade_tasks = {}
        self._lock = threading.Lock()
        self.connect()

    def connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            reply_message = self._send_dmx()
            if reply_message is not None:
                logger.error(f"DMX connection error: {reply_message}")
            else:
                logger.info(f"DMX connected to {self.port}")
        except Exception as e:
            logger.error(f"Failed to connect DMX: {e}")

    def set_rgb(self, start_channel, r, g, b):
        with self._lock:
            self.universe[start_channel-1:start_channel+2] = bytes([r, g, b])
            self._send_dmx()

    def fade_to_rgb(self, start_channel, r, g, b, duration):
        # Stop any existing fade for this channel
        fade_key = f"fade_{start_channel}"
        if fade_key in self._fade_tasks:
            self._fade_tasks[fade_key] = False  # Signal to stop
        
        # Start new fade in background thread
        self._fade_tasks[fade_key] = True
        fade_thread = threading.Thread(
            target=self._fade_worker, 
            args=(start_channel, r, g, b, duration, fade_key),
            daemon=True
        )
        fade_thread.start()

    def _fade_worker(self, start_channel, r, g, b, duration, fade_key):
        try:
            with self._lock:
                current = list(self.universe[start_channel-1:start_channel+2])
            target = [r, g, b]
            steps = int(duration * 30)
            
            for i in range(1, steps+1):
                if not self._fade_tasks.get(fade_key, False):  # Check if cancelled
                    break
                    
                intermediate = [
                    int(current[j] + (target[j] - current[j]) * i / steps)
                    for j in range(3)
                ]
                with self._lock:
                    self.universe[start_channel-1:start_channel+2] = bytes(intermediate)
                    self._send_dmx()
                time.sleep(duration / steps)
            
            # Clean up
            if fade_key in self._fade_tasks:
                del self._fade_tasks[fade_key]
        except Exception as e:
            logger.error(f"DMX fade error: {e}")

    def fade_to_scene(self, scene_name, start_channel=1, duration=2.0):
        rgb = SCENES.get(scene_name)
        if rgb:
            self.fade_to_rgb(start_channel, *rgb, duration)
        else:
            raise ValueError(f"Scene '{scene_name}' not defined")

    def set_scene(self, scene_name, start_channel=1):
        rgb = SCENES.get(scene_name)
        if rgb:
            self.set_rgb(start_channel, *rgb)
        else:
            raise ValueError(f"Scene '{scene_name}' not defined")
        
    def set_dimmer(self, intensity, start_channel):
        """
        Set the dimmer intensity for RGB channels while maintaining color ratios.
        
        Args:
            start_channel (int): Starting DMX channel (1-based)
            intensity (float): Intensity level from 0.0 (off) to 1.0 (full brightness)
        """
        intensity = max(0.0, min(1.0, intensity))  # Clamp between 0 and 1
        
        with self._lock:
            current_rgb = list(self.universe[start_channel-1:start_channel+2])
            # Apply intensity scaling to current RGB values
            dimmed_rgb = [int(value * intensity) for value in current_rgb]
            self.universe[start_channel-1:start_channel+2] = bytes(dimmed_rgb)
            self._send_dmx()

    def fade_to_dimmer(self, intensity, start_channel, duration):
        """
        Fade to a specific dimmer intensity over time.
        
        Args:
            start_channel (int): Starting DMX channel (1-based)
            intensity (float): Target intensity level from 0.0 to 1.0
            duration (float): Fade duration in seconds
        """
        intensity = max(0.0, min(1.0, intensity))  # Clamp between 0 and 1
        
        # Stop any existing fade for this channel
        fade_key = f"dimmer_fade_{start_channel}"
        if fade_key in self._fade_tasks:
            self._fade_tasks[fade_key] = False  # Signal to stop
        
        # Start new dimmer fade in background thread
        self._fade_tasks[fade_key] = True
        fade_thread = threading.Thread(
            target=self._dimmer_fade_worker, 
            args=(start_channel, intensity, duration, fade_key),
            daemon=True
        )
        fade_thread.start()

    def _dimmer_fade_worker(self, start_channel, target_intensity, duration, fade_key):
        """Worker thread for dimmer fading."""
        with self._lock:
            current_rgb = list(self.universe[start_channel-1:start_channel+2])
        
        # Calculate current intensity (max of RGB values normalized to 0-1)
        max_current = max(current_rgb)
        current_intensity = max_current / 255.0 if max_current > 0 else 0.0
        
        # Store the original color ratios
        if max_current > 0:
            color_ratios = [value / max_current for value in current_rgb]
        else:
            color_ratios = [1.0, 1.0, 1.0]  # Default to white if all zeros
        
        steps = int(duration * 30)  # 30 FPS
        
        for i in range(1, steps+1):
            if not self._fade_tasks.get(fade_key, False):  # Check if cancelled
                break
                
            # Interpolate intensity
            intermediate_intensity = current_intensity + (target_intensity - current_intensity) * i / steps
            
            # Apply intensity to color ratios
            intermediate_rgb = [
                int(ratio * intermediate_intensity * 255)
                for ratio in color_ratios
            ]
            
            with self._lock:
                self.universe[start_channel-1:start_channel+2] = bytes(intermediate_rgb)
                self._send_dmx()
            time.sleep(duration / steps)
        
        # Clean up
        if fade_key in self._fade_tasks:
            del self._fade_tasks[fade_key]

    def fade_dimmer(self, start_channel, intensity, duration):
        """
        Fade dimmer to a specific intensity over time.
        This is an alias for fade_to_dimmer for consistency with command naming.
        
        Args:
            start_channel (int): Starting DMX channel (1-based)
            intensity (float): Target intensity level from 0.0 to 1.0
            duration (float): Fade duration in seconds
        """
        self.fade_to_dimmer(intensity, start_channel, duration)

    def _send_dmx(self):
        # ENTTEC DMX USB Pro: send DMX packet (see protocol)
        # Start code: 0x7E, Label: 6, Length: 513, Data: [0]+universe, End: 0xE7
        data = bytes([0x7E, 6, 0x02, 0x02, 0x00]) + bytes([0]) + self.universe + bytes([0xE7])
        self.serial_conn.write(data)
        self.serial_conn.flush()
            
    def disconnect(self):
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
            logger.info("DMX disconnected")
    
    def __del__(self):
        self.disconnect()

    def validate_dmx_command_args(self, args):
        if not args or len(args) == 0:
            return ("Usage: dmx <command> <channel> <scene_or_value> [duration]\n"
                "Commands:\n"
                "  set <channel> <scene>\n"
                "  fade <channel> <scene> [duration]\n"
                "  dimmer <channel> <value 0.0-1.0>\n"
                "  fade_dimmer <channel> <value 0.0-1.0> [duration]\n"
                "Scenes: warm_white, cool_white, red, green, blue, yellow, orange")
        
        dmx_command = args[0].lower()
        valid_commands = {"set", "fade", "dimmer", "fade_dimmer"}
        if dmx_command not in valid_commands:
            return (f"Invalid DMX command: {dmx_command}. Valid commands: set, fade, dimmer, fade_dimmer.\n"
                "Usage: dmx <command> <channel> <scene_or_value> [duration]")
        
        # Command present but missing further arguments
        if len(args) == 1:
            if dmx_command in ("set", "fade"):
                return f"Missing arguments. Usage: dmx {dmx_command} <channel> <scene>{' [duration]' if dmx_command == 'fade' else ''}. Scenes: warm_white, cool_white, red, green, blue, yellow, orange"
            elif dmx_command == "dimmer":
                return "Missing arguments. Usage: dmx dimmer <channel> <value 0.0-1.0>"
            elif dmx_command == "fade_dimmer":
                return "Missing arguments. Usage: dmx fade_dimmer <channel> <value 0.0-1.0> [duration]"
        
        if len(args) == 2:
            channel = args[1]
            if not channel.isdigit() or not (1 <= int(channel) <= 512):
                return f"Invalid or missing channel: {channel}. Channel must be an integer 1-512."
            if dmx_command in ("set", "fade"):
                return f"Missing scene. Usage: dmx {dmx_command} {channel} <scene>{' [duration]' if dmx_command == 'fade' else ''}. Scenes: warm_white, cool_white, red, green, blue, yellow, orange"
            elif dmx_command == "dimmer":
                return f"Missing dimmer value. Usage: dmx dimmer {channel} <value 0.0-1.0>"
            elif dmx_command == "fade_dimmer":
                return f"Missing dimmer value. Usage: dmx fade_dimmer {channel} <value 0.0-1.0> [duration]"
            
        if len(args) == 3 and dmx_command in ("fade", "fade_dimmer"):
            # Third arg present; duration optional, handled later (defaults)
            pass

        # Validate channel: args[1] must be an integer between 1 and 512
        channel = args[1]
        if not channel.isdigit() or not (1 <= int(channel) <= 512):
            return f"Invalid DMX channel: {channel}. Must be an integer between 1 and 512"
        channel = int(channel)

        # Validate scene_or_value: args[2] must be a valid scene name or a float between 0.0 and 1.0
        scene_or_value = args[2]
        if dmx_command in ["set", "fade"]:
            if scene_or_value not in ["warm_white", "cool_white", "red", "green", "blue", "yellow", "orange"]:
                return f"Invalid DMX scene: {scene_or_value}. Must be one of 'warm_white', 'cool_white', 'red', 'green', 'blue', 'yellow', 'orange'"
        elif dmx_command in ["dimmer", "fade_dimmer"]:
            try:
                scene_or_value = float(scene_or_value)
                if not (0.0 <= scene_or_value <= 1.0):
                    return f"Invalid DMX dimmer value: {scene_or_value}. Must be a float between 0.0 and 1.0"
            except ValueError:
                return f"Invalid DMX dimmer value: {scene_or_value}. Must be a float between 0.0 and 1.0"
        
        # Validate duration for fade commands
        duration = 2.0  # Default duration
        if len(args) == 4 and dmx_command in ["fade", "fade_dimmer"]:
            duration = args[3]
            if not duration.replace('.', '', 1).isdigit() and float(duration) < 0:
                return f"Invalid duration value: {duration}. Must be a positive number"
            duration = float(duration)
        
        return (None, dmx_command, channel, scene_or_value, duration)