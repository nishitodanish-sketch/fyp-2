import math
import os
import hashlib
import stat
import time
from collections import Counter

# Categories for extensions
DOC_EXTENSIONS = {'.txt', '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.csv', '.rtf'}
IMG_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
EXECUTABLE_EXTENSIONS = {'.exe', '.msi', '.bat', '.sh', '.py', '.ps1', '.cmd', '.php', '.js'}
ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz'}
SYSTEM_EXTENSIONS = {'.sys', '.dll', '.ini', '.inf', '.reg'}

class FeatureExtractor:
    @staticmethod
    def calculate_entropy(data):
        if not data:
            return 0.0
        counter = Counter(data)
        len_data = len(data)
        entropy = -sum((count / len_data) * math.log2(count / len_data) for count in counter.values())
        return entropy / 8.0  # Normalized 0 to 1

    @staticmethod
    def get_byte_histogram(data, buckets=32):
        """Creates a normalized distribution of bytes into N buckets."""
        if not data:
            return [0.0] * buckets
        
        hist = [0] * 256
        for b in data:
            hist[b] += 1
        
        len_data = len(data)
        # Combine 256 bytes into N buckets
        chunk_size = 256 // buckets
        compressed_hist = []
        for i in range(0, 256, chunk_size):
            chunk_sum = sum(hist[i : i + chunk_size])
            compressed_hist.append(chunk_sum / len_data)
            
        return compressed_hist[:buckets]

    @staticmethod
    def extract_features_vector(file_path, prev_size=None, recent_event_count=0, global_event_count=0):
        """
        Extracts 50 features from a file.
        """
        features = []
        meta = {'size': 0, 'entropy': 0, 'extension': '', 'hash': '', 'permissions': 0}
        
        try:
            ext = os.path.splitext(file_path)[1].lower()
            meta['extension'] = ext
            
            # 1. Read file data
            data = b""
            if os.path.exists(file_path) and os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                meta['size'] = file_stat.st_size
                meta['permissions'] = file_stat.st_mode
                
                # Read first 1MB only for performance
                with open(file_path, 'rb') as f:
                    data = f.read(1024 * 1024)
                
                meta['hash'] = hashlib.sha256(data).hexdigest()
                meta['entropy'] = FeatureExtractor.calculate_entropy(data)

            # --- FEATURE GENERATION (Total 50) ---
            
            # [1-32] Byte Histogram
            features.extend(FeatureExtractor.get_byte_histogram(data, buckets=32))
            
            # [33] Normalized Size (Log scale)
            features.append(math.log10(meta['size'] + 1) / 10.0) 
            
            # [34] Entropy
            features.append(meta['entropy'])
            
            # [35] Filename length
            fname = os.path.basename(file_path)
            features.append(min(len(fname) / 100.0, 1.0))
            
            # [36] Filename digit ratio
            digits = sum(c.isdigit() for c in fname)
            features.append(digits / len(fname) if len(fname) > 0 else 0.0)
            
            # [37] Filename special char ratio
            special = sum(not c.isalnum() for c in fname)
            features.append(special / len(fname) if len(fname) > 0 else 0.0)
            
            # [38] Path depth
            depth = file_path.count(os.sep)
            features.append(min(depth / 20.0, 1.0))
            
            # [39-43] Extension Categories
            features.append(1.0 if ext in DOC_EXTENSIONS else 0.0)
            features.append(1.0 if ext in IMG_EXTENSIONS else 0.0)
            features.append(1.0 if ext in EXECUTABLE_EXTENSIONS else 0.0)
            features.append(1.0 if ext in SYSTEM_EXTENSIONS else 0.0)
            features.append(1.0 if ext in ARCHIVE_EXTENSIONS else 0.0)
            
            # [44] NULL byte ratio
            null_count = data.count(0)
            features.append(null_count / len(data) if len(data) > 0 else 0.0)
            
            # [45] Printable ASCII ratio
            printable = sum(32 <= b <= 126 for b in data)
            features.append(printable / len(data) if len(data) > 0 else 0.0)
            
            # [46] Size change ratio
            if prev_size is not None and prev_size > 0:
                diff = abs(meta['size'] - prev_size) / prev_size
                features.append(min(diff, 1.0))
            else:
                features.append(0.0)
                
            # [47] Modification frequency (Events per minute approx)
            features.append(min(recent_event_count / 20.0, 1.0))
            
            # [48] Global Event Frequency (Automation indicator - non-human speed)
            features.append(min(global_event_count / 10.0, 1.0))
            
            # [49] Day of Week
            dow = time.localtime().tm_wday
            features.append(dow / 6.0)
            
            # [50] Is Hidden (Windows style check)
            try:
                attrs = os.stat(file_path).st_file_attributes
                is_hidden = 1.0 if attrs & stat.FILE_ATTRIBUTE_HIDDEN else 0.0
            except Exception:
                # Fallback to filename-based hidden check if system attributes are inaccessible
                is_hidden = 1.0 if fname.startswith('.') else 0.0
            features.append(is_hidden)

            # Final safety check: ensure we have exactly 50
            if len(features) < 50:
                features.extend([0.0] * (50 - len(features)))
            return features[:50], meta

        except Exception as e:
            print(f"Error extracting features for {file_path}: {e}")
            return [0.0] * 50, meta
