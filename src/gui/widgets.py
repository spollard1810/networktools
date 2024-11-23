import tkinter as tk
from tkinter import ttk
from src.core.device import Device
from typing import List, Callable, Optional
import logging

class DeviceTreeView(ttk.Treeview):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            columns=("Hostname", "IP", "Type", "Status"),
            show="headings",
            **kwargs
        )
        
        # Add logging
        self.logger = logging.getLogger(__name__)
        
        # Configure headers
        headers = {
            "Hostname": 150,
            "IP": 150,
            "Type": 150,
            "Status": 100
        }
        
        for col, width in headers.items():
            self.heading(col, text=col)
            self.column(col, width=width)
        
        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(
            parent, 
            orient=tk.VERTICAL, 
            command=self.yview
        )
        self.configure(yscrollcommand=self.scrollbar.set)

    def grid_with_scrollbar(self, **kwargs):
        self.grid(row=kwargs.get('row', 0), 
                 column=kwargs.get('column', 0), 
                 sticky=kwargs.get('sticky', (tk.W, tk.E, tk.N, tk.S)))
        self.scrollbar.grid(row=kwargs.get('row', 0), 
                          column=kwargs.get('column', 0) + 1, 
                          sticky=(tk.N, tk.S))

    def update_devices(self, devices: List[Device]):
        self.clear()
        for device in devices:
            self.insert("", tk.END, values=(
                device.hostname,
                device.ip,
                device.device_type,
                "Disconnected"
            ))

    def update_device_status(self, hostname: str, status: str) -> bool:
        """Update device status with error handling
        Returns: True if successful, False otherwise"""
        try:
            for item in self.get_children():
                if self.item(item)['values'][0] == hostname:
                    self.set(item, "Status", status)
                    return True
            self.logger.warning(f"Device {hostname} not found in tree")
            return False
        except Exception as e:
            self.logger.error(f"Error updating status for {hostname}: {str(e)}")
            return False

    def clear(self):
        for item in self.get_children():
            self.delete(item)

class FeatureTab(ttk.Frame):
    def __init__(self, parent, device_manager, **kwargs):
        super().__init__(parent, **kwargs)
        self.device_manager = device_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Add cancel operation support
        self.current_operation = None
        self.cancel_requested = False
        
        self._create_widgets()
        self._configure_grid()

    def _create_widgets(self):
        """Create standard widgets for feature tabs"""
        # Status frame at top
        self.status_frame = ttk.LabelFrame(self, text="Status", padding="5")
        self.status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(self.status_frame, mode='determinate')
        self.progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Action buttons
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.run_button = ttk.Button(
            self.button_frame, 
            text="Run", 
            command=self.run_operation
        )
        self.run_button.pack(side=tk.LEFT)
        
        # Add cancel button
        self.cancel_button = ttk.Button(
            self.button_frame,
            text="Cancel",
            command=self.cancel_operation,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Results area
        self.results_frame = ttk.LabelFrame(self, text="Results", padding="5")
        self.results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True)

    def _configure_grid(self):
        """Configure grid weights"""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def run_operation(self):
        """Override this method in subclasses"""
        connected_devices = [
            device for device in self.device_manager.devices 
            if device.connection is not None
        ]
        
        if not connected_devices:
            self.update_status("No connected devices found")
            return
        
        self.update_status(f"Running operation on {len(connected_devices)} devices...")
        # Implement specific operation in subclass

    def update_status(self, message: str):
        """Update status label"""
        self.status_label.config(text=message)
        self.update()

    def update_progress(self, value: int):
        """Update progress bar"""
        self.progress['value'] = value
        self.update()

    def add_result(self, result: str):
        """Add text to results area"""
        self.results_text.insert(tk.END, f"{result}\n")
        self.results_text.see(tk.END)

    def cancel_operation(self):
        """Request cancellation of current operation"""
        self.cancel_requested = True
        self.update_status("Cancelling operation...")
        self.cancel_button.configure(state=tk.DISABLED)

    def start_operation(self):
        """Setup for starting an operation"""
        self.cancel_requested = False
        self.cancel_button.configure(state=tk.NORMAL)
        self.run_button.configure(state=tk.DISABLED)

    def finish_operation(self):
        """Cleanup after operation completes"""
        self.cancel_button.configure(state=tk.DISABLED)
        self.run_button.configure(state=tk.NORMAL)

class VlanDiscoveryTab:
   #unused
    pass
