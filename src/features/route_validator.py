from typing import List, Dict
import tkinter as tk
from tkinter import ttk
import yaml
from ipaddress import IPv4Network
from src.gui.widgets import FeatureTab
from src.core.micetro_client import MicetroClient
import logging

class RouteValidatorTab(FeatureTab):
    # Hardcoded interregional routers, change in env
    CORE_ROUTERS = [
        "router1.example.com",
        "router2.example.com",
        "router3.example.com",
        "router4.example.com",
        "router5.example.com",
        "router6.example.com"
    ]

    def __init__(self, parent, device_manager):
        super().__init__(parent, device_manager)
        self.micetro_client = None
        self._create_validator_widgets()

    def _create_validator_widgets(self):
        # Micetro Connection Frame
        conn_frame = ttk.LabelFrame(self, text="Micetro Connection", padding="5")
        conn_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        # URL
        ttk.Label(conn_frame, text="URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(conn_frame, width=40)
        self.url_entry.grid(row=0, column=1, padx=5, pady=2)

        # Username
        ttk.Label(conn_frame, text="Username:").grid(row=1, column=0, sticky=tk.W)
        self.username_entry = ttk.Entry(conn_frame, width=40)
        self.username_entry.grid(row=1, column=1, padx=5, pady=2)

        # Password
        ttk.Label(conn_frame, text="Password:").grid(row=2, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(conn_frame, width=40, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=2)

        # Results Treeview
        self.results_tree = ttk.Treeview(
            self.results_frame,
            columns=("Network", "Source", "Status"),
            show="headings"
        )
        
        # Configure headers
        self.results_tree.heading("Network", text="Network")
        self.results_tree.heading("Source", text="Source")
        self.results_tree.heading("Status", text="Status")
        
        self.results_tree.pack(fill=tk.BOTH, expand=True)

    def run_operation(self):
        """Main operation to validate routes"""
        self.start_operation()
        self.results_tree.delete(*self.results_tree.get_children())

        try:
            # Initialize Micetro client
            self.micetro_client = MicetroClient(
                self.url_entry.get(),
                self.username_entry.get(),
                self.password_entry.get()
            )

            # Load supernets from YAML
            with open('config/supernets.yaml', 'r') as f:
                supernets = yaml.safe_load(f)

            # Get networks from Micetro
            micetro_networks = self.micetro_client.get_networks()
            
            # Get routing tables from core routers
            router_routes = self._get_router_routes()

            # Compare and analyze
            self._analyze_networks(micetro_networks, router_routes, supernets)

        except Exception as e:
            self.add_result(f"Error: {str(e)}")
        finally:
            self.finish_operation()

    def _get_router_routes(self) -> Dict[str, List[IPv4Network]]:
        """Get routes from all core routers"""
        routes = {}
        for router in self.CORE_ROUTERS:
            device = self.device_manager.get_device_by_hostname(router)
            if device and device.connection:
                routes[router] = self._get_routes_from_device(device)
        return routes

    def _get_routes_from_device(self, device) -> List[IPv4Network]:
        """
        Extract routes from a single device using READ-ONLY commands
        Returns: List of IPv4Network objects
        """
        routes = []
        try:
            # Ensure we're only using show commands
            output = device.connection.send_command(
                "show ip route", 
                use_textfsm=True
            )
            
            # Safety check - ensure we're not in config mode
            if '%' in output or '(config' in output:
                self.logger.error(f"Unexpected output format from device {device.hostname}")
                return routes

            # Parse the routing table output
            if isinstance(output, list):  # TextFSM parsed output
                for route in output:
                    try:
                        if 'network' in route and 'mask' in route:
                            network = IPv4Network(f"{route['network']}/{route['mask']}")
                            routes.append(network)
                    except ValueError as e:
                        self.logger.warning(f"Invalid route format: {e}")
            else:
                self.logger.warning("TextFSM parsing failed, falling back to manual parsing")
                # Basic parsing of show ip route output
                for line in output.splitlines():
                    if line.startswith(('B', 'O', 'S', 'C', 'D', 'R')):  # Route types
                        try:
                            # Extract network/mask using regex or string operations
                            # This is a simplified example - adjust based on your router output
                            network_str = line.split()[1]
                            if '/' in network_str:
                                routes.append(IPv4Network(network_str))
                        except (ValueError, IndexError) as e:
                            self.logger.warning(f"Could not parse route: {e}")
        except Exception as e:
            self.logger.error(f"Error getting routes from {device.hostname}: {e}")
        
        return routes

    def _analyze_networks(self, micetro_networks, router_routes, supernets):
        """Compare networks and update results tree"""
        for network in micetro_networks:
            self.results_tree.insert("", tk.END, values=(
                str(network),
                "Micetro",
                self._validate_network(network, router_routes, supernets)
            ))

        # Add routes from routers that aren't in Micetro
        for router, routes in router_routes.items():
            for route in routes:
                if route not in micetro_networks:
                    self.results_tree.insert("", tk.END, values=(
                        str(route),
                        router,
                        "Not in Micetro"
                    ))

    def _validate_network(self, network, router_routes, supernets) -> str:
        """Validate a single network against routes and supernets"""
        # Check if network is within any supernet
        in_supernet = any(network.subnet_of(IPv4Network(supernet)) 
                         for supernet in supernets)
        if not in_supernet:
            return "Outside defined supernets"

        # Check if network is in routing tables
        found_in_routes = False
        for routes in router_routes.values():
            if network in routes:
                found_in_routes = True
                break

        return "Valid" if found_in_routes else "Missing from routing tables" 