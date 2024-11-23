import tkinter as tk
from src.gui.widgets import FeatureTab
from src.utils.threader import run_threaded_operation
import ipaddress

class SubnetCalculatorTab(FeatureTab):
    def __init__(self, parent, device_manager):
        super().__init__(parent, device_manager)
        self.run_button.config(text="Calculate Subnet")


