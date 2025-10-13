#!/usr/bin/env python3
import asyncio

# from dunebugger_settings import settings
from class_factory import terminal_interpreter, mqueue, mqueue_handler
from dunebugger_logging import update_queue_logging_handler_loop


async def main():
    try:
        # Update queue handler with the current event loop
        update_queue_logging_handler_loop()
        
        await mqueue.start()

        # Start the mqueue monitoring task
        await mqueue_handler.start_monitoring()

        # comment lines below to make a real server
        # await terminal_interpreter.process_terminal_input(settings.initializationCommandsString)
        await terminal_interpreter.terminal_listen()
    
    finally:
        # Clean up resources when exiting
        print("Cleaning up resources...")
        
        # Stop the monitoring task
        try:
            await mqueue_handler.stop_monitoring()
            print("Message queue monitoring stopped.")
        except Exception as e:
            print(f"Error stopping mqueue monitoring: {e}")
        
        # Close NATS connection
        await mqueue.close()
 
        print("Cleanup completed.")


if __name__ == "__main__":
    asyncio.run(main())
