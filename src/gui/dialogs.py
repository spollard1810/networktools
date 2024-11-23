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