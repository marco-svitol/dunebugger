import zmq
import threading
import atexit
import json

class ZeroMQComm:
    def __init__(self, mode, address, mqueue_handler, topic=""):
        """
        Initialize the ZeroMQ communication module.

        :param mode: 'REQ' for request-response or 'SUB' for subscription.
        :param address: The ZeroMQ address (default: IPC socket).
        :param topic: Topic for PUB/SUB mode (default: empty for all topics).
        """
        self.context = zmq.Context()
        self.mode = mode
        self.address = address
        self.topic = topic
        self.socket = None
        self.connect()
        self.listener_thread = None
        self.mqueue_handler = mqueue_handler
        self.stop_event = threading.Event()
        atexit.register(self.close)

    def connect(self):
        if self.mode == "REQ":
            self.socket = self.context.socket(zmq.REQ)
            self.socket.connect(self.address)
        elif self.mode == "REP":
            self.socket = self.context.socket(zmq.REP)
            self.socket.bind(self.address)
        else:
            raise ValueError("Invalid mode. Use 'REQ' or 'REP'.")

    def send(self, message):
        """
        Send a request and wait for a reply (REQ mode).
        """
        if self.mode != "REQ":
            raise RuntimeError("send is only supported in REQ mode.")
        
        compact_message = json.dumps(message, separators=(",", ":"))
        print(f"Sending message: {compact_message}")  # Debug log
        self.socket.send_string(compact_message)
        reply = self.socket.recv_string()
        print(f"Received reply: {reply}")  # Debug log
        return reply
    
    def listen(self):
        """
        Listen for incoming messages and send a reply (REP mode).
        """
        if self.mode != "REP":
            raise RuntimeError("listen is only supported in REP mode.")
        
        print(f"Listening for messages on {self.address}...")
        while not self.stop_event.is_set():
            try:
                # Wait for a request
                message = self.socket.recv_string()
                print(f"Received message: {message}")  # Debug log
                # Process the message and generate a reply
                reply = self.mqueue_handler.process_message(message)
                # Send the reply
                self.socket.send_string(reply)
                print(f"Sent reply: {reply}")  # Debug log
            except zmq.ZMQError as e:
                if not self.stop_event.is_set():
                    print(f"ZeroMQ error: {e}")
            except Exception as e:
                print(f"Error in listener: {e}")

    def start_listener(self):
        """
        Start the listener thread for REP mode.
        """
        if self.mode != "REP":
            raise RuntimeError("Listener is only supported in REP mode.")
        
        self.listener_thread = threading.Thread(target=self.listen, daemon=True)
        self.listener_thread.start()

    def stop_listener(self):
        """Stop the listener thread."""
        self.stop_event.set()
        if self.listener_thread:
            self.listener_thread.join()

    def close(self):
        """Close the ZeroMQ socket and terminate the context."""
        self.stop_listener()
        if self.socket:
            self.socket.close()
        self.context.term()
