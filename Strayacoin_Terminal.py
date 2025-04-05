import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import json
import subprocess
import sys
from datetime import datetime
import platform
import threading
import math
import requests

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
        self.output: scrolledtext.ScrolledText
        self.terminal_frame: ttk.Frame
        
        # Configure window
        self.root.geometry("960x525")
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
        

        # themes added dynamically based on what is in the themes folder
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
Python {sys.version.split()[0]} on {platform.system()} {platform.release()}
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
                self.print_output(f"Starting repeated mining of {blocks} blocks (Press Esc to stop)\n", "success")
            else:
                self.print_output(f"Started mining {blocks} blocks\n", "success")
                
        except (ValueError, IndexError):
            self.print_output("Usage: mine [-r] <number_of_blocks>\n", "error")

    def toggle_output_mode(self):
        self.output_mode_multiline = not self.output_mode_multiline

    def mine_blocks(self, blocks):
        """Mine Strayacoin blocks with optimized performance metrics, clean output."""
    
        #previous_rms = None
        #previous_emc_ratio = None
    
        def format_rms(rms):
            return f"{rms:.4f}"
    
        def format_emc(emc, rms):
            if rms > 0:
                raw_ratio = emc / rms
                compressed = math.sqrt(raw_ratio)
    
                if compressed < 0.01:
                    display = f"{compressed:.4f}"
                elif compressed < 1:
                    display = f"{compressed:.3f}"
                elif compressed < 100:
                    display = f"{compressed:.2f}"
                else:
                    display = f"{compressed:.1f}"
    
                return compressed, display
            return 0, "0.0000"
    
        self.mining_active = True
        try:
            while not self.mining_stop_event.is_set():
                for block in range(1, blocks + 1):
                    if self.mining_stop_event.is_set():
                        break
    
                    # Mine block
                    result = subprocess.run(
                        [self.cli_path, "generate", str(block)],
                        capture_output=True,
                        text=True,
                        check=True
                    )
    
                    # Get network stats once and reuse
                    stats = self._get_network_stats()
    
                    rms = stats["rms"]
                    emc = stats["emc"]
                    emc_ratio, emc_display = format_emc(emc, rms)
    
                    rms_str = format_rms(rms)
                    emc_str = emc_display
    
                    minedBlocks = 1
                    
                    # Save for next round
                    #previous_rms = rms
                    #previous_emc_ratio = emc_ratio
                    
                    #connectedPeers = self._get_connected_peer_count()
                    moneySupply = self._get_Money_Supply()
                    priceOnTradeOgre = self._get_Tradeogre_Ticker(field="price")
                    bidOnTradeOgre = self._get_Tradeogre_Ticker(field="bid")
                    askOnTradeOgre = self._get_Tradeogre_Ticker(field="ask")
                    
                    output = (
                        f"Mined Block {minedBlocks}\n"
                        f"├─ RMS: {rms_str}\n"
                        f"├─ EMC: {emc_str}\n"
                        f"├─ Connected Peers: {stats['conpeers']}\n"
                        f"├────────────────────────────────────────\n"
                        f"├─ Network Difficulty: {stats['difficulty']:.6f}\n"
                        f"├─ Network Peers: {stats['netpeers']}\n"
                        f"├─ Network Hashrate: {stats['hashrate']/1000:,.2f} KH/s\n"
                        f"├─ Network Money Supply: {moneySupply}\n"
                        f"├────────────────────────────────────────\n"
                        f"├─ BTC Price (TradeOgre): {priceOnTradeOgre}\n"
                        f"├─ BTC Sell (TradeOgre): {bidOnTradeOgre}\n"
                        f"├─ BTC Buy (TradeOgre): {askOnTradeOgre}\n"
                         "└────────────────────────────────────────\n"
                    )
                    self.print_output(output, "output")
                    
                    #add one to the number of mined blocks
                    minedBlocks + 1
                    #output = (
                    #    f"Mined Block {minedBlocks} | Difficulty: {stats['difficulty']:.6f} | RMS: {rms_str} | EMC: {emc_str} | Peers: {stats['peers']} | Net Hashrate: {stats['hashrate']/1000:,.2f} KH/s\n"
                    #    f"Mined Block {block}/{blocks} | Difficulty: {stats['difficulty']:.6f} | RMS: {rms_str} | EMC: {emc_str} | Peers: {stats['peers']} | Net Hashrate: {stats['hashrate']/1000:,.2f} KH/s\n"
                    #)
                    #self.print_output(output, "output")
    
                    if result.stdout.strip():
                        self.print_output(result.stdout + "\n", "output")
    
                if not self.mining_repeating:
                    break
    
        except subprocess.CalledProcessError as e:
            self.print_output(f"Mining error: {e.stderr}\n", "error")
        finally:
            self.mining_active = False
            if self.mining_stop_event.is_set():
                self.print_output("Mining stopped by user\n", "warning")

    def _get_network_stats(self):
        """Get all network statistics in one optimized call"""
        stats = {
            'difficulty': float('nan'),
            'netpeers': float('nan'),
            'conpeers': float('nan'),
            'hashrate': float('nan'),
            'rms': float('nan'),
            'emc': float('nan')
        }

        try:
            # Get difficulty and peers first since we need them for hashrate fallback
            stats['difficulty'] = self._get_network_difficulty()
            stats['netpeers'] = self._get_network_peer_count()
            stats['conpeers'] = self._get_connected_peer_count()

            # Get hashrate with optimized fallback
            stats['hashrate'] = self._get_network_hashrate(stats['difficulty'])

            # Calculate metrics
            if not math.isnan(stats['difficulty']) and not math.isnan(stats['netpeers']):
                if stats['netpeers'] > 0 and stats['difficulty'] > 0:
                    stats['rms'] = 1 / (stats['difficulty'] * stats['conpeers'])
                    if not math.isnan(stats['hashrate']):
                        stats['emc'] = stats['hashrate'] / (stats['difficulty'] * stats['netpeers'])

        except Exception as e:
            self.print_output(f"Network stats error: {str(e)}\n", "error")

        return stats

    def _get_network_difficulty(self):
            """Get current network difficulty"""
            try:
                result = subprocess.run(
                    [self.cli_path, "getdifficulty"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return float(result.stdout.strip())
            except:
                return float('nan')

    def _get_network_hashrate(self, current_difficulty=None):
        """Optimized hashrate getter with difficulty fallback"""
        try:
            result = subprocess.run(
                [self.cli_path, "getnetworkhashps"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            hashrate = float(result.stdout.strip())

            if hashrate <= 0 and current_difficulty is not None:
                # Use difficulty-based estimation if standard hashrate is 0
                inversion_factor = 2.5  
                return current_difficulty * (2**32) / (60 * inversion_factor)
            return hashrate
        except:
            if current_difficulty is not None:
                return current_difficulty * (2**32) / 60
            return float('nan')

    def _get_network_peer_count(self):
        """Get number of network peers from explorer API"""
        try:
            response = requests.get("https://explorer.strayacoin.com/api/getconnectioncount", timeout=5)
            if response.status_code == 200:
                return int(response.text)
            return float('nan')
        except:
            return float('nan')

    def _get_Money_Supply(self):
        """Get money supply and format it as an integer with commas."""
        try:
            response = requests.get("https://explorer.strayacoin.com/ext/getmoneysupply", timeout=5)
            if response.status_code == 200:
                supply = float(response.text)  # Convert response to float first
                return "{:,.0f}".format(supply)  # Format with commas, no decimals
            return "N/A"
        except:
            return "N/A"

   
    def _get_Tradeogre_Ticker(self, field="price"):
        """Get NAH-BTC market data from TradeOgre and return a specific field.
        
        Args:
            field (str): Which field to return (e.g., "price", "bid", "ask", "high", "low").
                        Defaults to "price".
    
        Returns:
            str: Formatted value (e.g., "0.00000003 BTC") or "N/A" if error.
        """
        try:
            response = requests.get("https://tradeogre.com/api/v1/ticker/NAH-BTC", timeout=5)
            if response.status_code == 200:
                data = response.json()
                value = float(data.get(field, 0))  # Get the field (default 0 if missing)
                return f"{value:.8f} BTC"  # Format to 8 decimal places
            return "N/A"
        except:
            return "N/A"

    def _get_connected_peer_count(self):
        """Get number of connected peers"""
        try:
            result = subprocess.run(
                [self.cli_path, "getpeerinfo"],
                capture_output=True,
                text=True,
                check=True
            )
            peers = json.loads(result.stdout)
            return len(peers)
        except:
            return float('nan')


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
  mine <blocks>       - Mine specified number of blocks once then stop
  mine -r <blocks>    - Mine specified number of blocks repeatidly until stopped with esc
  theme [name]        - Change color theme
  wallet [command]    - Interact with Strayacoin wallet
  help                - Show this help
  clear               - Clear the terminal
  exit                - Exit the application

System Commands:
  ls/dir              - List directory contents
  cd <directory>      - Change directory
  pwd                 - Print working directory
  date                - Show current date
  time                - Show current time
  <any command>       - Execute system command
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
