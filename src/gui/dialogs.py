import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple

class LoginDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("TACACS Login")
        self.result: Optional[Tuple[str, str]] = None
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Create widgets
        self._create_widgets()
        
        # Center dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                 parent.winfo_rooty() + 50))
        
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        
        # Wait for window to be destroyed
        self.wait_window(self)

    def _create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Username
        ttk.Label(main_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
        self.username = ttk.Entry(main_frame, width=30)
        self.username.grid(row=0, column=1, padx=5, pady=5)
        
        # Password
        ttk.Label(main_frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
        self.password = ttk.Entry(main_frame, width=30, show="*")
        self.password.grid(row=1, column=1, padx=5, pady=5)
        
        # Save credentials checkbox
        self.save_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Save credentials", 
                       variable=self.save_var).grid(row=2, column=0, 
                       columnspan=2, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.LEFT)

    def _ok(self):
        self.result = (self.username.get(), self.password.get(), self.save_var.get())
        self.destroy()

    def _cancel(self):
        self.destroy() 

class CrawlerRulesDialog(tk.Toplevel):
    def __init__(self, parent, network_validator):
        super().__init__(parent)
        self.title("Configure Network Boundaries")
        self.result = None
        self.network_validator = network_validator
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Center dialog
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.wait_window(self)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Subnets tab
        subnets_frame = ttk.Frame(notebook)
        notebook.add(subnets_frame, text="Allowed Subnets")
        
        self.subnet_tree = ttk.Treeview(subnets_frame, columns=("Subnet",), show="headings")
        self.subnet_tree.heading("Subnet", text="Subnet")
        self.subnet_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Protected devices tab
        devices_frame = ttk.Frame(notebook)
        notebook.add(devices_frame, text="Protected Devices")
        
        self.device_tree = ttk.Treeview(devices_frame, columns=("Hostname",), show="headings")
        self.device_tree.heading("Hostname", text="Hostname")
        self.device_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Populate trees
        for subnet in self.network_validator.allowed_subnets:
            self.subnet_tree.insert("", tk.END, values=(str(subnet),))
        
        for device in self.network_validator.protected_devices:
            self.device_tree.insert("", tk.END, values=(device,))

        # Buttons for both tabs
        for tree, frame, add_text in [(self.subnet_tree, subnets_frame, "Add Subnet"), 
                                    (self.device_tree, devices_frame, "Add Device")]:
            btn_frame = ttk.Frame(frame)
            btn_frame.grid(row=1, column=0, pady=5)
            ttk.Button(btn_frame, text=add_text, 
                      command=lambda t=tree: self._add_item(t)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Delete", 
                      command=lambda t=tree: self._delete_item(t)).pack(side=tk.LEFT)

        # OK/Cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=10)
        ttk.Button(button_frame, text="OK", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.LEFT)

    def _add_item(self, tree):
        dialog = tk.simpledialog.askstring(
            "Add Item",
            "Enter subnet (CIDR) or hostname:",
            parent=self
        )
        if dialog:
            tree.insert("", tk.END, values=(dialog,))

    def _delete_item(self, tree):
        selected = tree.selection()
        if selected:
            tree.delete(selected)

    def _ok(self):
        # Convert tree items to lists
        subnets = [tree.item(item)["values"][0] 
                  for item in self.subnet_tree.get_children()]
        devices = [tree.item(item)["values"][0] 
                  for item in self.device_tree.get_children()]
        
        self.result = {
            "allowed_subnets": subnets,
            "protected_devices": devices
        }
        self.destroy()

    def _cancel(self):
        self.destroy()

class RuleDialog(tk.Toplevel):
    def __init__(self, parent, current_values=None):
        super().__init__(parent)
        self.title("Rule Configuration")
        self.result = None
        self.current_values = current_values
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Center dialog
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.wait_window(self)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Rule fields
        fields = [
            ("Type:", "type_var", ("ip", "hostname")),
            ("Pattern:", "pattern", None),
            ("Action:", "action_var", ("allow", "deny"))
        ]

        for i, (label, attr, values) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W)
            if values:
                setattr(self, attr, tk.StringVar(value=self.current_values[i] if self.current_values else ""))
                widget = ttk.Combobox(main_frame, textvariable=getattr(self, attr))
                widget['values'] = values
            else:
                widget = ttk.Entry(main_frame, width=30)
                setattr(self, attr, widget)
                if self.current_values:
                    widget.insert(0, self.current_values[i])
            widget.grid(row=i, column=1, padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="OK", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.LEFT)

    def _ok(self):
        self.result = (
            self.type_var.get(),
            self.pattern.get() if isinstance(self.pattern, ttk.Entry) else self.pattern.get(),
            self.action_var.get()
        )
        self.destroy()

    def _cancel(self):
        self.destroy() 

class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, title="Please Wait", message="Operation in progress..."):
        super().__init__(parent)
        self.title(title)
        
        # Remove window decorations and make it modal
        self.transient(parent)
        self.grab_set()
        
        # Remove minimize/maximize buttons
        self.resizable(False, False)
        
        # Create widgets
        self.frame = ttk.Frame(self, padding="20")
        self.frame.grid(row=0, column=0)
        
        self.label = ttk.Label(self.frame, text=message)
        self.label.grid(row=0, column=0, pady=(0, 10))
        
        self.progress = ttk.Progressbar(
            self.frame, 
            mode='indeterminate', 
            length=200
        )
        self.progress.grid(row=1, column=0)
        self.progress.start(10)
        
        # Center dialog
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))