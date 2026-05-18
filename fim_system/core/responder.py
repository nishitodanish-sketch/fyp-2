import os
import shutil
import time
import queue
import subprocess
import getpass
import getpass
from config import QUARANTINE_DIR, QUARANTINE_KEY
from database.db_manager import DatabaseManager

# Thread-safe queue for pushing alerts to the GUI
alert_queue = queue.Queue()

class Responder:
    def __init__(self):
        self.db_manager = DatabaseManager()
        if not os.path.exists(QUARANTINE_DIR):
            os.makedirs(QUARANTINE_DIR)
        
        # Secure the folder immediately on startup
        self._secure_quarantine_folder()

    def _secure_quarantine_folder(self):
        """
        Uses Windows icacls to restrict the quarantine folder so ONLY the 
        current user and SYSTEM can access it. Others (including hackers) are blocked.
        """
        try:
            current_user = getpass.getuser()
            folder = os.path.abspath(QUARANTINE_DIR)
            
            # 1. Reset/Disable inheritance so it doesn't get permissions from parent folder
            subprocess.run(['icacls', folder, '/inheritance:r'], capture_output=True)
            
            # 2. Grant Full Control only to current user and SYSTEM
            subprocess.run(['icacls', folder, '/grant:r', f'{current_user}:(OI)(CI)F'], capture_output=True)
            subprocess.run(['icacls', folder, '/grant:r', f'SYSTEM:(OI)(CI)F'], capture_output=True)
            
            # 3. Remove access for 'Everyone' and 'Users' explicitly just in case
            subprocess.run(['icacls', folder, '/remove', 'Everyone'], capture_output=True)
            subprocess.run(['icacls', folder, '/remove', 'Users'], capture_output=True)
            
            # 4. Make folder Hidden + System via attrib
            subprocess.run(['attrib', '+h', '+s', folder], capture_output=True)
            
            print(f"[Security] Quarantine folder '{folder}' locked and hidden.")
        except Exception as e:
            print(f"[Security] Failed to lock quarantine folder: {e}")

    def _xor_cipher(self, file_path):
        """ Scrambles/Unscrambles file content using XOR with a secret key. """
        try:
            with open(file_path, 'rb') as f:
                data = bytearray(f.read())
            
            for i in range(len(data)):
                data[i] ^= QUARANTINE_KEY
            
            with open(file_path, 'wb') as f:
                f.write(data)
        except Exception as e:
            print(f"XOR Cipher Error on {file_path}: {e}")

    def quarantine_file(self, file_path, reason="Anomaly Detected"):
        """
        Moves the file to the quarantine directory and logs the action.
        """
        try:
            if not os.path.exists(file_path):
                print(f"File {file_path} not found for quarantine.")
                return

            filename = os.path.basename(file_path)
            # Create a unique name to prevent overwrites AND mask the extension
            timestamp_str = str(int(time.time()))
            quarantine_name = f"{timestamp_str}_{filename}.locked"
            quarantine_path = os.path.join(QUARANTINE_DIR, quarantine_name)

            # Move the file
            shutil.move(file_path, quarantine_path)
            
            # Neutralize the file via Encryption (XOR)
            self._xor_cipher(quarantine_path)
            
            # Lock permissions (Read-only for owner, nothing for others)
            os.chmod(quarantine_path, 0o400) # Read only for owner
            
            # Log to DB
            self.db_manager.log_quarantine(file_path, quarantine_path, time.time(), reason)
            print(f"Quarantined {file_path} to {quarantine_path}")
            
        except Exception as e:
            print(f"Error quarantining file {file_path}: {e}")

    def respond(self, file_path, anomaly_score, verdict, feature_vector, metadata):
        """
        Central response logic.
        """
        if verdict == -1:
            print(f"Responding to THREAT in {file_path} (Score: {anomaly_score})")
            reason = f"ML Anomaly Score: {anomaly_score:.4f}"
            self.quarantine_file(file_path, reason)
            # Push a popup alert to the GUI via the thread-safe queue
            alert_queue.put({
                'path': file_path,
                'reason': reason
            })
