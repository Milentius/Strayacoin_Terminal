# Note: This is an unofficial community project not affiliated with the official Strayacoin team. #

# Strayacoin Terminal

![Strayacoin Terminal Screenshot](https://i.imgur.com/FA4IzIU.png) *(Example screenshot placeholder)*

A customizable terminal interface for Strayacoin mining and wallet management with theming support.

## Features

- 🖥️ Terminal-like interface with command history
- ⛏️ Strayacoin mining with single or repeating mode
  - `mine 5` - Mine 5 blocks once
  - `mine -r 1` - Continuously mine 1 block (press Esc to stop)
- 💰 Wallet integration:
  - Check balance
  - Send coins
  - View wallet info
- 🎨 Customizable themes (Dark/Light included)
- 📁 File system navigation
- 🛑 Safe mining interruption (Esc key)

## Installation

1. **Prerequisites**:
   - Python 3.8+
   - Strayacoin CLI (`Strayacoin-cli.exe` in same directory)
2. **Installing**:
   - Unzip the miner (Strayacoin_Terminal.py)

## Running the Application
   to run the Strayacoin Terminal use you choice of IDE or in a command prompt or terminal, navigate to the wallet folder and type "python Strayacoin_Terminal.py"

## Usage

### Basic Commands

| Command               | Description                          |
|-----------------------|--------------------------------------|
| `help`                | Show all available commands          |
| `mine [blocks]`       | Mine specified number of blocks      |
| `mine -r [blocks]`    | Continuously mine blocks             |
| `wallet balance`      | Show wallet balance                  |
| `wallet send amt addr`| Send coins to address                |
| `wallet info`         | Show wallet information              |
| `theme [name]`        | Change color theme                   |
| `clear`               | Clear the terminal                   |
| `exit`                | Exit the application                 |

### System Commands

All standard system commands are supported:
- `ls`/`dir` - List directory contents
- `cd` - Change directory
- `pwd` - Show current directory
- `date` - Show current date
- `time` - Show current time

## Theming

Customize the terminal appearance by:
1. Editing JSON files in the `themes` directory
2. Using the `theme` command to switch between themes

Included themes:
- `Dark` (default)
- `Light`

### Creating Custom Themes

1. Create a new JSON file in the `themes` folder
2. Follow this structure:
```json
{
    "name": "MyTheme",
    "colors": {
        "background": "#HEXCOLOR",
        "foreground": "#HEXCOLOR",
        "prompt": "#HEXCOLOR",
        "output": "#HEXCOLOR",
        "error": "#HEXCOLOR",
        "warning": "#HEXCOLOR",
        "success": "#HEXCOLOR",
        "statusbar": "#HEXCOLOR"
    }
}
```
3. Restart the application or use theme MyTheme

	
Ctrl+V	Paste
Ctrl+L	Clear terminal
Ctrl+N	New terminal window
Esc	Stop mining operation
Up/Down	Navigate command history

## Keyboard Shortcuts

| Shortcut              | Action                               |
|-----------------------|--------------------------------------|
| `Ctrl+C`              | Copy selected text                   |
| `Ctrl+V`              | Paste                                |
| `Ctrl+L`              | Clear Terminal                       |
| `Ctrl+N`              | New Terminal Window                  |
| `Esc`                 | Stop mining operation                |
| `Up/Down`             | Navigate command history             |

## Troubleshooting
**Issue: "Strayacoin CLI not found"**
  - Ensure the miner is in the wallet folder along side the Strayacoin-cli.exe file.
  - Update the cli_path variable in the code

**Issue: Mining doesn't start**
  - Check if another mining process is already running
  - Verify your Strayacoin node is properly configured





## Development
Open the miner in Thonny or any other Python IDE

MIT License - Free for personal and commercial use
