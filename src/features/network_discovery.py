import tkinter as tk
from src.gui.widgets import FeatureTab
from src.utils.threader import run_threaded_operation

class NetworkDiscoveryTab(FeatureTab):
    def __init__(self, parent, device_manager):
        super().__init__(parent, device_manager)
        self.run_button.config(text="Discover Network")

    def run_operation(self):
        super().run_operation()
        connected_devices = [d for d in self.device_manager.devices if d.connection]
        
        def discover_network(device):
            try:
                connection = device.connection
                cdp_output = connection.send_command("show cdp neighbors detail")
                lldp_output = connection.send_command("show lldp neighbors detail")
                return (device.hostname, f"CDP:\n{cdp_output}\n\nLLDP:\n{lldp_output}")
            except Exception as e:
                return (device.hostname, f"Error: {str(e)}")

        results = run_threaded_operation(discover_network, connected_devices)
        
        for hostname, output in results:
            self.add_result(f"\n=== {hostname} ===\n{output}\n")
