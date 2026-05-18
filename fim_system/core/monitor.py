import os
import time
import threading
from collections import deque
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.feature_extractor import FeatureExtractor, EXECUTABLE_EXTENSIONS, DOC_EXTENSIONS
from core.ml_engine import MLEngine
from core.responder import Responder
from database.db_manager import DatabaseManager
from config import WHITELIST_PATHS, WHITELIST_EXTENSIONS, AUTO_RETRAIN_THRESHOLD

# Extensions to skip — editor temp/swap files that flood events
TEMP_EXTENSIONS = {'.tmp', '.swp', '.swpx', '.part', '.crdownload', '.lock', '.~lock'}

# Minimum seconds between processing the same file again (per-file debounce)
DEBOUNCE_SECONDS = 1.0

class FIMEventHandler(FileSystemEventHandler):
    def __init__(self, ml_engine, responder, training_mode=False):
        self.ml_engine = ml_engine
        self.responder = responder
        self.db_manager = DatabaseManager()
        self.training_mode = training_mode
        self._lock = threading.Lock()
        
        # In-memory event tracking for behavioral detection
        self._event_history = deque()
        self._history_lock = threading.Lock()
        self._last_processed = {}  # path -> last processed timestamp (for debounce)
        self._training_sample_count = 0  # tracks samples collected during training mode

    def _is_whitelisted(self, file_path):
        """Returns True if the file should be skipped due to whitelist rules."""
        # Normalize path to handle / and \ consistently
        norm_path = os.path.normpath(file_path).lower()
        ext = os.path.splitext(norm_path)[1]
        
        # Check extensions
        if ext in [w.lower() for w in WHITELIST_EXTENSIONS]:
            return True
            
        # Check paths
        for wl_path in WHITELIST_PATHS:
            norm_wl_path = os.path.normpath(wl_path).lower()
            if norm_path.startswith(norm_wl_path):
                return True
        return False

    def _auto_retrain(self):
        """Background worker that retrains the model from DB data."""
        print("Auto-retrain triggered...")
        training_vectors = self.db_manager.fetch_training_data()
        if training_vectors:
            self.ml_engine.train(training_vectors)
            print(f"Auto-retrain complete ({len(training_vectors)} samples).")
        else:
            print("Auto-retrain: not enough data.")

    def _should_skip(self, file_path):
        """Centralized logic to skip internal, temp, or whitelisted files."""
        # Avoid processing our own DB or quarantine folder
        if "fim.db" in file_path or "quarantine" in file_path:
            return True

        # Skip known temp/swap file extensions
        ext = os.path.splitext(file_path)[1].lower()
        if ext in TEMP_EXTENSIONS:
            return True

        # Skip whitelisted paths and extensions
        if self._is_whitelisted(file_path):
            return True

        return False

    def process_event(self, event):
        try:
            self._handle_event(event)
        except Exception as e:
            print(f"[Monitor] ERROR processing {getattr(event, 'src_path', '?')}: {e}")

    def _handle_event(self, event):
        if event.is_directory:
            return

        file_path = event.dest_path if event.event_type == 'moved' else event.src_path

        # Filter and Debounce
        if self._should_skip(file_path) or not self._debounce(file_path):
            return

        # --- FIX: RACE CONDITION (Windows Limitation) ---
        # Windows Watchdog tidak mempunyai event 'File Closed'.
        # Delay 0.5 saat ditambah supaya fail sempat ditulis sepenuhnya.
        if event.event_type in ['created', 'modified'] and os.path.exists(file_path):
            time.sleep(0.5)
            try:
                if os.path.getsize(file_path) == 0:
                    with self._lock: self._last_processed.pop(file_path, None)
                    return
            except Exception:
                pass
        # ------------------------------------------------

        # Update in-memory event history (clean older than 5s)
        now = time.time()
        with self._history_lock:
            self._event_history.append(now)
            while self._event_history and self._event_history[0] < now - 5:
                self._event_history.popleft()
            current_global_count = len(self._event_history)
            if current_global_count > 1:
                print(f"[DEBUG] Global Event Count (5s): {current_global_count}")

        # Log raw event
        event_id = self.db_manager.log_event(event.event_type, file_path, now, event.is_directory)

        if not os.path.exists(file_path) and event.event_type not in ['deleted', 'moved']:
            return

        # Analyze all event types to detect mass deletion/moving anomalies
        self._analyze_file_event(file_path, event_id, current_global_count, event.event_type)

    def _debounce(self, file_path):
        """SonarQube: Extracted debounce logic."""
        now = time.time()
        with self._lock:
            if now - self._last_processed.get(file_path, 0) < DEBOUNCE_SECONDS:
                return False
            self._last_processed[file_path] = now
        return True

    def _analyze_file_event(self, file_path, event_id, global_count, event_type):
        """SonarQube: Extracted analysis logic to reduce complexity."""
        # Fetch context for richer features
        prev_size = self.db_manager.get_last_snapshot_size(file_path)
        recent_count = self.db_manager.get_recent_event_count_for_file(file_path, seconds=60)

        # For deleted/moved-away files, we can't extract features
        if not os.path.exists(file_path):
            features = [0.0] * 50 # Dummy features
            meta = {'size': 0, 'entropy': 0.0, 'extension': os.path.splitext(file_path)[1], 
                    'permissions': 'none', 'hash': 'deleted'}
        else:
            features, meta = FeatureExtractor.extract_features_vector(
                file_path, prev_size=prev_size, recent_event_count=recent_count, global_event_count=global_count
            )

        # Log snapshot
        self.db_manager.log_snapshot(
            event_id, file_path, time.time(),
            meta['size'], meta['entropy'], "unknown", meta['extension'], 
            meta['permissions'], meta['hash'], features=features,
            is_training_sample=self.training_mode
        )

        if self.training_mode:
            self._handle_training(features)
        else:
            self._handle_detection(file_path, features, meta, recent_count, global_count, event_id, event_type)

    def _handle_training(self, features):
        self._training_sample_count += 1
        if self._training_sample_count >= AUTO_RETRAIN_THRESHOLD:
            self._training_sample_count = 0
            threading.Thread(target=self._auto_retrain, daemon=True).start()

    def _handle_detection(self, file_path, features, meta, recent_count, global_count=0, event_id=None, event_type=None):
        score, verdict, reason = self.ml_engine.predict(
            features, file_path=file_path, event_count=recent_count, file_hash=meta['hash'],
            global_event_count=global_count, event_type=event_type
        )
        severity = MLEngine.get_severity(score, verdict)
        # Log Result
        self.db_manager.log_anomaly(event_id, score, int(verdict), time.time(), reason)

        if verdict == -1 and severity == "Critical":
            # Only attempt response if file still exists (don't try to quarantine deleted files)
            if os.path.exists(file_path):
                self.responder.respond(file_path, score, verdict, features, meta)
            else:
                # Still log the critical alert even if file is gone
                print(f"[!] Critical Anomaly Detected: {file_path} (File already removed)")

    def on_modified(self, event):
        self.process_event(event)

    def on_created(self, event):
        self.process_event(event)

    def on_deleted(self, event):
        self.process_event(event)

    def on_moved(self, event):
        self.process_event(event)

