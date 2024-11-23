import tkinter as tk
from tkinter import ttk
from src.gui.widgets import FeatureTab
from src.utils.report_manager import ReportManager
from datetime import datetime

class ReporterTab(FeatureTab):
    def __init__(self, parent, device_manager):
        super().__init__(parent, device_manager)
        self.report_manager = ReportManager()
        self._create_report_widgets()

    def _create_report_widgets(self):
        # Create filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(filter_frame, text="Report Type:").pack(side=tk.LEFT, padx=5)
        self.report_type = ttk.Combobox(filter_frame, values=["All", "audit"])
        self.report_type.set("All")
        self.report_type.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Refresh", 
                  command=self._load_reports).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Delete Selected", 
                  command=self._delete_selected).pack(side=tk.LEFT, padx=5)

        # Create reports tree
        self.reports_tree = ttk.Treeview(
            self,
            columns=("Timestamp", "Type", "Device", "Status"),
            show="headings"
        )
        
        # Configure headers
        headers = {
            "Timestamp": ("Timestamp", 150),
            "Type": ("Type", 100),
            "Device": ("Device", 150),
            "Status": ("Status", 100)
        }
        
        for col, (text, width) in headers.items():
            self.reports_tree.heading(col, text=text)
            self.reports_tree.column(col, width=width)
        
        self.reports_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.reports_tree.bind('<<TreeviewSelect>>', self._on_select_report)
        
        # Load initial reports
        self._load_reports()

    def _load_reports(self):
        # Clear existing items
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)
        
        # Get reports
        report_type = None if self.report_type.get() == "All" else self.report_type.get()
        reports = self.report_manager.get_reports(report_type)
        
        # Add reports to tree
        for report in reports:
            status = "Issues Found" if "No issues found" not in report.results else "Clean"
            self.reports_tree.insert("", tk.END, values=(
                report.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                report.report_type,
                report.device_hostname,
                status
            ))

    def _on_select_report(self, event):
        selected = self.reports_tree.selection()
        if not selected:
            return
        
        # Get selected report
        item = self.reports_tree.item(selected[0])
        values = item['values']
        
        # Find corresponding report
        reports = self.report_manager.get_reports()
        for report in reports:
            if (report.timestamp.strftime('%Y-%m-%d %H:%M:%S') == values[0] and
                report.device_hostname == values[2]):
                # Display report details
                self.results_text.delete('1.0', tk.END)
                self.results_text.insert(tk.END, f"Device: {report.device_hostname}\n")
                self.results_text.insert(tk.END, f"IP: {report.device_info.get('ip', 'N/A')}\n")
                self.results_text.insert(tk.END, f"Type: {report.device_info.get('device_type', 'N/A')}\n")
                self.results_text.insert(tk.END, f"Timestamp: {report.timestamp}\n")
                self.results_text.insert(tk.END, f"\nResults:\n{report.results}\n")
                break

    def _delete_selected(self):
        selected = self.reports_tree.selection()
        if not selected:
            return
            
        # Delete selected reports
        for item in selected:
            values = self.reports_tree.item(item)['values']
            timestamp = datetime.strptime(values[0], '%Y-%m-%d %H:%M:%S')
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{values[2]}.json"
            self.report_manager.delete_report(values[1], filename)
        
        # Refresh display
        self._load_reports()
