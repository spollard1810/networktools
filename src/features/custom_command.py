import tkinter as tk
from tkinter import ttk, filedialog
from typing import Dict, List, Optional
import difflib
import json
import csv
from datetime import datetime
from src.gui.widgets import FeatureTab
from src.core.device import Device

class CommandHistory:
    def __init__(self, max_size: int = 50):
        self.history: List[str] = []
        self.max_size = max_size
        self.position = -1
        self._load_history()

    def add(self, command: str):
        if command and (not self.history or command != self.history[-1]):
            self.history.append(command)
            if len(self.history) > self.max_size:
                self.history.pop(0)
            self._save_history()
        self.position = len(self.history)

    def get_previous(self) -> Optional[str]:
        if self.position > 0:
            self.position -= 1
            return self.history[self.position]
        return None

    def get_next(self) -> Optional[str]:
        if self.position < len(self.history) - 1:
            self.position += 1
            return self.history[self.position]
        return None

    def _save_history(self):
        with open('command_history.json', 'w') as f:
            json.dump(self.history, f)

    def _load_history(self):
        try:
            with open('command_history.json', 'r') as f:
                self.history = json.load(f)
                self.position = len(self.history)
        except FileNotFoundError:
            pass

    def clear(self):
        """Clear the command history"""
        self.history = []
        self.position = -1
        self._save_history()

