import tkinter as tk
from src.gui.widgets import FeatureTab
from src.utils.threader import run_threaded_operation

class RouteAnalyzerTab(FeatureTab):
    def __init__(self, parent, device_manager):
        super().__init__(parent, device_manager)
        self.run_button.config(text="Analyze Routes")

    def run_operation(self):
        super().run_operation()
        connected_devices = [d for d in self.device_manager.devices if d.connection]
        
        def analyze_routes(device):
            try:
                connection = device.connection
                routes = connection.send_command("show ip route")
                return (device.hostname, routes)
            except Exception as e:
                return (device.hostname, f"Error: {str(e)}")

        results = run_threaded_operation(analyze_routes, connected_devices)
        
        for hostname, output in results:
            self.add_result(f"\n=== {hostname} ===\n{output}\n")
