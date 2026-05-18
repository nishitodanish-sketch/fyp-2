import customtkinter as ctk
from tkinter import ttk
import datetime
from database.db_manager import DatabaseManager
from core.ml_engine import MLEngine

class EventsFrame(ctk.CTkFrame):
    def __init__(self, parent, monitor):
        super().__init__(parent, fg_color="transparent")
        self.monitor = monitor
        self.db = DatabaseManager()

        self.header = ctk.CTkLabel(self, text="Real-time Security Events", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        self.header.pack(pady=(0, 10), anchor="w")

        # Status sub-label
        self.watched_label = ctk.CTkLabel(self, text="Watching: (not started)",
                                          font=ctk.CTkFont(size=12), text_color="gray")
        self.watched_label.pack(anchor='w', padx=5, pady=(0, 15))

        # Styling the Treeview (Standard ttk)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        fieldbackground="#2b2b2b",
                        rowheight=25)
        style.map("Treeview", background=[('selected', '#3498db')])
        style.configure("Treeview.Heading", 
                        background="#1f1f1f", 
                        foreground="white", 
                        relief="flat")

        # Container for Treeview + Scrollbar
        tree_container = ctk.CTkFrame(self)
        tree_container.pack(fill="both", expand=True)

        columns = ('id', 'type', 'path', 'timestamp', 'severity', 'reason')
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('type', text='Event')
        self.tree.heading('path', text='Path')
        self.tree.heading('timestamp', text='Time')
        self.tree.heading('severity', text='Severity')
        self.tree.heading('reason', text='Reason')

        self.tree.column('id', width=50)
        self.tree.column('type', width=90)
        self.tree.column('path', width=400)
        self.tree.column('timestamp', width=120)
        self.tree.column('severity', width=80)
        self.tree.column('reason', width=150)

        # Tags for coloring
        self.tree.tag_configure('Normal',   background='#2b2b2b', foreground='#2ecc71')
        self.tree.tag_configure('Trained',  background='#2b2b2b', foreground='#3498db')
        self.tree.tag_configure('Low',      background='#2b2b2b', foreground='#f1c40f')
        self.tree.tag_configure('Medium',   background='#2b2b2b', foreground='#e67e22')
        self.tree.tag_configure('Critical', background='#e74c3c', foreground='white')

        scrollbar = ctk.CTkScrollbar(tree_container, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self._schedule_refresh()

    def on_show(self):
        self._update_watched_label()
        self._refresh_data()

    def _update_watched_label(self):
        paths = self.monitor.paths
        if not paths:
            self.watched_label.configure(text="STATUS: No folders selected")
        elif self.monitor.active:
            self.watched_label.configure(text=f"PROTECTING: {' | '.join(paths)}", text_color="#2ecc71")
        else:
            self.watched_label.configure(text=f"PAUSED: {' | '.join(paths)}", text_color="gray")

    def _schedule_refresh(self):
        try:
            self._refresh_data()
        except Exception: 
            # Silent failure during UI refresh is acceptable to prevent dashboard flickering
            pass
        finally:
            self.after(2000, self._schedule_refresh)

    def _refresh_data(self):
        events = self.db.get_recent_events_with_verdict(limit=5000)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in events:
            # event_id, event_type, file_path, timestamp, verdict, score, is_training, reason = row
            event_id, event_type, file_path, timestamp, verdict, score, is_training, reason = row
            ts = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            
            if is_training:
                severity = "Trained"
                reason = "Training Sample"
            else:
                severity = MLEngine.get_severity(score, verdict)
                
            self.tree.insert('', 'end',
                             values=(event_id, event_type, file_path, ts, severity, reason),
                             tags=(severity,))
