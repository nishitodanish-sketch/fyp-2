import os
import customtkinter as ctk
from database.db_manager import DatabaseManager
import threading
import queue
import time
from tkinter import messagebox
from core.responder import alert_queue

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, monitor):
        super().__init__(parent, fg_color="transparent")
        self.monitor = monitor
        self.db = DatabaseManager()
        self.alert_queue = queue.Queue()
        self.popup_active = False
        self.is_scanning = False

        # Header
        self.header = ctk.CTkLabel(self, text="Security Intelligence Dashboard", 
                                   font=ctk.CTkFont(size=28, weight="bold"))
        self.header.pack(pady=(0, 20), anchor="w")

        # Top row: System Controls & Mode
        self.top_row = ctk.CTkFrame(self, fg_color="transparent")
        self.top_row.pack(fill="x", pady=10)

        self.btn_toggle = ctk.CTkButton(self.top_row, text="START PROTECTION", 
                                        height=40, font=ctk.CTkFont(weight="bold"),
                                        fg_color="#2ecc71", hover_color="#27ae60",
                                        command=self.toggle_monitor)
        self.btn_toggle.pack(side="left", padx=5)

        self.btn_scan = ctk.CTkButton(self.top_row, text="SCAN FOLDER", 
                                       height=40, font=ctk.CTkFont(weight="bold"),
                                       fg_color="#3498db", hover_color="#2980b9",
                                       command=self.scan_existing)
        self.btn_scan.pack(side="left", padx=5)

        self.seg_mode = ctk.CTkSegmentedButton(self.top_row, values=["Training", "Detection"],
                                               command=self.toggle_mode_seg)
        self.seg_mode.set("Detection")
        self.seg_mode.pack(side="right", padx=5)

        # Main Stats Grid
        self.stats_container = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_container.pack(fill="both", expand=True, pady=20)
        self.stats_container.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_events = self._create_stat_card(self.stats_container, "TOTAL EVENTS", "0", 0)
        self.card_anomalies = self._create_stat_card(self.stats_container, "THREATS BLOCKED", "0", 1, color="#e74c3c")
        self.card_samples = self._create_stat_card(self.stats_container, "MODEL KNOWLEDGE", "0", 2, color="#3498db")

        # Bottom Info Status Card
        self.info_card = ctk.CTkFrame(self, corner_radius=15, border_width=1, border_color="#34495e")
        self.info_card.pack(fill="x", pady=20)
        
        self.lbl_status = ctk.CTkLabel(self.info_card, text="SYSTEM STATUS: IDLE", 
                                       font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_status.pack(pady=(15, 5))
        
        self.lbl_details = ctk.CTkLabel(self.info_card, text="Waiting for user to start protection...", 
                                        font=ctk.CTkFont(size=13), text_color="gray")
        self.lbl_details.pack(pady=(0, 15))

        # Start loops
        self._update_stats_loop()
        self._poll_alerts()

    def _create_stat_card(self, parent, title, value, col, color=None):
        card = ctk.CTkFrame(parent, corner_radius=15, border_width=2, border_color="#2c3e50")
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        
        title_lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        title_lbl.pack(pady=(20, 0))
        
        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=42, weight="bold"), text_color=color)
        val_lbl.pack(pady=(5, 20))
        
        return val_lbl

    def on_show(self):
        self._update_stats()

    def toggle_monitor(self):
        if self.monitor.active:
            self.monitor.stop()
            # Clear any pending alerts so they don't pop up after stopping
            while not self.alert_queue.empty():
                try: 
                    self.alert_queue.get_nowait()
                except Exception: 
                    break
        else:
            if not self.monitor.paths:
                messagebox.showwarning("Setup Required", "Please add a folder in Settings before starting.")
                return
            self.monitor.start()
        self._update_stats()

    def scan_existing(self):
        if not self.monitor.paths:
            messagebox.showwarning("Setup Required", "Please add a folder in Settings first.")
            return
        
        if self.is_scanning: return

        self.is_scanning = True
        self.btn_scan.configure(state="disabled", text="SCANNING...")
        is_training = self.monitor.training_mode
        self.lbl_status.configure(text="SYSTEM STATUS: SCANNING IN PROGRESS...", text_color="#3498db")
        self.lbl_details.configure(text="Analyzing file integrity across monitored directories. Please wait.")
        
        initial_anomalies = self.db.get_anomaly_count()

        def run_scan():
            try:
                scanned, failed = self.monitor.scan_existing_files(training_mode=is_training)
                
                # Brief pause to let DB/UI catch up
                time.sleep(0.5)
                
                final_anomalies = self.db.get_anomaly_count()
                new_threats = final_anomalies - initial_anomalies
                
                msg = f"Scan Analysis Finished!\n\n" \
                      f"Total Files Scanned: {scanned}\n" \
                      f"Errors/Skipped: {failed}"
                
                if new_threats > 0:
                    msg += f"\n\n⚠️ THREATS DETECTED: {new_threats}\n" \
                           f"Action: Suspicious files have been moved to Quarantine.\n\n" \
                           f"Please review the 'Quarantine' tab for details."
                else:
                    msg += f"\n\n✅ Results: No security threats found."

                # Clear any real-time alerts that were bundled during scan to avoid double-popup
                while not self.alert_queue.empty():
                    try: self.alert_queue.get_nowait()
                    except Exception: break

                self.after(0, lambda: messagebox.showinfo("Scan Complete", msg))
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Scan Error", f"An error occurred during scan: {err}"))
            finally:
                self.after(0, self._scan_finished)

        threading.Thread(target=run_scan, daemon=True).start()

    def _scan_finished(self):
        self.is_scanning = False
        self.btn_scan.configure(state="normal", text="SCAN FOLDER")
        self._update_stats()

    def toggle_mode_seg(self, value):
        self.monitor.training_mode = (value == "Training")
        self._update_stats()

    def _update_stats_loop(self):
        self._update_stats()
        self.after(3000, self._update_stats_loop)

    def _update_stats(self):
        stats = self.db.get_statistics()
        self.card_events.configure(text=str(stats['total_events']))
        self.card_anomalies.configure(text=str(stats['total_anomalies']))
        self.card_samples.configure(text=str(stats['training_samples']))
        
        if self.monitor.active:
            mode = "TRAINING" if self.monitor.training_mode else "ACTIVE DEFENSE"
            self.lbl_status.configure(text=f"SYSTEM STATUS: {mode}", text_color="#2ecc71")
            self.lbl_details.configure(text=f"Monitoring: {' | '.join(self.monitor.paths)}")
            stop_text = "STOP TRAINING" if self.monitor.training_mode else "STOP PROTECTION"
            self.btn_toggle.configure(text=stop_text, fg_color="#e67e22")
        else:
            self.lbl_status.configure(text="SYSTEM STATUS: IDLE", text_color="white")
            self.lbl_details.configure(text="Ready to secure your files. Press START.")
            
            # Dynamic button text based on mode
            btn_text = "START TRAINING" if self.monitor.training_mode else "START PROTECTION"
            self.btn_toggle.configure(text=btn_text, fg_color="#2ecc71")

            # Safety fix: Reset scan button if system is idle
            if self.btn_scan.cget("text") == "SCANNING...":
                self.is_scanning = False
                self.btn_scan.configure(state="normal", text="SCAN FOLDER")

    def _poll_alerts(self):
        # Always empty the responder queue into our local queue
        try:
            while True:
                alert = alert_queue.get_nowait()
                self.alert_queue.put(alert)
        except queue.Empty:
            pass

        # STRICT CHECK: Only show popup if NOT currently scanning
        if not self.is_scanning:
            if not self.popup_active and not self.alert_queue.empty():
                self._show_next_alert()

        self.after(500, self._poll_alerts)

    def _show_next_alert(self):
        if self.is_scanning or self.alert_queue.empty(): return
        
        # Collect ALL pending alerts and clear the queue
        alerts = []
        while not self.alert_queue.empty():
            alerts.append(self.alert_queue.get())

        total = len(alerts)
        latest_alert = alerts[-1] # Show the most recent one
        
        if total == 1:
            msg = f"THREAT DETECTED!\n\nFile: {latest_alert['path']}\nReason: {latest_alert['reason']}"
        else:
            msg = f"SECURITY ALERT: MULTIPLE THREATS!\n\n" \
                  f"Total Anomalies Detected: {total}\n" \
                  f"Most Recent: {os.path.basename(latest_alert['path'])}\n\n" \
                  f"Please check the 'Live Events' or 'Quarantine' tab for details."

        self.popup_active = True
        messagebox.showwarning("Security Alert", msg)
        self.popup_active = False
