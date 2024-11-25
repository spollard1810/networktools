import tkinter as tk
from tkinter import ttk, filedialog
from src.core.device_manager import DeviceManager
from src.features.vlan_discovery import VlanDiscoveryTab
from src.features.network_discovery import NetworkDiscoveryTab
from src.features.route_analyzer import RouteAnalyzerTab
from src.features.auditor import AuditorTab
from src.features.reporter import ReporterTab
from src.features.crawler import CrawlerTab
from src.utils.credentials_manager import CredentialsManager
from .widgets import DeviceTreeView
from .dialogs import LoginDialog, LoadingDialog
from src.core.connector import create_connection
from src.features.custom_command import CustomCommandTab
from src.features.route_validator import RouteValidatorTab
import threading
import queue

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.device_manager = DeviceManager()
        self.credentials_manager = CredentialsManager()
        
        self._init_window()
        self._create_main_frame()
        self._create_notebook()
        self._create_tabs()
        self._configure_grid()

    def _init_window(self):
        """Initialize main window settings"""
        self.root.title("Network Tools")
        self.root.geometry("800x600")

    def _create_main_frame(self):
        """Create and configure the main frame"""
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def _create_notebook(self):
        """Create the notebook for tabs"""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def _create_tabs(self):
        """Create and add all tabs to the notebook"""
        self.tabs = {
            "Devices": self._create_devices_tab(),
            "Custom Commands": CustomCommandTab(self.notebook, self.device_manager),
            "VLAN Discovery": VlanDiscoveryTab(self.notebook, self.device_manager),
            "Network Discovery": NetworkDiscoveryTab(self.notebook, self.device_manager),
            "Local Routes": RouteAnalyzerTab(self.notebook, self.device_manager),
            "Audit": AuditorTab(self.notebook, self.device_manager),
            "Reports": ReporterTab(self.notebook, self.device_manager),
            "Crawler": CrawlerTab(self.notebook, self.device_manager),
            "Route Validator": RouteValidatorTab(self.notebook, self.device_manager)
        }
        
        for name, tab in self.tabs.items():
            self.notebook.add(tab, text=name)

    def _configure_grid(self):
        """Configure grid weights for responsive layout"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def _create_devices_tab(self):
        """Create and configure the devices tab"""
        tab = ttk.Frame(self.notebook, padding="10")
        
        # Create buttons frame
        buttons_frame = ttk.Frame(tab)
        buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Left-side buttons
        left_buttons = ttk.Frame(buttons_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(left_buttons, text="Load Devices from CSV", 
                  command=self._handle_csv_load).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_buttons, text="Connect Selected", 
                  command=self._handle_device_connection).pack(side=tk.LEFT, padx=5)
        
        # Right-side buttons
        right_buttons = ttk.Frame(buttons_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(right_buttons, text="Select All", 
                  command=self._select_all_devices).pack(side=tk.LEFT, padx=5)
        ttk.Button(right_buttons, text="Deselect All", 
                  command=self._deselect_all_devices).pack(side=tk.LEFT, padx=5)
        
        # Create device tree using our custom widget
        self.device_tree = DeviceTreeView(tab)
        self.device_tree.grid_with_scrollbar(row=1, column=0)
        
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        
        return tab

    def _handle_csv_load(self):
        filename = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if filename:
            devices = self.device_manager.load_from_csv(filename)
            self.device_tree.update_devices(devices)

    def _handle_device_connection(self):
        """Handle connecting to selected devices"""
        selected_items = self.device_tree.selection()
        if not selected_items:
            return

        # Get credentials
        dialog = LoginDialog(self.root)
        if not dialog.result:
            return

        username, password, save_credentials = dialog.result
        
        # Save credentials if requested
        if save_credentials:
            self.credentials_manager.save_tacacs_credentials(username, password)

        # Get selected devices and prepare them
        selected_devices = []
        for item in selected_items:
            device = self.device_manager.get_device_by_hostname(
                self.device_tree.item(item)['values'][0]
            )
            if device:
                device.username = username
                device.password = password
                selected_devices.append(device)

        # Create queue for results
        result_queue = queue.Queue()
        
        # Create loading dialog
        loading_dialog = LoadingDialog(
            self.root,
            title="Connecting to Devices",
            message=f"Connecting to {len(selected_devices)} devices..."
        )

        def connection_thread():
            try:
                # Connect devices using DeviceManager
                connected_devices = self.device_manager.connect_devices(selected_devices)
                result_queue.put(("success", connected_devices))
            except Exception as e:
                result_queue.put(("error", str(e)))
            finally:
                # Schedule dialog destruction in main thread
                self.root.after(0, loading_dialog.destroy)

        def check_queue():
            try:
                result_type, result_data = result_queue.get_nowait()
                if result_type == "success":
                    # Update status in tree
                    for device in result_data:
                        status = "Connected" if device.connection else "Connection Failed"
                        self.device_tree.update_device_status(device.hostname, status)
                else:
                    # Show error message
                    tk.messagebox.showerror(
                        "Connection Error",
                        f"Error connecting to devices: {result_data}"
                    )
            except queue.Empty:
                # If queue is empty and thread is still running, check again
                if thread.is_alive():
                    self.root.after(100, check_queue)

        # Start connection thread
        thread = threading.Thread(target=connection_thread)
        thread.daemon = True
        thread.start()

        # Start checking for results
        self.root.after(100, check_queue)

    def _select_all_devices(self):
        """Select all devices in the tree"""
        for item in self.device_tree.get_children():
            self.device_tree.selection_add(item)

    def _deselect_all_devices(self):
        """Deselect all devices in the tree"""
        self.device_tree.selection_remove(self.device_tree.selection())
