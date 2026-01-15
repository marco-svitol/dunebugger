#!/usr/bin/env python3
import asyncio

# print component version info on startup
from version import get_version_info
print(f"Dunebugger core version: {get_version_info()['full_version']}, build type: {get_version_info()['build_type']}, build number: {get_version_info()['build_number']}")

from class_factory import terminal_interpreter, mqueue, state_tracker, sequence_handler, modes_handler
from dunebugger_logging import update_queue_logging_handler_loop


async def main():
    try:
        # Queue logging helper: update queue handler with the current event loop
        update_queue_logging_handler_loop()
        
        # Initialize sequence and modes handlers
        sequence_handler.initialize()
        modes_handler.initialize()

        # Start NATS connection manager (non-blocking)
        await mqueue.start_listener()
        # Wait some seconds to allow NATS connection establishment
        await asyncio.sleep(2)
        # Start the state monitoring task
        await state_tracker.start_state_monitoring()

        # Terminal listener (blocking) will keep the program running
        # If you want to run other tasks, create them before this line
        # The listener will detect if an interactive terminal is available
        # and disable itself if not (e.g., running in a container or background)
        await terminal_interpreter.terminal_listen()
    
    finally:
        # Clean up resources when exiting
        print("Cleaning up resources...")
        
        # Stop the monitoring task
        try:
            await state_tracker.stop_state_monitoring()
            print("State monitoring stopped.")
        except Exception as e:
            print(f"Error stopping state monitoring: {e}")

        # Close NATS connection
        await mqueue.close_listener()
 
        print("Cleanup completed.")


if __name__ == "__main__":
    asyncio.run(main())
