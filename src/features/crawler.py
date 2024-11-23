import tkinter as tk
from tkinter import ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.gui.widgets import FeatureTab
from src.utils.threader import run_threaded_operation
from src.core.device import Device
from src.core.connector import create_connection
import re
from typing import Dict, Set, Optional
from src.utils.network_validator import NetworkValidator
import yaml

class CrawlerTab(FeatureTab):
    def __init__(self, parent, device_manager):
        super().__init__(parent, device_manager)
        self._create_crawler_widgets()
        self.network_graph = nx.Graph()
        self.network_validator = NetworkValidator()
        self.device_colors = {
            'cisco_ios': '#FF9999',    # Light Red
            'cisco_nxos': '#99FF99',   # Light Green
            'cisco_xr': '#9999FF',     # Light Blue
            'protected': '#FF0000',    # Red
            'unknown': '#CCCCCC'       # Gray
        }

    def _create_crawler_widgets(self):
        # Create control frame
        control_frame = ttk.Frame(self.button_frame)
        control_frame.pack(side=tk.LEFT, padx=5)

        # Max depth selector
        ttk.Label(control_frame, text="Max Depth:").pack(side=tk.LEFT)
        self.max_depth = ttk.Spinbox(control_frame, from_=1, to=10, width=5)
        self.max_depth.set(3)
        self.max_depth.pack(side=tk.LEFT, padx=5)

        # Update run button text
        self.run_button.config(text="Discover Network")

        # Create network view frame
        self.network_frame = ttk.LabelFrame(self, text="Network Topology")
        self.network_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure grid weights for network frame
        self.grid_rowconfigure(3, weight=1)

        # Add Configure Rules button
        self.config_button = ttk.Button(
            control_frame,
            text="Configure Rules",
            command=self._show_rules_dialog
        )
        self.config_button.pack(side=tk.LEFT, padx=5)

    def _parse_cdp_output(self, output: str) -> list:
        """Parse CDP neighbor details output"""
        neighbors = []
        current_neighbor = {}
        
        # Regular expressions for parsing
        device_id_pattern = r"Device ID: (.+)"
        ip_pattern = r"IP address: (.+)"
        platform_pattern = r"Platform: (.+?),"
        
        for line in output.split('\n'):
            if "Device ID:" in line:
                if current_neighbor:
                    neighbors.append(current_neighbor)
                current_neighbor = {}
                match = re.search(device_id_pattern, line)
                if match:
                    current_neighbor['hostname'] = match.group(1)
            elif "IP address:" in line:
                match = re.search(ip_pattern, line)
                if match:
                    current_neighbor['ip'] = match.group(1)
            elif "Platform:" in line:
                match = re.search(platform_pattern, line)
                if match:
                    platform = match.group(1).lower()
                    if 'nexus' in platform:
                        current_neighbor['device_type'] = 'cisco_nxos'
                    elif 'ios-xr' in platform:
                        current_neighbor['device_type'] = 'cisco_xr'
                    else:
                        current_neighbor['device_type'] = 'cisco_ios'
        
        if current_neighbor:
            neighbors.append(current_neighbor)
        
        return neighbors

    def _discover_neighbors(self, device: Device, depth: int, max_depth: int, 
                          visited: Set[str], credentials: Dict[str, str]):
        """Recursively discover network neighbors"""
        if depth > max_depth or not device.connection:
            return

        try:
            # Get CDP neighbors
            output = device.connection.send_command("show cdp neighbors detail")
            neighbors = self._parse_cdp_output(output)
            
            for neighbor in neighbors:
                if neighbor['hostname'] not in visited:
                    visited.add(neighbor['hostname'])
                    
                    # Check if device is allowed
                    is_allowed, reason = self.network_validator.is_allowed(
                        neighbor['ip'], 
                        neighbor['hostname']
                    )
                    
                    # Add to graph regardless of protection status
                    self.network_graph.add_edge(device.hostname, neighbor['hostname'])
                    
                    if not is_allowed:
                        self.add_result(
                            f"Skipping {neighbor['hostname']} ({neighbor['ip']}): {reason}"
                        )
                        continue
                    
                    try:
                        # Create and connect to new device
                        new_device = Device(
                            hostname=neighbor['hostname'],
                            ip=neighbor['ip'],
                            device_type=neighbor.get('device_type', 'cisco_ios'),
                            username=credentials['username'],
                            password=credentials['password']
                        )
                        
                        # Add to device manager if not exists
                        if not self.device_manager.get_device_by_hostname(new_device.hostname):
                            self.device_manager.devices.append(new_device)
                            
                        # Connect to device
                        device_params = {
                            'device_type': new_device.device_type,
                            'ip': new_device.ip,
                            'username': new_device.username,
                            'password': new_device.password,
                        }
                        new_device.connection = create_connection(device_params)
                        
                        if new_device.connection:
                            # Recursive discovery
                            self._discover_neighbors(new_device, depth + 1, max_depth, 
                                                  visited, credentials)
                    except Exception as e:
                        self.add_result(f"Failed to connect to {new_device.hostname}: {str(e)}")
        
        except Exception as e:
            self.add_result(f"Error discovering neighbors for {device.hostname}: {str(e)}")

    def _draw_network_graph(self):
        """Draw the network topology graph"""
        # Clear previous graph
        for widget in self.network_frame.winfo_children():
            widget.destroy()

        # Create figure and canvas
        fig, ax = plt.subplots(figsize=(8, 6))
        canvas = FigureCanvasTkAgg(fig, master=self.network_frame)
        
        # Update node colors to show protected devices
        node_colors = []
        for node in self.network_graph.nodes():
            device = self.device_manager.get_device_by_hostname(node)
            if device:
                is_allowed, _ = self.network_validator.is_allowed(device.ip, device.hostname)
                if not is_allowed:
                    node_colors.append(self.device_colors['protected'])
                else:
                    node_colors.append(self.device_colors.get(device.device_type, 
                                                            self.device_colors['unknown']))
        
        # Draw the graph
        pos = nx.spring_layout(self.network_graph)
        nx.draw(
            self.network_graph,
            pos,
            ax=ax,
            with_labels=True,
            node_color=node_colors,
            node_size=1000,
            font_size=8,
            font_weight='bold'
        )
        
        # Create legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=color, label=device_type, markersize=10)
            for device_type, color in self.device_colors.items()
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        # Pack the canvas
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def run_operation(self):
        super().run_operation()
        
        # Get root device (first connected device)
        root_device = next((d for d in self.device_manager.devices if d.connection), None)
        if not root_device:
            self.update_status("No connected devices found")
            return

        # Clear previous graph
        self.network_graph.clear()
        self.network_graph.add_node(root_device.hostname)

        # Get credentials from root device
        credentials = {
            'username': root_device.username,
            'password': root_device.password
        }

        # Start discovery
        max_depth = int(self.max_depth.get())
        visited = set()
        
        self.update_status("Discovering network topology...")
        self._discover_neighbors(root_device, 1, max_depth, visited, credentials)
        
        # Draw the network graph
        self.update_status("Drawing network topology...")
        self._draw_network_graph()
        
        # Update device tree in main window
        self.device_manager.update_device_tree()
        
        self.update_status("Network discovery complete")

    def _show_rules_dialog(self):
        """Show dialog for configuring network boundaries"""
        from src.gui.dialogs import CrawlerRulesDialog
        dialog = CrawlerRulesDialog(self, self.network_validator)
        if dialog.result:
            # Update network validator with new configuration
            config_file = self.network_validator.config_dir / 'network_boundaries.yaml'
            with open(config_file, 'w') as f:
                yaml.dump(dialog.result, f, default_flow_style=False)
            # Reload the configuration
            self.network_validator.load_network_config()
