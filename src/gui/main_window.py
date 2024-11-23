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
from .dialogs import LoginDialog
from src.core.connector import create_connection
from src.features.custom_command import CustomCommandTab

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
            "Crawler": CrawlerTab(self.notebook, self.device_manager)
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

        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Connecting to Devices")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Center the progress window
        progress_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # Add progress bar and label
        ttk.Label(progress_window, text="Connecting to devices...").pack(pady=10)
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window, 
            length=300, 
            mode='determinate',
            variable=progress_var
        )
        progress_bar.pack(padx=10, pady=5)
        status_label = ttk.Label(progress_window, text="")
        status_label.pack(pady=5)

        # Update device parameters with credentials
        selected_devices = [
            self.device_manager.get_device_by_hostname(
                self.device_tree.item(item)['values'][0]
            )
            for item in selected_items
        ]

        # Add credentials to each device
        for device in selected_devices:
            device.username = username
            device.password = password

        total_devices = len(selected_devices)
        progress_step = 100.0 / total_devices if total_devices > 0 else 0

        def connect_and_update():
            for i, device in enumerate(selected_devices):
                # Update progress
                progress_var.set(i * progress_step)
                status_label.config(text=f"Connecting to {device.hostname}...")
                progress_window.update()

                # Connect to device
                device_params = {
                    'device_type': device.device_type,
                    'ip': device.ip,
                    'username': device.username,
                    'password': device.password,
                }
                device.connection = create_connection(device_params)
                
                # Update device status in tree
                status = "Connected" if device.connection else "Connection Failed"
                self.device_tree.update_device_status(device.hostname, status)
                
            # Close progress window
            progress_window.destroy()

        # Run connection process in a separate thread
        import threading
        connection_thread = threading.Thread(target=connect_and_update)
        connection_thread.start()

    def _select_all_devices(self):
        """Select all devices in the tree"""
        for item in self.device_tree.get_children():
            self.device_tree.selection_add(item)

    def _deselect_all_devices(self):
        """Deselect all devices in the tree"""
        self.device_tree.selection_remove(self.device_tree.selection())
