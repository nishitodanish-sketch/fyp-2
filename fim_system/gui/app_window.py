import customtkinter as ctk
from .dashboard_frame import DashboardFrame
from .events_frame import EventsFrame
from .quarantine_frame import QuarantineFrame
from .settings_frame import SettingsFrame
from .history_frame import HistoryFrame
from core.monitor import FileMonitor

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Anomaly-Based FIM System - PRO")
        self.geometry("1100x750")
        
        # Initialize Monitor
        self.monitor = FileMonitor([])
        
        # Grid layout (1x2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main_container()
        
    def _create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FIM CORE", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.btn_dash = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=lambda: self.show_frame(DashboardFrame))
        self.btn_dash.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_live = ctk.CTkButton(self.sidebar_frame, text="Live Events", command=lambda: self.show_frame(EventsFrame))
        self.btn_live.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_hist = ctk.CTkButton(self.sidebar_frame, text="Scan History", command=lambda: self.show_frame(HistoryFrame))
        self.btn_hist.grid(row=3, column=0, padx=20, pady=10)
        
        self.btn_quar = ctk.CTkButton(self.sidebar_frame, text="Quarantine", command=lambda: self.show_frame(QuarantineFrame))
        self.btn_quar.grid(row=4, column=0, padx=20, pady=10)
        
        self.btn_sett = ctk.CTkButton(self.sidebar_frame, text="Settings", command=lambda: self.show_frame(SettingsFrame))
        self.btn_sett.grid(row=5, column=0, padx=20, pady=10)
        
        self.exit_button = ctk.CTkButton(self.sidebar_frame, text="Exit System", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.quit)
        self.exit_button.grid(row=7, column=0, padx=20, pady=20)

    def _create_main_container(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.frames = {}
        for F in (DashboardFrame, EventsFrame, HistoryFrame, QuarantineFrame, SettingsFrame):
            frame = F(self.content_frame, self.monitor)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')
            
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        self.show_frame(DashboardFrame)
        
    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.on_show() 
        frame.tkraise()

    def quit(self):
        self.monitor.stop()
        super().quit()
