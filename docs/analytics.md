# Analytics Module Documentation

## Overview

The `analytics.py` module provides functionality to parse dunebugger logs and extract metrics about "Start button pressed" events.

## Features

- **Dual Log Source Support**:
  - Production: Reads logs from systemd journal via `journalctl -u dunebugger.service`
  - Development: Reads logs from the `dunebugger.log` file
  
- **Automatic Detection**: Automatically detects whether the app is running as a systemd service and selects the appropriate log source

- **Metrics Collection**: Counts and extracts timestamps of all "Start button pressed" events

## Class: LogAnalytics

### Initialization

```python
from analytics import LogAnalytics
from dunebugger_logging import get_log_file_path

# Initialize with default settings
analytics = LogAnalytics()

# Or specify custom paths
analytics = LogAnalytics(
    systemd_service_name="dunebugger.service",
    log_file_path="/path/to/dunebugger.log"
)

# Get log file path from configuration
log_path = get_log_file_path()
analytics = LogAnalytics(log_file_path=log_path)
```

### Methods

#### `get_metrics(since=None)`

Get analytics metrics for start button presses.

**Parameters:**
- `since` (Optional[str]): Time filter for systemd logs (e.g., "today", "1 week ago", "2025-01-01")

**Returns:**
Dictionary containing:
- `count`: Total number of start button presses
- `timestamps`: List of datetime objects for each press
- `first_press`: First press timestamp (or None)
- `last_press`: Last press timestamp (or None)
- `log_source`: Source of logs ("systemd" or "file")

**Example:**
```python
metrics = analytics.get_metrics()
print(f"Total presses: {metrics['count']}")
print(f"First press: {metrics['first_press']}")

# Get metrics for today only (systemd)
metrics = analytics.get_metrics(since="today")
```

#### `format_metrics_summary(metrics)`

Format metrics into a human-readable summary string.

**Example:**
```python
metrics = analytics.get_metrics()
summary = analytics.format_metrics_summary(metrics)
print(summary)
```

#### `is_running_as_systemd()`

Check if the application is running as a systemd service.

**Returns:** `bool`

#### `get_start_button_events(since=None)`

Get list of datetime objects for each start button press event.

**Returns:** `List[datetime]`

## Log Patterns

### Systemd Journal Pattern
```
Jan 10 17:46:19 rpi4bDB2025 python[596]: INFO - 10/01/2026 17:46:19 : Start button pressed
```
The module extracts the timestamp: `10/01/2026 17:46:19`

### File Log Pattern
```
INFO - 05/01/2026 15:40:38 : Start button pressed
```
The module extracts the timestamp: `05/01/2026 15:40:38`

## Helper Functions

### `dunebugger_logging.get_log_file_path()`

Reads the `dunebuggerlogging.conf` file and extracts the log file path.

**Module:** `dunebugger_logging`

**Returns:** `Optional[str]` - Absolute path to the log file, or None if not found

**Example:**
```python
from dunebugger_logging import get_log_file_path

log_path = get_log_file_path()
```

## Usage Example

### Basic Usage

```python
from analytics import LogAnalytics
from dunebugger_logging import get_log_file_path

# Initialize
log_file = get_log_file_path()
analytics = LogAnalytics(log_file_path=log_file)

# Get metrics
metrics = analytics.get_metrics()

# Display summary
print(analytics.format_metrics_summary(metrics))
```

### With Time Filtering (Systemd)

```python
# Get metrics for today only
metrics = analytics.get_metrics(since="today")

# Get metrics for the last week
metrics = analytics.get_metrics(since="1 week ago")

# Get metrics since specific date
metrics = analytics.get_metrics(since="2026-01-01")
```

### Access Individual Timestamps

```python
metrics = analytics.get_metrics()

for i, timestamp in enumerate(metrics['timestamps'], 1):
    print(f"Press {i}: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
```

## Testing

Run the test script:

```bash
cd /home/marco/dev/dunebugger-project/dunebugger
python test_analytics.py
```

Or if executable:

```bash
./test_analytics.py
```

## Notes

- The module only tracks "Start button pressed" log entries
- All other log entries are ignored
- Timestamps are parsed in MM/DD/YYYY HH:MM:SS format
- Invalid timestamp formats are silently skipped
- For systemd logs, the module uses the timestamp from the Python log entry, not the systemd timestamp

## Future Enhancements

- Integration with terminal commands
- Integration with message queue for remote monitoring
- Additional metrics (average time between presses, daily/weekly aggregations, etc.)
- Export metrics to JSON/CSV formats
