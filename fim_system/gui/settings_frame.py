import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from database.db_manager import DatabaseManager
from config import MODEL_PATH

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, monitor):
        super().__init__(parent, fg_color="transparent")
        self.monitor = monitor
        self.db = DatabaseManager()

        self.header = ctk.CTkLabel(self, text="System Configuration", 
                                   font=ctk.CTkFont(size=28, weight="bold"))
        self.header.pack(pady=(0, 20), anchor="w")

        # --- Reset Section ---
        self.reset_card = ctk.CTkFrame(self, border_width=1, border_color="#c0392b")
        self.reset_card.pack(fill="x", pady=10)
        
        ctk.CTkLabel(self.reset_card, text="FACTORY RESET", 
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="#c0392b").pack(pady=(10, 5), padx=15, anchor="w")
        
        ctk.CTkLabel(self.reset_card, 
                     text="Wipe all database records, quarantine files, and the ML model.\nUse this to start a completely fresh training session.",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(padx=15, anchor="w")
        
        self.btn_reset = ctk.CTkButton(self.reset_card, text="RESET SYSTEM", 
                                       fg_color="#c0392b", hover_color="#a93226",
                                       command=self.reset_all)
        self.btn_reset.pack(pady=15, padx=15, anchor="w")

        # --- Monitored Directories ---
        self.dir_card = ctk.CTkFrame(self)
        self.dir_card.pack(fill="x", pady=10)
        
        ctk.CTkLabel(self.dir_card, text="MONITORED DIRECTORIES", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5), padx=15, anchor="w")

        list_container = ctk.CTkFrame(self.dir_card, fg_color="transparent")
        list_container.pack(fill="x", padx=15, pady=5)

        self.listbox = tk.Listbox(list_container, height=4, bg="#2b2b2b", fg="white", 
                                  borderwidth=0, highlightthickness=0, font=("Inter", 10))
        self.listbox.pack(side="left", fill="x", expand=True)

        btn_row = ctk.CTkFrame(self.dir_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(btn_row, text="ADD FOLDER", width=120, command=self.add_folder).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="REMOVE", width=120, fg_color="#34495e", command=self.remove_folder).pack(side="left", padx=5)

    def on_show(self):
        self.refresh_list()

    def reset_all(self):
        if not messagebox.askyesno("CONFIRM RESET", "Are you sure? This will delete ALL data and models."):
            return
        
        if self.monitor.active:
            self.monitor.stop()
        self.db.clear_all_data()
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        self.monitor.ml_engine.is_fitted = False
        self.monitor.paths.clear()
        self.refresh_list()
        messagebox.showinfo("Reset", "System reset successful.")

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for path in self.monitor.paths:
            self.listbox.insert(tk.END, path)

    def add_folder(self):
        path = filedialog.askdirectory()
        if path and path not in self.monitor.paths:
            self.monitor.paths.append(path)
            self.refresh_list()
            if self.monitor.active:
                self.monitor.stop()
                self.monitor.start()

    def remove_folder(self):
        sel = self.listbox.curselection()
        if sel:
            path = self.listbox.get(sel[0])
            self.monitor.paths.remove(path)
            self.refresh_list()
            if self.monitor.active:
                self.monitor.stop()
                self.monitor.start()
