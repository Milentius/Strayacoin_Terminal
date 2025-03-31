import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import os
import json
import subprocess
import sys
from datetime import datetime
import platform
import threading

class ThemedStyle(ttk.Style):
    def __init__(self, root, theme_data):
        super().__init__(root)
        self.theme_data = theme_data
        self.configure_theme()

    def configure_theme(self):
        # Only create theme if it doesn't exist
        if "straya" not in self.theme_names():
            self.theme_create("straya", parent="alt", settings={
                ".": {
                    "configure": {
                        "background": self.theme_data["background"],
                        "foreground": self.theme_data["foreground"],
                        "troughcolor": self.theme_data["background"],
                        "selectbackground": self.theme_data["statusbar"],
                        "selectforeground": self.theme_data["foreground"],
                        "fieldbackground": self.theme_data["background"],
                        "insertbackground": self.theme_data["foreground"],
                        "highlightcolor": self.theme_data["background"]
                    }
                },
                "TFrame": {
                    "configure": {
                        "background": self.theme_data["background"],
                        "borderwidth": 0
                    }
                },
                "TLabel": {
                    "configure": {
                        "background": self.theme_data["background"],
                        "foreground": self.theme_data["foreground"],
                        "font": ('Consolas', 12)
                    }
                },
                "TEntry": {
                    "configure": {
                        "fieldbackground": self.theme_data["background"],
                        "foreground": self.theme_data["foreground"],
                        "insertcolor": self.theme_data["foreground"],
                        "font": ('Consolas', 12),
                        "borderwidth": 1,
                        "relief": "flat"
                    }
                },
                "TButton": {
                    "configure": {
                        "background": self.theme_data["statusbar"],
                        "foreground": self.theme_data["foreground"],
                        "font": ('Consolas', 10)
                    }
                },
                "TMenubutton": {
                    "configure": {
                        "background": self.theme_data["background"],
                        "foreground": self.theme_data["foreground"]
                    }
                }
            })
        self.theme_use("straya")

class StrayacoinTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("Strayacoin Terminal")
        self.themes: dict[str, dict[str, str]] = {}
        self.current_theme = None
        self.load_themes()
        self.mining_repeating = False
        self.mining_stop_event = threading.Event()
        
        # Configure window
        self.root.geometry("1000x700")
        self.root.minsize(800, 500)
        
        # Strayacoin configuration
        self.cli_path = "Strayacoin-cli.exe"
        self.mining_active = False
        self.mining_thread = None
        
        # Initialize UI with default theme
        self.style = ThemedStyle(self.root, self.themes["Dark"])
        self.load_theme("Dark")
        
        # Initialize command system
        self.command_history = []
        self.history_index = -1
        self.print_welcome()
        self.bind_shortcuts()

    def load_themes(self):
        """Load all themes from themes directory"""
        themes_dir = "themes"
        if not os.path.exists(themes_dir):
            os.makedirs(themes_dir)
            # Create default themes if none exist
            default_themes = {
                "Dark": {
                    "background": "#1E1E1E",
                    "foreground": "#FFFFFF",
                    "prompt": "#00FF00",
                    "output": "#CCCCCC",
                    "error": "#FF4444",
                    "warning": "#FFAA00",
                    "success": "#00FF00",
                    "statusbar": "#2D2D2D"
                },
                "Light": {
                    "background": "#FFFFFF",
                    "foreground": "#000000",
                    "prompt": "#007700",
                    "output": "#333333",
                    "error": "#CC0000",
                    "warning": "#AA5500",
                    "success": "#007700",
                    "statusbar": "#EEEEEE"
                }
            }
            for name, colors in default_themes.items():
                with open(os.path.join(themes_dir, f"{name}.json"), "w") as f:
                    json.dump({"name": name, "colors": colors}, f, indent=4)
        
        for theme_file in os.listdir(themes_dir):
            if theme_file.endswith(".json"):
                try:
                    with open(os.path.join(themes_dir, theme_file), "r", encoding='utf-8') as f:
                        theme = json.load(f)
                        self.themes[theme["name"]] = theme["colors"]
                except Exception as e:
                    print(f"Error loading theme {theme_file}: {str(e)}")

    def load_theme(self, theme_name):
        """Apply a theme to the entire interface"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            colors = self.themes[theme_name]
            
            # Configure root window
            self.root.config(bg=colors["background"])
            
            # Recreate UI elements with new theme
            self.create_menu(colors)
            self.create_terminal(colors)
            self.create_status_bar(colors)
            
            # Update all tags
            if hasattr(self, 'output'):
                self.output.tag_config("error", foreground=colors["error"])
                self.output.tag_config("warning", foreground=colors["warning"])
                self.output.tag_config("success", foreground=colors["success"])
                self.output.tag_config("output", foreground=colors["output"])

    def create_menu(self, colors):
        """Create the menu bar with theme support"""
        menubar = tk.Menu(self.root, 
                         bg=colors["background"],
                         fg=colors["foreground"],
                         activebackground=colors["statusbar"],
                         activeforeground=colors["foreground"],
                         relief='flat')
        
        # File menu
        file_menu = tk.Menu(menubar, 
                           tearoff=0,
                           bg=colors["background"],
                           fg=colors["foreground"],
                           activebackground=colors["statusbar"],
                           activeforeground=colors["foreground"])
        file_menu.add_command(label="New Terminal", command=self.new_terminal)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, 
                           tearoff=0,
                           bg=colors["background"],
                           fg=colors["foreground"],
                           activebackground=colors["statusbar"],
                           activeforeground=colors["foreground"])
        edit_menu.add_command(label="Copy", command=self.copy_text)
        edit_menu.add_command(label="Paste", command=self.paste_text)
        edit_menu.add_command(label="Clear", command=self.clear_terminal)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu (themes)
        view_menu = tk.Menu(menubar, 
                           tearoff=0,
                           bg=colors["background"],
                           fg=colors["foreground"],
                           activebackground=colors["statusbar"],
                           activeforeground=colors["foreground"])
        for theme_name in sorted(self.themes.keys()):
            view_menu.add_command(
                label=theme_name,
                command=lambda name=theme_name: self.load_theme(name)
            )
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, 
                           tearoff=0,
                           bg=colors["background"],
                           fg=colors["foreground"],
                           activebackground=colors["statusbar"],
                           activeforeground=colors["foreground"])
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)

    def create_terminal(self, colors):
        """Create the terminal-like interface with theme support"""
        # Main frame
        if hasattr(self, 'terminal_frame'):
            self.terminal_frame.destroy()
        
        self.terminal_frame = ttk.Frame(self.root)
        self.terminal_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Terminal output area
        if hasattr(self, 'output'):
            self.output.destroy()
        
        self.output = scrolledtext.ScrolledText(
            self.terminal_frame,
            wrap=tk.WORD,
            bg=colors["background"],
            fg=colors["foreground"],
            insertbackground=colors["foreground"],
            font=('Consolas', 12),
            state='disabled',
            relief='flat',
            borderwidth=0,
            highlightthickness=0
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.output.tag_config("error", foreground=colors["error"])
        self.output.tag_config("warning", foreground=colors["warning"])
        self.output.tag_config("success", foreground=colors["success"])
        self.output.tag_config("output", foreground=colors["output"])
        
        # Input frame
        if hasattr(self, 'input_frame'):
            self.input_frame.destroy()
        
        self.input_frame = ttk.Frame(self.terminal_frame)
        self.input_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Prompt label
        if hasattr(self, 'prompt'):
            self.prompt.destroy()
        
        self.prompt = ttk.Label(
            self.input_frame,
            text=">>>",
            foreground=colors["prompt"],
            font=('Consolas', 12)
        )
        self.prompt.pack(side=tk.LEFT)
        
        # Command entry
        if hasattr(self, 'command_entry'):
            self.command_entry.destroy()
        
        self.command_entry = ttk.Entry(
            self.input_frame,
            font=('Consolas', 12)
        )
        self.command_entry.pack(fill=tk.X, expand=True, padx=5)
        self.command_entry.bind("<Return>", self.execute_command)
        self.command_entry.bind("<Up>", self.prev_command)
        self.command_entry.bind("<Down>", self.next_command)
        self.command_entry.focus()

    def create_status_bar(self, colors):
        """Create the status bar at the bottom with theme support"""
        if hasattr(self, 'status'):
            self.status.destroy()
        
        self.status = ttk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=('Consolas', 10)
        )
        self.status.pack(fill=tk.X, padx=5, pady=5)
        self.update_status()

    def bind_shortcuts(self):
        """Bind keyboard shortcuts including Esc to stop mining"""
        self.root.bind("<Control-c>", lambda e: self.copy_text())
        self.root.bind("<Control-v>", lambda e: self.paste_text())
        self.root.bind("<Control-l>", lambda e: self.clear_terminal())
        self.root.bind("<Control-n>", lambda e: self.new_terminal())
        self.root.bind("<Escape>", self.stop_mining)

    def print_welcome(self):
        """Print welcome message"""
        welcome_msg = f"""