class CustomCommandTab(FeatureTab):
    def __init__(self, parent, device_manager):
        super().__init__(parent, device_manager)
        self.device_outputs: Dict[str, Dict[str, str]] = {}
        self.command_history = CommandHistory()
        self.template_commands = self._load_template_commands()
        self._create_custom_widgets()

    def _create_custom_widgets(self):
        # Command input area
        input_frame = ttk.LabelFrame(self, text="Command Input", padding="5")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Template commands dropdown
        self.template_var = tk.StringVar()
        template_menu = ttk.Combobox(input_frame, textvariable=self.template_var,
                                   values=list(self.template_commands.keys()))
        template_menu.pack(side=tk.LEFT, padx=(0, 5))
        template_menu.bind('<<ComboboxSelected>>', self._load_template)
        
        # Command input with history support
        self.command_text = tk.Text(input_frame, height=3, width=50)
        self.command_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.command_text.bind('<Control-Return>', lambda e: self.run_operation())
        self.command_text.bind('<Up>', self._history_up)
        self.command_text.bind('<Down>', self._history_down)
        
        # Buttons frame
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="Execute", 
                  command=self.run_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save Template", 
                  command=self._save_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save Output", 
                  command=self._save_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear", 
                  command=self.clear_results).pack(side=tk.LEFT, padx=5)

        # Search frame
        search_frame = ttk.Frame(self)
        search_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._handle_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # View options
        view_frame = ttk.LabelFrame(self, text="View Options", padding="5")
        view_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.view_var = tk.StringVar(value="tabbed")
        ttk.Radiobutton(view_frame, text="Tabbed View", 
                       variable=self.view_var, value="tabbed",
                       command=self._switch_view).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(view_frame, text="Diff View", 
                       variable=self.view_var, value="diff",
                       command=self._switch_view).pack(side=tk.LEFT, padx=5)
        
        # Results area with notebook for tabs
        self.results_frame = ttk.LabelFrame(self, text="Results", padding="5")
        self.results_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.notebook = ttk.Notebook(self.results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.diff_text = tk.Text(self.results_frame)
        
        # Configure grid weights
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Add History Management Frame
        history_frame = ttk.Frame(input_frame)
        history_frame.pack(side=tk.LEFT, padx=5)

        # History dropdown
        self.history_var = tk.StringVar()
        self.history_dropdown = ttk.Combobox(history_frame, 
                                           textvariable=self.history_var,
                                           width=30)
        self.history_dropdown.pack(side=tk.LEFT, padx=(0, 5))
        self.history_dropdown.bind('<<ComboboxSelected>>', self._load_from_history)
        
        # Clear history button
        ttk.Button(history_frame, text="Clear History", 
                  command=self._clear_history).pack(side=tk.LEFT)

    def _update_history_dropdown(self):
        """Update the history dropdown with current history items"""
        self.history_dropdown['values'] = self.command_history.history
        
    def _load_from_history(self, event):
        """Load selected command from history dropdown"""
        selected = self.history_var.get()
        if selected:
            self.command_text.delete("1.0", tk.END)
            self.command_text.insert("1.0", selected)
            self.history_var.set('')  # Clear selection after loading

    def _clear_history(self):
        """Clear command history"""
        if tk.messagebox.askyesno("Clear History", 
                                 "Are you sure you want to clear the command history?"):
            self.command_history.clear()
            self._update_history_dropdown()
            self.update_status("Command history cleared")

    def run_operation(self):
        """Execute the commands on selected devices"""
        commands = self.command_text.get("1.0", tk.END).strip().split('\n')
        if not commands or all(not cmd.strip() for cmd in commands):
            self.update_status("Please enter command(s)")
            return
            
        connected_devices = [
            device for device in self.device_manager.devices 
            if device.connection is not None
        ]
        
        if not connected_devices:
            self.update_status("No connected devices found")
            return
        
        self.device_outputs.clear()
        total_commands = len(commands)
        self.update_status(f"Running {total_commands} command(s) on {len(connected_devices)} devices...")
        self.update_progress(0)
        
        for device in connected_devices:
            self.device_outputs[device.hostname] = {}
            for i, command in enumerate(commands, 1):
                if not command.strip():
                    continue
                try:
                    output = device.connection.send_command(command)
                    self.device_outputs[device.hostname][command] = output
                    progress = (i / (total_commands * len(connected_devices))) * 100
                    self.update_progress(progress)
                except Exception as e:
                    self.device_outputs[device.hostname][command] = f"Error: {str(e)}"
        
        # Add command to history
        for command in commands:
            if command.strip():
                self.command_history.add(command)
        self._update_history_dropdown()
        
        self.update_status("Command execution completed")
        self._update_results_view()

    def _save_output(self):
        """Save outputs to CSV file"""
        if not self.device_outputs:
            self.update_status("No output to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"command_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Hostname', 'Command', 'Output'])
                
                for hostname, commands in self.device_outputs.items():
                    for command, output in commands.items():
                        writer.writerow([hostname, command, output])
            
            self.update_status(f"Output saved to {filename}")

    def _handle_search(self, *args):
        """Handle search in output"""
        search_text = self.search_var.get()
        if self.view_var.get() == "tabbed":
            for tab in self.notebook.tabs():
                text_widget = self.notebook.select_slave(tab).winfo_children()[0]
                self._highlight_search(text_widget, search_text)
        else:
            self._highlight_search(self.diff_text, search_text)

    def _highlight_search(self, text_widget, search_text):
        """Highlight search text in widget"""
        text_widget.tag_remove('search', '1.0', tk.END)
        if search_text:
            start = '1.0'
            while True:
                start = text_widget.search(search_text, start, tk.END, nocase=True)
                if not start:
                    break
                end = f"{start}+{len(search_text)}c"
                text_widget.tag_add('search', start, end)
                start = end
            text_widget.tag_config('search', background='yellow')

    def _history_up(self, event):
        """Handle up arrow key for command history"""
        command = self.command_history.get_previous()
        if command:
            self.command_text.delete("1.0", tk.END)
            self.command_text.insert("1.0", command)
        return "break"

    def _history_down(self, event):
        """Handle down arrow key for command history"""
        command = self.command_history.get_next()
        if command:
            self.command_text.delete("1.0", tk.END)
            self.command_text.insert("1.0", command)
        return "break"

    def _load_template_commands(self) -> Dict[str, str]:
        """Load template commands from JSON file"""
        try:
            with open('command_templates.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "Show Interfaces": "show interfaces\nshow interfaces status",
                "Show Version": "show version",
                "Show Running Config": "show running-config"
            }

    def _save_template(self):
        """Save current command as template"""
        name = tk.simpledialog.askstring("Template Name", 
                                       "Enter name for command template:")
        if name:
            commands = self.command_text.get("1.0", tk.END).strip()
            self.template_commands[name] = commands
            with open('command_templates.json', 'w') as f:
                json.dump(self.template_commands, f)
            
            # Update template dropdown
            template_menu = self.template_var.master
            template_menu['values'] = list(self.template_commands.keys())
            self.update_status(f"Template '{name}' saved")

    def _load_template(self, event):
        """Load selected template into command input"""
        template_name = self.template_var.get()
        if template_name in self.template_commands:
            self.command_text.delete("1.0", tk.END)
            self.command_text.insert("1.0", self.template_commands[template_name])

    def _update_results_view(self):
        """Update the results view based on current view mode"""
        if self.view_var.get() == "tabbed":
            self._show_tabbed_view()
        else:
            self._show_diff_view()

    def _show_tabbed_view(self):
        """Display results in tabbed view"""
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.diff_text.pack_forget()
        
        # Clear existing tabs
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        
        # Create new tabs for each device
        for hostname, commands in self.device_outputs.items():
            frame = ttk.Frame(self.notebook)
            for command, output in commands.items():
                text = tk.Text(frame, wrap=tk.NONE)
                text.insert(tk.END, output)
                text.pack(fill=tk.BOTH, expand=True)
                
                # Add scrollbars
                v_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
                h_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text.xview)
                text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
                
                v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
                h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
                
                self.notebook.add(frame, text=f"{hostname} - {command}")

    def _show_diff_view(self):
        """Display results in diff view"""
        self.notebook.pack_forget()
        self.diff_text.pack(fill=tk.BOTH, expand=True)
        
        # Generate diff
        if len(self.device_outputs) < 2:
            diff_output = "Need at least 2 devices to compare outputs"
        else:
            devices = list(self.device_outputs.keys())
            diff = difflib.HtmlDiff().make_file(
                self.device_outputs[devices[0]].values(),
                self.device_outputs[devices[1]].values(),
                devices[0],
                devices[1]
            )
            diff_output = diff
        
        self.diff_text.delete(1.0, tk.END)
        self.diff_text.insert(tk.END, diff_output)

    def _switch_view(self):
        """Switch between tabbed and diff views"""
        self._update_results_view()

    def clear_results(self):
        """Clear all results and reset the view"""
        self.device_outputs.clear()
        self.command_text.delete("1.0", tk.END)
        self.update_status("Ready")
        self.update_progress(0)
        self._update_results_view() 