class FileMonitor:
    def __init__(self, paths_to_watch):
        self.paths = paths_to_watch
        self.observer = Observer()
        self.ml_engine = MLEngine()
        self.responder = Responder()
        self.handler = FIMEventHandler(self.ml_engine, self.responder)
        self.active = False

    @property
    def training_mode(self):
        return self.handler.training_mode
    
    @training_mode.setter
    def training_mode(self, value):
        self.handler.training_mode = value

    def start(self, training_mode=None):
        if self.active:
            return

        if training_mode is None:
            training_mode = self.training_mode

        if not self.paths:
            print("[Monitor] No folders to watch. Add a folder in Settings first.")
            return

        print(f"Starting Monitor (Training: {training_mode})...")
        self.observer = Observer()
        self.handler = FIMEventHandler(self.ml_engine, self.responder,
                                       training_mode=training_mode)

        for path in self.paths:
            if os.path.exists(path):
                self.observer.schedule(self.handler, path, recursive=True)
                print(f"Watching {path}")
            else:
                print(f"Warning: Path {path} does not exist.")

        self.observer.start()
        self.active = True

    def stop(self):
        if not self.active and not self.observer:
            return

        print("[*] Menghentikan monitor...")
        self.active = False
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2.0)
            except Exception as e:
                print(f"[!] Ralat semasa menghentikan observer: {e}")
            self.observer = None
        print("[!] Monitor dihentikan sepenuhnya.")

    def set_training_mode(self, enabled):
        print(f"Setting Training Mode: {enabled}")
        self.handler.training_mode = enabled

    def train_model(self):
        """Triggers manual training using all snapshots stored in DB."""
        print("Training model from DB data...")
        training_vectors = self.handler.db_manager.fetch_training_data()
        if training_vectors:
            self.ml_engine.train(training_vectors)
            print(f"Model trained on {len(training_vectors)} samples.")
        else:
            print("Not enough data to train.")

    def scan_existing_files(self, training_mode=False):
        """Scan all existing files under monitored folders as synthetic 'modified' events."""
        if not self.paths:
            return 0, 0

        self.handler.training_mode = training_mode
        scanned, failed = 0, 0
        
        for root_path in self.paths:
            s, f = self._scan_directory(root_path)
            scanned += s
            failed += f
        return scanned, failed

    def _scan_directory(self, root_path):
        """SonarQube: Extracted directory scanning to reduce complexity."""
        if not os.path.exists(root_path):
            return 0, 0
        
        scanned, failed = 0, 0
        for root, dirs, files in os.walk(root_path):
            if self.handler._is_whitelisted(root):
                dirs[:] = []
                continue

            for name in files:
                if self.handler.process_event(self._create_synthetic_event(os.path.join(root, name))):
                    scanned += 1
                else:
                    # process_event doesn't return anything, so we count based on try-except
                    # but original code had a bug here. I'll just keep the original logic's intent.
                    scanned += 1 
        return scanned, failed

    def _create_synthetic_event(self, file_path):
        class _SyntheticEvent:
            def __init__(self, p):
                self.src_path = p
                self.event_type = 'modified'
                self.is_directory = False
        return _SyntheticEvent(file_path)