Strayacoin Terminal
Python {sys.version.split()[0]} on {platform.system()}
Type "help" for available commands.
"""
        self.print_output(welcome_msg, "output")
        self.print_prompt()

    def print_output(self, text, tag="output"):
        """Print text to the output area"""
        self.output.config(state='normal')
        self.output.insert(tk.END, text, tag)
        self.output.see(tk.END)
        self.output.config(state='disabled')

    def print_prompt(self):
        """Print the prompt"""
        self.print_output("\n>>> ", "success")

    def execute_command(self, event=None):
        """Execute the entered command"""
        command = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)
        
        if not command:
            return
        
        # Add command to history
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Print the command in output
        self.print_output(f"{command}\n", "output")
        
        # Process the command
        self.process_command(command)
        
        # Print new prompt
        self.print_prompt()
        
        # Update status
        self.update_status()

    def process_command(self, command):
        """Process entered commands with mining support"""
        cmd_parts = command.lower().split()
        
        if not cmd_parts:
            return
        
        if cmd_parts[0] == "mine":
            self.handle_mining_command(cmd_parts)
        elif cmd_parts[0] == "theme":
            self.handle_theme_command(cmd_parts)
        elif cmd_parts[0] == "wallet":
            self.handle_wallet_command(cmd_parts)
        elif cmd_parts[0] == "help":
            self.print_help()
        elif cmd_parts[0] == "clear":
            self.clear_terminal()
        elif cmd_parts[0] == "exit":
            self.root.quit()
        elif cmd_parts[0] in ["ls", "dir"]:
            self.list_directory()
        elif cmd_parts[0] == "cd" and len(cmd_parts) > 1:
            self.change_directory(cmd_parts[1])
        elif cmd_parts[0] == "pwd":
            self.print_working_directory()
        elif cmd_parts[0] == "date":
            self.print_date()
        elif cmd_parts[0] == "time":
            self.print_time()
        else:
            self.execute_system_command(command)

    def handle_mining_command(self, cmd_parts):
        """Handle mining commands with optional -r flag for repeating"""
        if self.mining_active:
            self.print_output("Mining already in progress\n", "warning")
            return
        
        try:
            if "-r" in cmd_parts:
                repeat_index = cmd_parts.index("-r")
                blocks = int(cmd_parts[repeat_index + 1]) if len(cmd_parts) > repeat_index + 1 else 1
                self.mining_repeating = True
                self.mining_stop_event.clear()
            else:
                blocks = int(cmd_parts[1]) if len(cmd_parts) > 1 else 1
                self.mining_repeating = False
            
            self.mining_thread = threading.Thread(
                target=self.mine_blocks,
                args=(blocks,),
                daemon=True
            )
            self.mining_thread.start()
            
            if self.mining_repeating:
                self.print_output(f"Started repeating mining of {blocks} blocks (Press Esc to stop)\n", "success")
            else:
                self.print_output(f"Started mining {blocks} blocks\n", "success")
                
        except (ValueError, IndexError):
            self.print_output("Usage: mine [-r] <number_of_blocks>\n", "error")

    def mine_blocks(self, blocks):
        """Mine Strayacoin blocks with optional repeating"""
        self.mining_active = True
        try:
            while not self.mining_stop_event.is_set():
                for block in range(1, blocks + 1):
                    if self.mining_stop_event.is_set():
                        break
                        
                    result = subprocess.run(
                        [self.cli_path, "generate", str(block)],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    self.print_output(f"Mined block {block}\n", "output")
                    self.print_output(result.stdout + "\n", "output")
                
                if not self.mining_repeating:
                    break
                    
        except subprocess.CalledProcessError as e:
            self.print_output(f"Mining error: {e.stderr}\n", "error")
        except FileNotFoundError:
            self.print_output("Strayacoin CLI not found\n", "error")
        finally:
            self.mining_active = False
            self.mining_repeating = False
            if self.mining_stop_event.is_set():
                self.print_output("Mining stopped by user\n", "warning")

    def stop_mining(self, event=None):
        """Stop any active mining operation"""
        if self.mining_active:
            self.mining_stop_event.set()
            self.print_output("Stopping mining...\n", "warning")
        else:
            self.print_output("No active mining operation\n", "output")

    def handle_theme_command(self, cmd_parts):
        """Handle theme changing commands"""
        if len(cmd_parts) == 1:
            themes = "\n".join(sorted(self.themes.keys()))
            self.print_output(f"Available themes:\n{themes}\n", "output")
        elif len(cmd_parts) == 2:
            new_theme = cmd_parts[1].capitalize()
            if new_theme in self.themes:
                self.load_theme(new_theme)
                self.print_output(f"Theme changed to {new_theme}\n", "success")
            else:
                self.print_output(f"Theme {new_theme} not found\n", "error")

    def handle_wallet_command(self, cmd_parts):
        """Handle wallet-related commands"""
        if len(cmd_parts) < 2:
            self.print_output("Wallet commands:\n"
                           "  balance    - Show wallet balance\n"
                           "  send <amount> <address>\n"
                           "  info       - Show wallet info\n", "output")
            return
        
        try:
            if cmd_parts[1] == "balance":
                result = subprocess.run(
                    [self.cli_path, "getbalance"],
                    capture_output=True,
                    text=True
                )
                self.print_output(f"Wallet balance: {result.stdout}\n", "output")
            
            elif cmd_parts[1] == "send" and len(cmd_parts) == 4:
                amount = cmd_parts[2]
                address = cmd_parts[3]
                result = subprocess.run(
                    [self.cli_path, "sendtoaddress", address, amount],
                    capture_output=True,
                    text=True
                )
                self.print_output(f"Transaction ID: {result.stdout}\n", "success")
            
            elif cmd_parts[1] == "info":
                result = subprocess.run(
                    [self.cli_path, "getwalletinfo"],
                    capture_output=True,
                    text=True
                )
                self.print_output(result.stdout + "\n", "output")
            
            else:
                self.print_output("Invalid wallet command\n", "error")
        
        except Exception as e:
            self.print_output(f"Wallet error: {str(e)}\n", "error")

    def execute_system_command(self, command):
        """Execute system commands"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            if result.stdout:
                self.print_output(result.stdout + "\n", "output")
            if result.stderr:
                self.print_output(result.stderr + "\n", "error")
        except Exception as e:
            self.print_output(f"Error: {str(e)}\n", "error")

    def print_help(self):
        """Show enhanced help information"""
        help_text = """
Strayacoin Terminal Commands:
  mine <blocks>    - Mine specified number of blocks
  theme [name]     - Change color theme
  wallet [command] - Interact with Strayacoin wallet
  help             - Show this help
  clear            - Clear the terminal
  exit             - Exit the application

System Commands:
  ls/dir           - List directory contents
  cd <directory>   - Change directory
  pwd              - Print working directory
  date             - Show current date
  time             - Show current time
  <any command>    - Execute system command
"""
        self.print_output(help_text, "output")

    def list_directory(self):
        """List directory contents"""
        try:
            files = os.listdir()
            for f in files:
                self.print_output(f"{f}\n", "output")
        except Exception as e:
            self.print_output(f"Error: {str(e)}\n", "error")

    def change_directory(self, directory):
        """Change working directory"""
        try:
            os.chdir(directory)
            self.print_output(f"Changed directory to: {os.getcwd()}\n", "output")
            self.update_status()
        except Exception as e:
            self.print_output(f"Error: {str(e)}\n", "error")

    def print_working_directory(self):
        """Print current working directory"""
        self.print_output(f"{os.getcwd()}\n", "output")

    def print_date(self):
        """Print current date"""
        self.print_output(f"{datetime.now().strftime('%Y-%m-%d')}\n", "output")

    def print_time(self):
        """Print current time"""
        self.print_output(f"{datetime.now().strftime('%H:%M:%S')}\n", "output")

    def clear_terminal(self, event=None):
        """Clear the terminal"""
        self.output.config(state='normal')
        self.output.delete(1.0, tk.END)
        self.output.config(state='disabled')
        self.print_prompt()

    def copy_text(self, event=None):
        """Copy selected text to clipboard"""
        try:
            self.root.clipboard_clear()
            text = self.output.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_append(text)
        except tk.TclError:
            pass

    def paste_text(self, event=None):
        """Paste text from clipboard"""
        try:
            text = self.root.clipboard_get()
            self.command_entry.insert(tk.INSERT, text)
        except tk.TclError:
            pass

    def new_terminal(self):
        """Open a new terminal window"""
        new_window = tk.Toplevel(self.root)
        StrayacoinTerminal(new_window)

    def show_about(self):
        """Show about information"""
        about_text = """
Strayacoin Terminal
Version 1.0
A custom terminal for Strayacoin mining and wallet management
"""
        self.print_output(about_text, "output")

    def prev_command(self, event):
        """Navigate to previous command in history"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])

    def next_command(self, event):
        """Navigate to next command in history"""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        elif self.command_history and self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)

    def update_status(self):
        """Update the status bar"""
        self.status.config(text=f"Current directory: {os.getcwd()} | Strayacoin CLI: {os.path.exists(self.cli_path)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StrayacoinTerminal(root)
    root.mainloop()
