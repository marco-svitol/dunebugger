# dmx_handler.py
"""
DMX controller for ENTTEC DMX USB Pro (for Raspberry Pi)

Features:
- set_rgb(channel, r, g, b): Set RGB values for a PAR starting at channel
- fade_to_rgb(channel, r, g, b, duration): Fade RGB to target over duration (seconds)
- set_scene(scene_name): Set predefined scenes
- Non-blocking fades using threading

Example usage:
    dmx = DMXController('/dev/ttyUSB0')
    dmx.connect()
    dmx.set_rgb(1, 255, 100, 50)
    dmx.fade_to_rgb(1, 0, 0, 255, 2.0)
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
}

class DMXController:
    def __init__(self, port, universe_size=512):
        self.port = port
        self.universe = bytearray([0] * universe_size)
        self.serial_conn = None
        self._fade_tasks = {}
        self._lock = threading.Lock()

    def connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, baudrate=57600, timeout=1)
            self._send_dmx()
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

    def fade_to_scene(self, scene_name, start_channel=1, duration=2.0):
        rgb = SCENES.get(scene_name)
        if rgb:
            self.fade_to_rgb(start_channel, *rgb, duration)

    def set_scene(self, scene_name, start_channel=1):
        rgb = SCENES.get(scene_name)
        if rgb:
            self.set_rgb(start_channel, *rgb)

    def _send_dmx(self):
        if not self.serial_conn:
            return
        try:
            # ENTTEC DMX USB Pro: send DMX packet (see protocol)
            # Start code: 0x7E, Label: 6, Length: 513, Data: [0]+universe, End: 0xE7
            data = bytes([0x7E, 6, 0x02, 0x02, 0x00]) + bytes([0]) + self.universe + bytes([0xE7])
            self.serial_conn.write(data)
            self.serial_conn.flush()
        except Exception as e:
            logger.error(f"DMX send error: {e}")

    def disconnect(self):
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
            logger.info("DMX disconnected")
