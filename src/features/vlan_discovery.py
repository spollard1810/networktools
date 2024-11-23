import tkinter as tk
from src.gui.widgets import FeatureTab
from src.utils.threader import run_threaded_operation

class VlanDiscoveryTab(FeatureTab):
    def __init__(self, parent, device_manager):
        super().__init__(parent, device_manager)
        
        # Add any VLAN-specific widgets
        self.run_button.config(text="Discover VLANs")

    def run_operation(self):
        super().run_operation()
        connected_devices = [d for d in self.device_manager.devices if d.connection]
        
        def discover_vlans(device):
            try:
                connection = device.connection
                output = connection.send_command("show vlan brief")
                return (device.hostname, output)
            except Exception as e:
                return (device.hostname, f"Error: {str(e)}")

        # Run discovery in threads
        results = run_threaded_operation(discover_vlans, connected_devices)
        
        # Process and display results
        self.results_text.delete('1.0', tk.END)
        for hostname, output in results:
            self.add_result(f"\n=== {hostname} ===\n{output}\n")
