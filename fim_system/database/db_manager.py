import sqlite3
import os
import time
import threading
import csv
from config import DB_PATH, BASE_DIR

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        self.db_path = DB_PATH
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize schema
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        conn = self.get_connection()
        try:
            conn.executescript(schema)
            conn.commit()
        finally:
            conn.close()
        self._migrate_schema()

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def clear_all_data(self):
        """Wipe all tables so the user can start fresh with a new folder."""
        conn = self.get_connection()
        try:
            conn.executescript('''
                DELETE FROM anomalies;
                DELETE FROM snapshots;
                DELETE FROM quarantine_log;
                DELETE FROM events;
                DELETE FROM known_files;
                DELETE FROM sqlite_sequence;
            ''')
            conn.commit()
        except Exception as e:
            print(f"DB Error clear_all_data: {e}")
        finally:
            conn.close()
        # Force re-init so the singleton picks up the fresh empty DB
        DatabaseManager._instance = None

    def log_event(self, event_type, file_path, timestamp, is_directory):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO events (event_type, file_path, timestamp, is_directory)
                VALUES (?, ?, ?, ?)
            ''', (event_type, file_path, timestamp, is_directory))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"DB Error log_event: {e}")
            return None
        finally:
            conn.close()

    def _migrate_schema(self):
        """Add new columns to existing DB without breaking old data."""
        conn = self.get_connection()
        try:
            conn.execute('ALTER TABLE snapshots ADD COLUMN features_json TEXT')
            conn.commit()
        except Exception:
            pass  # Column already exists
        try:
            conn.execute('ALTER TABLE snapshots ADD COLUMN is_training_sample INTEGER DEFAULT 0')
            conn.commit()
        except Exception:
            pass  # Column already exists
        finally:
            conn.close()

    def log_snapshot(self, event_id, file_path, timestamp, file_size, entropy, mime_type,
                     extension, permissions, sha256_hash, features=None, is_training_sample=False):
        import json
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            features_json = json.dumps(features) if features is not None else None
            cursor.execute('''
                INSERT INTO snapshots (
                    event_id, file_path, timestamp, file_size, entropy, mime_type,
                    extension, permissions, sha256_hash, features_json, is_training_sample
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_id, file_path, timestamp, file_size, entropy, mime_type,
                extension, permissions, sha256_hash, features_json,
                1 if is_training_sample else 0
            ))
            conn.commit()
        except Exception as e:
            print(f"DB Error log_snapshot: {e}")
        finally:
            conn.close()
            
    def get_recent_events(self, limit=50):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, event_type, file_path, timestamp, is_directory 
                FROM events ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        finally:
            conn.close()

    def log_anomaly(self, event_id, score, verdict, timestamp, details):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO anomalies (event_id, anomaly_score, verdict, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_id, score, verdict, timestamp, details))
            conn.commit()
        finally:
            conn.close()

    def log_quarantine(self, original_path, quarantine_path, timestamp, reason):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO quarantine_log (original_path, quarantine_path, timestamp, reason)
                VALUES (?, ?, ?, ?)
            ''', (original_path, quarantine_path, timestamp, reason))
            conn.commit()
        finally:
            conn.close()
            
    def get_event_count(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) FROM events')
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_anomaly_count(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) FROM anomalies WHERE verdict = -1')
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_training_sample_count(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) FROM snapshots WHERE features_json IS NOT NULL')
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_quarantine_log(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, original_path, quarantine_path, timestamp, reason, restored
                FROM quarantine_log ORDER BY timestamp DESC
            ''')
            return cursor.fetchall()
        finally:
            conn.close()

    def restore_quarantine_entry(self, entry_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE quarantine_log SET restored = 1 WHERE id = ?', (entry_id,))
            conn.commit()
        finally:
            conn.close()

    def get_last_snapshot_size(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT file_size FROM snapshots
                WHERE file_path = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (file_path,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def get_recent_event_count_for_file(self, file_path, seconds=60):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            since = time.time() - seconds
            cursor.execute('''
                SELECT COUNT(*) FROM events
                WHERE file_path = ? AND timestamp > ?
            ''', (file_path, since))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_global_recent_event_count(self, seconds=10):
        """Counts all file events across the system in the last N seconds."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            since = time.time() - seconds
            cursor.execute('SELECT COUNT(*) FROM events WHERE timestamp > ?', (since,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_events_over_time(self, buckets=10, bucket_seconds=30):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = time.time()
            result = []
            for i in range(buckets - 1, -1, -1):
                bucket_start = now - (i + 1) * bucket_seconds
                bucket_end = now - i * bucket_seconds
                cursor.execute('''
                    SELECT COUNT(*) FROM events
                    WHERE timestamp >= ? AND timestamp < ?
                ''', (bucket_start, bucket_end))
                total = cursor.fetchone()[0]
                cursor.execute('''
                    SELECT COUNT(*) FROM anomalies
                    WHERE timestamp >= ? AND timestamp < ? AND verdict = -1
                ''', (bucket_start, bucket_end))
                anoms = cursor.fetchone()[0]
                result.append((max(total - anoms, 0), anoms))
            return result
        finally:
            conn.close()

    def get_recent_deleted_file(self, filename, seconds=2.0):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            since = time.time() - seconds
            cursor.execute('''
                SELECT file_path FROM events
                WHERE event_type = 'deleted' AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (since,))
            rows = cursor.fetchall()
            for r in rows:
                if os.path.basename(r[0]) == filename:
                    return r[0]
            return None
        finally:
            conn.close()

    def get_recent_events_with_verdict(self, limit=50):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT e.id, e.event_type, e.file_path, e.timestamp,
                       COALESCE(a.verdict, 1) as verdict,
                       COALESCE(a.anomaly_score, 0.0) as score,
                       COALESCE(s.is_training_sample, 0) as is_training,
                       COALESCE(a.details, 'Normal') as reason
                FROM events e
                LEFT JOIN anomalies a ON a.event_id = e.id
                LEFT JOIN snapshots s ON s.event_id = e.id
                ORDER BY e.id ASC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        finally:
            conn.close()

    def fetch_training_data(self):
        import json
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT features_json
                FROM snapshots
                WHERE features_json IS NOT NULL
                  AND is_training_sample = 1
            ''')
            rows = cursor.fetchall()
            vectors = []
            for (fj,) in rows:
                try:
                    vec = json.loads(fj)
                    if isinstance(vec, list) and (len(vec) == 7 or len(vec) == 50):
                        vectors.append(vec)
                except Exception:
                    pass
            return vectors
        except Exception:
            return []
        finally:
            conn.close()

    def export_events_csv(self, output_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT e.id, e.event_type, e.file_path, e.timestamp,
                       COALESCE(a.verdict, 1) as verdict,
                       COALESCE(a.anomaly_score, 0.0) as anomaly_score,
                       CASE 
                           WHEN s.features_json IS NOT NULL THEN 'Sample Data'
                           ELSE COALESCE(a.details, '') 
                       END as details
                FROM events e
                LEFT JOIN anomalies a ON a.event_id = e.id
                LEFT JOIN snapshots s ON s.event_id = e.id
                ORDER BY e.timestamp DESC
            ''')
            rows = cursor.fetchall()
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'event_type', 'file_path', 'timestamp', 'verdict', 'anomaly_score', 'details'])
                writer.writerows(rows)
            return len(rows)
        finally:
            conn.close()

    def export_quarantine_csv(self, output_path):
        rows = self.get_quarantine_log()
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'original_path', 'quarantine_path', 'timestamp', 'reason', 'restored'])
            writer.writerows(rows)
        return len(rows)

    def get_evaluation_summary(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) FROM events')
            total_events = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM anomalies')
            total_scored = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM anomalies WHERE verdict = -1')
            total_anomalies = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM snapshots WHERE features_json IS NOT NULL')
            training_samples = cursor.fetchone()[0]

            cursor.execute('''
                SELECT AVG(a.timestamp - e.timestamp)
                FROM anomalies a
                JOIN events e ON e.id = a.event_id
            ''')
            avg_response = cursor.fetchone()[0]
            avg_response = float(avg_response) if avg_response is not None else 0.0

            anomaly_rate = (total_anomalies / total_scored) if total_scored else 0.0
            return {
                'total_events': total_events,
                'total_scored_events': total_scored,
                'total_anomalies': total_anomalies,
                'anomaly_rate': anomaly_rate,
                'avg_detection_latency_sec': avg_response,
                'training_samples': training_samples,
            }
        finally:
            conn.close()

    def get_all_scanned_files(self):
        """Returns a list of unique file paths ever seen, with their latest metadata and status."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT s.file_path, MAX(s.timestamp) as last_seen, s.file_size, s.entropy, s.extension, 
                       COALESCE(a.verdict, 1) as verdict,
                       COALESCE(a.anomaly_score, 0.0) as score
                FROM snapshots s
                LEFT JOIN anomalies a ON a.event_id = s.event_id
                GROUP BY s.file_path
                ORDER BY last_seen DESC
            ''')
            return cursor.fetchall()
        finally:
            conn.close()
    def get_statistics(self):
        """Alias for get_evaluation_summary for dashboard compatibility."""
        return self.get_evaluation_summary()

    def add_to_baseline(self, file_path, sha256_hash):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO known_files (file_path, sha256_hash, timestamp)
                VALUES (?, ?, ?)
            ''', (file_path, sha256_hash, time.time()))
            conn.commit()
        except Exception as e:
            print(f"DB Error add_to_baseline: {e}")
        finally:
            conn.close()

    def is_file_known(self, file_path, sha256_hash):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # We check if this EXACT file path and hash exists in our 'Trusted' list
            cursor.execute('''
                SELECT id FROM known_files 
                WHERE file_path = ? AND sha256_hash = ?
            ''', (file_path, sha256_hash))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"DB Error is_file_known: {e}")
            return False
        finally:
            conn.close()
