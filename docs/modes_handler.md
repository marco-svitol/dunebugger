# Modes Handler Documentation

## Overview

The `ModesHandler` class manages "modes" files (`.mod` extension) that define system states with metadata and a list of commands to execute. Unlike sequence files, mode files do not require timestamp management.

## File Structure

Mode files use INI/ConfigParser format with two required sections:

### Example: standby.mod

```ini
[metadata]
name = Stand-by
desc = Pronto per l'avvio, solo luci essenziali

[commands]
start_button = start_button enable
random_actions = random_actions disable
audio_music = audio music_volume 80
audio_sfx = audio sfx_volume 80
switch_lucestart = switch 12VLuceStart on
switch_lunastelle = switch 220VLunaStelle off
switch_alwayson = switch 220VAlwaysOn on
switch_case1 = switch 220VCase1 off
switch_fuochi = switch 220VFuochi on
switch_acqua = switch 220VAcquaCornice off
```

## Configuration

Add to `dunebugger.conf`:

```ini
[General]
modesFolder = /opt/dunebugger-data/modes
```

## Commands

### Execute a Mode

```bash
mode execute <mode_name>
```

Example:
```bash
mode execute standby
```

This will execute all commands defined in `standby.mod` in the order they appear.

### List Available Modes

```bash
mode list
```

This will return a JSON object with all available modes and their metadata:
```json
{
  "modes": [
    {
      "filename": "standby.mod",
      "mode_name": "standby",
      "name": "Stand-by",
      "desc": "Pronto per l'avvio, solo luci essenziali"
    }
  ]
}
```

### Validate All Modes

```bash
mode validate
```

Re-validates all mode files in the modes folder. Useful after configuration changes or when mode files are updated.

### Upload a Mode File

```bash
mode upload <filename> <file_content>
```

Upload a new mode file or update an existing one. The file content should have escaped newlines (`\n`).

Example:
```bash
mode upload standby.mod "[metadata]\nname = Stand-by\ndesc = Ready to start\n\n[commands]\nstart_button = start_button enable\nrandom_actions = random_actions disable"
```

The upload command will:
- Validate the filename (must end with `.mod`)
- Create a backup if the file already exists
- Validate the file content structure and commands
- Write the file to the modes folder
- Notify state tracker of the change

## ModesHandler Class

### Initialization

```python
modes_handler = ModesHandler(state_tracker, command_interpreter)
modes_handler.initialize()
```

### Key Methods

#### `execute_mode_command(args)`
Execute mode commands with subcommands.
- **args**: List with subcommand and arguments:
  - `['execute', 'standby']` - Execute standby mode
  - `['list']` - List all modes with metadata
  - `['validate']` - Re-validate all mode files
  - `['upload', 'filename.mod', 'content']` - Upload a mode file

Returns success message, modes list JSON, or raises ValueError/RuntimeError.

#### `get_modes_list_with_metadata()`
Retrieve all modes with their metadata in JSON format.

Returns:
```json
{
  "modes": [
    {
      "filename": "standby.mod",
      "mode_name": "standby",
      "name": "Stand-by",
      "desc": "Pronto per l'avvio, solo luci essenziali"
    }
  ]
}
```

#### `get_mode_details(mode_name)`
Get detailed information about a specific mode.

Returns:
```json
{
  "mode_name": "standby",
  "name": "Stand-by",
  "desc": "Pronto per l'avvio, solo luci essenziali",
  "commands": {
    "start_button": "start_button enable",
    "audio_music": "audio music_volume 80",
    ...
  }
}
```

#### `validate_all_mode_files(directory)`
Validates all `.mod` files in the specified directory:
- Checks required sections (`[metadata]` and `[commands]`)
- Validates metadata fields (`name` and `desc`)
- Performs dry run on all commands to ensure validity

#### `upload_mode_file(filename, file_content)`
Upload a new mode file:
- Validates filename (must end with `.mod`)
- Creates backup if file exists
- Validates content before writing
- Returns upload status with file paths

#### `get_state()`
Get current modes handler state.

Returns:
```json
{
  "modes_validated": true,
  "modes_count": 3,
  "available_modes": ["standby", "play", "off"]
}
```

## Integration

### Command Interpreter

The mode command is registered in `commands.conf`:

```ini
mode = handle_mode, "[execute <mode_name>|list]: execute a mode or list available modes"
```

Handler method in `command_interpreter.py`:

```python
def handle_mode(self, args=None, dry_run=False):
    return self.modes_handler.execute_mode_command(args, dry_run=dry_run)
```

### Class Factory

Modes handler is instantiated in `class_factory.py`:

```python
modes_handler = ModesHandler(state_tracker, command_interpreter)
command_interpreter.modes_handler = modes_handler
```

### Main Application

Initialized in `main.py`:

```python
from class_factory import modes_handler

async def main():
    sequence_handler.initialize()
    modes_handler.initialize()
    # ... rest of initialization
```

## Usage Examples

### Execute a Mode

```python
# Via command interpreter
command_interpreter.process_command("mode execute standby")

# Direct call
modes_handler.execute_mode_command(['execute', 'standby'])
```

### List Available Modes

```python
# Via command interpreter
result = command_interpreter.process_command("mode list")

# Direct call
modes_list = modes_handler.execute_mode_command(['list'])
print(modes_list['modes'])
```

### Validate All Modes

```python
# Via command interpreter
result = command_interpreter.process_command("mode validate")

# Direct call
result = modes_handler.execute_mode_command(['validate'])
```

### Upload a Mode File

```python
# Via command interpreter
mode_content = "[metadata]\\nname = Stand-by\\ndesc = Ready\\n\\n[commands]\\nstart_button = start_button enable"
result = command_interpreter.process_command(f"mode upload standby.mod {mode_content}")

# Direct call
result = modes_handler.execute_mode_command(['upload', 'standby.mod', mode_content])

# Or using the direct method
result = modes_handler.upload_mode_file('standby.mod', "[metadata]\nname = Stand-by\ndesc = Ready\n\n[commands]\nstart_button = start_button enable")
```

### Get Modes with Metadata (Alternative)

```python
modes_list = modes_handler.get_modes_list_with_metadata()
print(modes_list['modes'])
```

### Get Mode State

```python
state = modes_handler.get_state()
print(f"Validated: {state['modes_validated']}")
print(f"Available modes: {state['available_modes']}")
```

## Error Handling

The modes handler raises specific exceptions:

- **ValueError**: Invalid arguments, missing mode, or invalid mode file structure
- **FileNotFoundError**: Mode file or directory not found
- **RuntimeError**: Command execution errors or validation failures
- **OSError**: Directory access errors

All errors are logged and propagated to the caller.

## Comparison with Sequences

| Feature | Sequences | Modes |
|---------|-----------|-------|
| File Extension | `.seq` | `.mod` |
| Timestamps | Required | Not needed |
| Format | Custom (time + command) | INI/ConfigParser |
| Metadata | No | Yes (name, desc) |
| Execution | Sequential with timing | Immediate sequential |
| Use Case | Timed choreography | System state configuration |

## Notes

- Mode files are validated on initialization
- Commands are executed in the order they appear in the file
- Each command is validated with a dry run before actual execution
- State changes trigger notifications via `state_tracker`
- The modes folder path is configurable in `dunebugger.conf`
