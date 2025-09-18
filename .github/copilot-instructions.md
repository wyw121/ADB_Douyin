# Repository Instructions for GitHub Copilot

## Project Overview

This is an Android automation tool for Douyin (TikTok Chinese version) that uses ADB (Android Debug Bridge) to automatically follow contacts from the user's address book. The project is built with Python and implements UI automation through XML parsing and element identification.

**Primary Goal**: Automate the process of following friends from contacts in Douyin app using ADB connection and UI analysis.

## Repository Structure

```
ADB_Douyin/
├── main.py                 # Main program entry point with interactive menu
├── adb_connection.py      # ADB connection management and device communication
├── ui_analyzer.py         # UI XML parsing and element identification
├── douyin_automator.py    # Main automation logic for Douyin operations  
├── logs/                  # Log directory (auto-created)
│   ├── main.log          # Main operation logs
│   ├── debug.log         # Detailed debug information
│   └── error.log         # Error and exception logs
├── .github/
│   └── copilot-instructions.md  # This instructions file
└── README.md              # Project documentation
```

## Technology Stack

- **Language**: Python 3.7+
- **Primary Dependencies**: 
  - No external packages required (uses only standard library)
  - `subprocess` for ADB command execution
  - `xml.etree.ElementTree` for UI XML parsing
  - `logging` for comprehensive logging system
  - `time` for operation delays and timing

## Build and Run Instructions

### Prerequisites
1. **Python 3.7+** must be installed
2. **ADB (Android Debug Bridge)** must be installed and accessible in PATH
3. **Android device** with USB debugging enabled
4. **Douyin app** installed on the target device

### Environment Setup
```bash
# Verify ADB installation
adb version

# Connect Android device and verify
adb devices

# Should show your device in the list
```

### Running the Application
```bash
# Navigate to project directory
cd /path/to/ADB_Douyin

# Run the main program
python main.py
```

### Available Modes
1. **UI Analysis Mode** (`1`): Analyze current screen structure and identify elements
2. **Detailed Test Mode** (`2`): Comprehensive system functionality testing with detailed logging
3. **Auto Follow Mode** (`3`): Execute automated following of contacts (main functionality)

## Code Quality Standards

### Critical Requirements
- **Cognitive Complexity**: Functions must not exceed complexity of 15
- **Line Length**: Maximum 79 characters per line (PEP 8 compliance)
- **Function Length**: Maximum 50 lines per function
- **Documentation**: All public functions must have docstrings
- **Error Handling**: All operations must have proper exception handling with logging

### Code Style
- Follow PEP 8 Python style guide strictly
- Use descriptive variable and function names
- Prefer explicit over implicit code
- Use type hints where applicable
- No hardcoded strings or magic numbers

### Testing Strategy
**IMPORTANT**: This project uses logging-based testing instead of demo files or test scripts.

- **No demo files allowed**: Never create `demo_*.py` or similar test files
- **Logging-driven validation**: Use detailed logging to verify functionality
- **Comprehensive test mode**: All testing done through the integrated test mode in `main.py`
- **Multi-level logging**: Separate logs for main operations, debug info, and errors

## Logging System

The project implements a sophisticated multi-level logging system:

### Log Files
- `logs/main.log`: Main operations and user-facing information
- `logs/debug.log`: Detailed execution traces and debug information  
- `logs/error.log`: Errors, exceptions, and failure conditions

### Logging Levels
- **INFO**: Successful operations and important status updates
- **DEBUG**: Detailed execution flow and variable states
- **ERROR**: Failures, exceptions, and error conditions
- **WARNING**: Potential issues and recoverable problems

### Example Usage
```python
logger = logging.getLogger(__name__)

# Success logging
logger.info(f"ADB connection established: device_id={device_id}")

# Error logging with exception details
logger.error(f"UI analysis failed: {str(e)}", exc_info=True)

# Debug logging for detailed tracing
logger.debug(f"Found {len(elements)} UI elements for analysis")
```

## Architecture Details

### Key Components

1. **ADBConnection** (`adb_connection.py`):
   - Manages device connection state
   - Executes ADB commands with proper error handling
   - Handles UI XML dumping and retrieval

2. **UIAnalyzer** (`ui_analyzer.py`):
   - Parses Android UI XML into structured elements
   - Identifies clickable elements and navigation options
   - Provides Douyin-specific element detection

3. **DouyinAutomator** (`douyin_automator.py`):
   - Main automation logic and workflow orchestration
   - Integrates ADB connection and UI analysis
   - Implements the complete following automation process

4. **Main Program** (`main.py`):
   - User interface and mode selection
   - Comprehensive testing system with detailed logging
   - Error handling and graceful failure recovery

### Error Handling Strategy
- All operations wrapped in try-catch blocks
- Specific exception types handled appropriately
- Comprehensive logging of all error conditions
- Graceful degradation when possible
- User-friendly error messages with technical details in logs

## Development Workflow

### Making Changes
1. **Always check code quality first**: Run `get_errors` to identify issues
2. **Fix quality issues**: Address cognitive complexity, line length, and style issues
3. **Add comprehensive logging**: Every new feature must have detailed logging
4. **Test through logging**: Validate functionality using the integrated test mode
5. **Document changes**: Update docstrings and comments as needed

### Validation Steps
1. **Syntax Check**: `python -m py_compile main.py`
2. **Code Quality**: Ensure no cognitive complexity or style violations
3. **Functional Testing**: Run detailed test mode and review logs
4. **Integration Testing**: Verify complete workflow with actual device

### Common Pitfalls to Avoid
- Never create demo or test files (use logging instead)
- Don't ignore code quality warnings
- Always handle exceptions with proper logging  
- Don't use print() for debugging (use logging)
- Avoid hardcoded device IDs or paths
- Don't skip error handling for ADB operations

## ADB Command Patterns

### Common Operations
```python
# Device connection check
adb_result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)

# UI XML dump
subprocess.run(['adb', 'exec-out', 'uiautomator', 'dump', '/dev/tty'], 
               capture_output=True, text=True)

# Element interaction
subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)])
```

### Error Conditions to Handle
- Device not connected or unauthorized
- ADB daemon not running  
- UI dump failures or timeouts
- Invalid XML response from device
- Permission denied for input commands

## Performance Considerations

- **ADB command latency**: Each command has ~100-500ms overhead
- **UI XML parsing**: Large screens may have 1000+ elements
- **Network delays**: Wireless ADB connections are slower
- **Rate limiting**: Add delays between operations to avoid overwhelming the device

## Security Notes

- Never log sensitive user information
- Device interactions require explicit user consent
- ADB debugging must be manually enabled by user
- All operations are performed locally (no network data transmission)

---

**Important**: This project prioritizes code quality, comprehensive logging, and maintainable architecture. Always refer to these instructions when making changes to ensure consistency with project standards.