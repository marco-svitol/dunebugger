import os
import threading
from terminal_interpreter import terminal_interpreter
from dunebugger_settings import settings

class PipeListener:
    def __init__(self):
        self.pipe_path = settings.pipePath
        if not os.path.exists(self.pipe_path):
            os.mkfifo(self.pipe_path)
    
    def pipe_input_thread(self):
        with open(self.pipe_path, 'r') as pipe:
            while True:
                command = pipe.readline().strip()
                if command:
                    terminal_interpreter.process_terminal_input(command)

    def pipe_listen(self):
        # Start a separate thread for reading from the named pipe
        pipe_thread = threading.Thread(target=self.pipe_input_thread, daemon=True)
        pipe_thread.start()
    
    def pipe_send(self, stream):
        with open(self.pipe_path, 'w') as pipe:
            pipe.write(stream + "\n")

pipe_listener = PipeListener()