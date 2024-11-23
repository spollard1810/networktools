import tkinter as tk
from tkinter import ttk
import re
from src.gui.widgets import FeatureTab
from src.utils.threader import run_threaded_operation
from src.utils.audit_rules import AuditRuleManager, AuditRule
from src.utils.report_manager import Report, ReportManager
from datetime import datetime

class AuditRuleDialog(tk.Toplevel):
    def __init__(self, parent, rule: AuditRule = None):
        super().__init__(parent)
        self.title("Add/Edit Audit Rule")
        self.rule = rule
        self.result = None
        
        self._create_widgets()
        self._populate_fields()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                 parent.winfo_rooty() + 50))

    def _create_widgets(self):
        # Create form fields
        fields = [
            ("Name:", "name"),
            ("Command:", "command"),
            ("Pattern:", "pattern"),
            ("Description:", "description")
        ]
        
        self.entries = {}
        for i, (label, field) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=0, padx=5, pady=5)
            self.entries[field] = ttk.Entry(self, width=40)
            self.entries[field].grid(row=i, column=1, padx=5, pady=5)

        # Severity dropdown
        ttk.Label(self, text="Severity:").grid(row=len(fields), column=0, padx=5, pady=5)
        self.severity = ttk.Combobox(self, values=["Low", "Medium", "High", "Critical"])
        self.severity.grid(row=len(fields), column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

    def _populate_fields(self):
        if self.rule:
            self.entries["name"].insert(0, self.rule.name)
            self.entries["command"].insert(0, self.rule.command)
            self.entries["pattern"].insert(0, self.rule.pattern)
            self.entries["description"].insert(0, self.rule.description)
            self.severity.set(self.rule.severity)

    def _save(self):
        self.result = AuditRule(
            name=self.entries["name"].get(),
            command=self.entries["command"].get(),
            pattern=self.entries["pattern"].get(),
            severity=self.severity.get(),
            description=self.entries["description"].get()
        )
        self.destroy()

class AuditorTab(FeatureTab):
    def __init__(self, parent, device_manager):
        super().__init__(parent, device_manager)
        self.rule_manager = AuditRuleManager()
        self._create_audit_widgets()

    def _create_audit_widgets(self):
        # Create rules frame
        rules_frame = ttk.LabelFrame(self, text="Audit Rules")
        rules_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Rules list
        self.rules_tree = ttk.Treeview(
            rules_frame,
            columns=("Name", "Severity", "Description"),
            show="headings"
        )
        
        for col in ("Name", "Severity", "Description"):
            self.rules_tree.heading(col, text=col)
        
        self.rules_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons
        button_frame = ttk.Frame(rules_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(button_frame, text="Add Rule", 
                  command=self._add_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Rule", 
                  command=self._edit_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Rule", 
                  command=self._delete_rule).pack(side=tk.LEFT, padx=5)
        
        self._load_rules()

    def _load_rules(self):
        """Load rules into the treeview"""
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
            
        for rule in self.rule_manager.get_all_rules():
            self.rules_tree.insert("", tk.END, values=(
                rule.name, rule.severity, rule.description
            ))

    def _add_rule(self):
        dialog = AuditRuleDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.rule_manager.save_rule(dialog.result)
            self._load_rules()

    def _edit_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            return
            
        rule_name = self.rules_tree.item(selected[0])['values'][0]
        rule = self.rule_manager.get_rule(rule_name)
        if rule:
            dialog = AuditRuleDialog(self, rule)
            self.wait_window(dialog)
            if dialog.result:
                self.rule_manager.save_rule(dialog.result)
                self._load_rules()

    def _delete_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            return
            
        rule_name = self.rules_tree.item(selected[0])['values'][0]
        self.rule_manager.delete_rule(rule_name)
        self._load_rules()

    def run_operation(self):
        super().run_operation()
        connected_devices = [d for d in self.device_manager.devices if d.connection]
        rules = self.rule_manager.get_all_rules()
        
        def audit_device(device):
            try:
                results = []
                connection = device.connection
                
                for rule in rules:
                    output = connection.send_command(rule.command)
                    if re.search(rule.pattern, output):
                        results.append(
                            f"[{rule.severity}] {rule.name}: {rule.description}"
                        )
                
                # Create report
                report = Report(
                    report_type="audit",
                    device_hostname=device.hostname,
                    timestamp=datetime.now(),
                    results="\n".join(results) if results else "No issues found",
                    device_info={
                        'ip': device.ip,
                        'device_type': device.device_type
                    }
                )
                
                # Save report
                ReportManager().save_report(report)
                
                return (device.hostname, report.results)
            except Exception as e:
                return (device.hostname, f"Error: {str(e)}")

        results = run_threaded_operation(audit_device, connected_devices)
        
        self.results_text.delete('1.0', tk.END)
        for hostname, output in results:
            self.add_result(f"\n=== {hostname} ===\n{output}\n")
