#!/usr/bin/env python3
import asyncio

# from dunebugger_settings import settings
from class_factory import terminal_interpreter, mqueue, state_tracker, initialization_handler
from dunebugger_logging import update_queue_logging_handler_loop


async def main():
    try:
        # Queue logging helper: update queue handler with the current event loop
        update_queue_logging_handler_loop()
        
        # Start NATS connection manager (non-blocking)
        await mqueue.start_listener()
        # Wait some seconds to allow NATS connection establishment
        await asyncio.sleep(2)
        # Start the state monitoring task
        await state_tracker.start_state_monitoring()

        # Execute initialization commands if any
        await initialization_handler.execute_initialization_commands()

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
