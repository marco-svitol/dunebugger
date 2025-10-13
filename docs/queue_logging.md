# Queue Logging Feature Documentation

## Overview

The queue logging feature allows the Dunebugger application to optionally send all log messages to the message queue in addition to the standard console and file outputs. This enables remote monitoring and logging capabilities.

## Configuration

### Enable/Disable Queue Logging

To enable or disable queue logging, modify the `sendLogsToQueue` setting in the configuration file:

**File:** `app/config/dunebugger.conf`

```ini
[Log]
dunebuggerLogLevel = DEBUG
sendLogsToQueue = True    # Set to True to enable, False to disable
```

- `sendLogsToQueue = True`: Logs will be sent to both stdout/file AND message queue
- `sendLogsToQueue = False`: Logs will only be sent to stdout/file (default behavior)

## Message Format

When queue logging is enabled, log messages are sent to the message queue with the following format:

**Subject:** `log_message`
**Recipient:** `remote`
**Message Body (JSON):**
```json
{
    "level": "INFO",
    "message": "The actual log message content without timestamp"
}
```

### Log Levels

The `level` field can contain any of the standard Python logging levels:
- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

### Message Content

The `message` field contains the raw log message content without the timestamp or level prefix, making it easy to process programmatically.

## Implementation Details

### How It Works

1. **Configuration Loading**: The `sendLogsToQueue` setting is loaded during application startup
2. **Handler Registration**: If enabled, a `QueueHandler` is added to the logger
3. **Async Message Dispatch**: Log messages are asynchronously sent to the queue using `dispatch_message()`
4. **Error Handling**: Queue send failures are silently ignored to prevent logging loops

### Key Components

- **QueueHandler Class**: Custom logging handler in `dunebugger_logging.py`
- **Configuration**: Added to the `[Log]` section in `dunebugger.conf`
- **Integration**: Enabled in `class_factory.py` during application initialization
- **Event Loop Management**: `update_queue_handler_loop()` called in `main.py` to handle threading

### Threading Support

The queue logging feature properly handles logs from different threads:

- **Main Thread**: Logs are sent directly using `asyncio.create_task()`
- **Background Threads**: Logs are sent using `asyncio.run_coroutine_threadsafe()` to safely cross thread boundaries
- **Event Loop Reference**: The handler maintains a reference to the main event loop for cross-thread operations

### Safety Features

- **No Blocking**: Queue sending is asynchronous and won't block the main application or background threads
- **Thread-Safe**: Properly handles logging from any thread, including sequence execution threads
- **Error Resilience**: If the queue is unavailable, logging continues normally to console/file
- **Loop Prevention**: Queue send errors are silently ignored to prevent infinite logging loops

## Usage Examples

### Remote Log Monitoring

When enabled, remote systems can subscribe to the `dunebugger.remote.log_message` subject to receive real-time log messages.

### Log Analysis

The structured JSON format makes it easy to:
- Filter by log level
- Search message content
- Aggregate log statistics
- Build monitoring dashboards

## Performance Considerations

- Queue logging adds minimal overhead due to async processing
- Messages are sent without timestamps to reduce payload size
- Failed queue sends don't impact application performance

## Troubleshooting

### Queue Logging Not Working

1. Verify `sendLogsToQueue = True` in `app/config/dunebugger.conf`
2. Check that the message queue connection is established
3. Ensure the application has proper permissions to send messages

### Missing Log Messages

- Queue logging only works when the message queue is connected
- Very early startup logs (before queue connection) won't be sent to queue
- Log level filtering still applies (e.g., DEBUG messages won't be sent if log level is INFO)