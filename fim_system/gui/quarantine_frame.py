import customtkinter as ctk
from tkinter import ttk, messagebox
import os
import datetime
from config import QUARANTINE_KEY
from database.db_manager import DatabaseManager

class QuarantineFrame(ctk.CTkFrame):
    def __init__(self, parent, monitor):
        super().__init__(parent, fg_color="transparent")
        self.monitor = monitor
        self.db = DatabaseManager()

        self.header = ctk.CTkLabel(self, text="File Quarantine vault", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        self.header.pack(pady=(0, 10), anchor="w")

        # Action Buttons (Pack at bottom first to ensure visibility)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side='bottom', fill="x", pady=10)

        self.btn_refresh = ctk.CTkButton(btn_frame, text="REFRESH", width=100, command=self.load_files)
        self.btn_refresh.pack(side='left', padx=5)

        self.btn_restore = ctk.CTkButton(btn_frame, text="RESTORE SELECTED", fg_color="#2ecc71", hover_color="#27ae60", command=self.restore_selected)
        self.btn_restore.pack(side='left', padx=5)

        self.btn_restore_all = ctk.CTkButton(btn_frame, text="RESTORE ALL", fg_color="#34495e", command=self.restore_all)
        self.btn_restore_all.pack(side='left', padx=5)

        # Container for Treeview (Takes remaining space in the middle)
        tree_container = ctk.CTkFrame(self)
        tree_container.pack(side='top', fill="both", expand=True, pady=10)

        columns = ('id', 'original', 'quarantined', 'time', 'reason')
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', selectmode='extended')
        self.tree.heading('id', text='ID')
        self.tree.heading('original', text='Original Path')
        self.tree.heading('quarantined', text='Quarantine File')
        self.tree.heading('time', text='Time')
        self.tree.heading('reason', text='Reason')

        self.tree.column('id', width=40)
        self.tree.column('original', width=260)
        self.tree.column('quarantined', width=200)
        self.tree.column('time', width=130)
        self.tree.column('reason', width=200)

        scrollbar = ctk.CTkScrollbar(tree_container, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def on_show(self):
        self.load_files()

    def load_files(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = self.db.get_quarantine_log()
        for row in rows:
            entry_id, original_path, quarantine_path, timestamp, reason, restored = row
            if restored:
                continue
            ts = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            qname = os.path.basename(quarantine_path)
            self.tree.insert('', 'end', iid=str(entry_id),
                             values=(entry_id, original_path, qname, ts, reason or ''))

    def restore_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        try:
            count = 0
            errors = []
            for item_id in selected:
                success, error_msg = self._do_restore(item_id)
                if success:
                    count += 1
                else:
                    errors.append(error_msg)
            
            if errors:
                messagebox.showerror("Error", "Failed to restore some files:\n" + "\n".join(errors[:5]))
            
            if count > 0:
                messagebox.showinfo("Success", f"Restored {count} file(s).")
            
            self.load_files()
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def restore_all(self):
        all_items = self.tree.get_children()
        if not all_items: return
        if not messagebox.askyesno("Confirm", f"Restore all {len(all_items)} files?"): return

        count = 0
        errors = []
        for item_id in all_items:
            success, error_msg = self._do_restore(item_id)
            if success:
                count += 1
            else:
                errors.append(error_msg)
        
        if errors:
            messagebox.showerror("Error", "Failed to restore some files:\n" + "\n".join(errors[:5]))
            
        if count > 0:
            messagebox.showinfo("Success", f"Restored {count} file(s).")
        
        self.load_files()

    def _do_restore(self, item_id):
        try:
            entry_id = int(item_id)
            rows = self.db.get_quarantine_log()
            target = next((r for r in rows if r[0] == entry_id), None)
            if not target: return False, "Entry not found in database"
            _, original_path, quarantine_path, _, _, _ = target
            
            if not os.path.exists(quarantine_path): 
                return False, f"Quarantine file missing: {os.path.basename(quarantine_path)}"
            
            # Check if target directory is writable
            parent_dir = os.path.dirname(original_path)
            if parent_dir and not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                except Exception as e:
                    return False, f"Cannot create directory {parent_dir}: {e}"
            
            # Decrypt the file safely
            try:
                os.chmod(quarantine_path, 0o600)
                with open(quarantine_path, 'rb') as f:
                    data = bytearray(f.read())
                
                # Check if already decrypted (very basic check)
                # In a real app we'd use a more robust way, but here we just XOR
                for i in range(len(data)):
                    data[i] ^= QUARANTINE_KEY
                
                # Try to move first, if move fails, we don't commit the decryption
                # Actually, shutil.move might fail if destination exists and is locked.
                if os.path.exists(original_path):
                    try:
                        os.remove(original_path)
                    except Exception as e:
                        return False, f"Original file is locked/protected: {e}"

                with open(original_path, 'wb') as f:
                    f.write(data)
                
                os.remove(quarantine_path)
                self.db.restore_quarantine_entry(entry_id)
                return True, None
            except Exception as e:
                return False, f"Permission or Disk Error: {e}"

        except Exception as e:
            return False, str(e)

