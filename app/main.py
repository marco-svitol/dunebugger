#!/usr/bin/env python3
import asyncio
from dunebugger_settings import settings
from class_factory import terminal_interpreter, mqueue, mqueue_handler


async def main():
    await mqueue.start()

    # Start the mqueue monitoring task
    await mqueue_handler.start_monitoring()

    # comment lines below to make a real server
    # await terminal_interpreter.process_terminal_input(settings.initializationCommandsString)
    await terminal_interpreter.terminal_listen()


if __name__ == "__main__":
    asyncio.run(main())
