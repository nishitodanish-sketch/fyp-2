import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
import datetime
import os
from database.db_manager import DatabaseManager
from core.ml_engine import MLEngine

class HistoryFrame(ctk.CTkFrame):
    def __init__(self, parent, monitor):
        super().__init__(parent, fg_color="transparent")
        self.monitor = monitor
        self.db = DatabaseManager()

        self.header = ctk.CTkLabel(self, text="Comprehensive Scan Inventory", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        self.header.pack(pady=(0, 5), anchor="w")
        
        self.sub_label = ctk.CTkLabel(self, text="Global database of all unique files analyzed by the system.",
                                      font=ctk.CTkFont(size=12), text_color="gray")
        self.sub_label.pack(pady=(0, 15), anchor="w")

        # Container for Treeview + Scrollbar
        tree_container = ctk.CTkFrame(self)
        tree_container.pack(fill="both", expand=True)

        columns = ('path', 'size', 'entropy', 'last_seen', 'severity')
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings')
        self.tree.heading('path', text='File Path')
        self.tree.heading('size', text='Size (Bytes)')
        self.tree.heading('entropy', text='Entropy')
        self.tree.heading('last_seen', text='Last Seen')
        self.tree.heading('severity', text='Latest Verdict')

        self.tree.column('path', width=400)
        self.tree.column('size', width=100)
        self.tree.column('entropy', width=80)
        self.tree.column('last_seen', width=140)
        self.tree.column('severity', width=100)

        self.tree.tag_configure('Normal',   background='#2b2b2b', foreground='#2ecc71')
        self.tree.tag_configure('Low',      background='#2b2b2b', foreground='#f1c40f')
        self.tree.tag_configure('Medium',   background='#2b2b2b', foreground='#e67e22')
        self.tree.tag_configure('Critical', background='#e74c3c', foreground='white')

        scrollbar = ctk.CTkScrollbar(tree_container, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # --- Action Buttons ---
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=(15, 0))

        self.export_btn = ctk.CTkButton(self.button_frame, 
                                        text="📊 Generate CSV Report", 
                                        fg_color="#3498db", 
                                        hover_color="#2980b9",
                                        command=self.export_csv)
        self.export_btn.pack(side="right")

    def export_csv(self):
        try:
            filename = f"FIM_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            # We call the ml_engine inside monitor
            self.monitor.ml_engine.export_data(filename)
            
            if os.path.exists(filename):
                messagebox.showinfo("Success", f"Report berjaya dijana!\nFail: {filename}")
            else:
                messagebox.showwarning("Empty", "Tiada data untuk diexport. Sila buat testing dulu.")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menjana report: {e}")

    def on_show(self):
        self._refresh_data()

    def _refresh_data(self):
        files = self.db.get_all_scanned_files()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in files:
            path, last_seen, size, entropy, ext, verdict, score = row
            ts = datetime.datetime.fromtimestamp(last_seen).strftime('%Y-%m-%d %H:%M:%S')
            severity = MLEngine.get_severity(score, verdict)
            
            self.tree.insert('', 'end',
                             values=(path, f"{size:,}", f"{entropy:.4f}", ts, severity),
                             tags=(severity,))
