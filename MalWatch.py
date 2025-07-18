#!/usr/bin/env python3
"""
Malware File Monitor - Cross-platform file tracking tool for malware analysis
Monitors file system changes and preserves suspicious files with metadata
"""

import os
import sys
import time
import json
import hashlib
import shutil
import argparse
import threading
import platform
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import math

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: watchdog library required. Install with: pip install watchdog")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("WARNING: psutil not available. Process attribution will be limited.")
    psutil = None

# Try to import enhanced analyzer
try:
    # First try to import numpy and sklearn
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.preprocessing import StandardScaler
    
    # If successful, enable enhanced mode
    ENHANCED_ANALYSIS = True
    
    class EnhancedFileAnalyzer:
        """Simplified enhanced analyzer embedded in main script"""
        
        def __init__(self):
            self.feature_scaler = StandardScaler()
        
        def calculate_chi_squared(self, data):
            """Calculate chi-squared test for randomness"""
            if len(data) < 256:
                return 0
            
            expected = len(data) / 256
            observed = [0] * 256
            for byte in data:
                observed[byte] += 1
            
            chi_squared = sum((obs - expected) ** 2 / expected for obs in observed)
            return chi_squared
        
        def analyze_byte_patterns(self, data):
            """Analyze byte patterns for anomalies"""
            if not data:
                return {}
            
            # Calculate byte frequency variance
            byte_counts = [0] * 256
            for byte in data:
                byte_counts[byte] += 1
            
            total_bytes = len(data)
            frequencies = [count / total_bytes for count in byte_counts]
            
            return {
                'byte_variance': np.var(frequencies),
                'unique_bytes': sum(1 for count in byte_counts if count > 0),
                'most_common_byte_freq': max(frequencies)
            }
        
        def comprehensive_analysis(self, filepath):
            """Enhanced analysis with statistical methods"""
            try:
                with open(filepath, 'rb') as f:
                    data = f.read(8192)  # Read first 8KB
                
                if not data:
                    return {'suspicion_score': 0, 'reasons': [], 'enhanced': False}
                
                # Calculate advanced entropy
                entropy = self.calculate_entropy(data)
                chi_squared = self.calculate_chi_squared(data)
                byte_patterns = self.analyze_byte_patterns(data)
                
                # Enhanced scoring
                suspicion_score = 0
                reasons = []
                
                # File extension and path scoring (from original analyzer)
                file_ext = Path(filepath).suffix.lower()
                if file_ext in {'.exe', '.dll', '.scr', '.bat', '.cmd', '.vbs', '.ps1'}:
                    suspicion_score += 30
                    reasons.append(f"Suspicious extension: {file_ext}")
                
                # Enhanced entropy analysis
                if entropy > 7.5:
                    suspicion_score += 35
                    reasons.append(f"Very high entropy: {entropy:.2f}")
                elif entropy > 7.0:
                    suspicion_score += 25
                    reasons.append(f"High entropy: {entropy:.2f}")
                
                # Chi-squared randomness test
                if chi_squared > 400:
                    suspicion_score += 30
                    reasons.append(f"High randomness (chi²: {chi_squared:.1f})")
                elif chi_squared > 300:
                    suspicion_score += 20
                    reasons.append(f"Moderate randomness (chi²: {chi_squared:.1f})")
                
                # Byte pattern analysis
                if byte_patterns['byte_variance'] < 0.001:
                    suspicion_score += 25
                    reasons.append("Low byte variance (possible encryption)")
                
                if byte_patterns['unique_bytes'] < 100:
                    suspicion_score += 15
                    reasons.append(f"Low byte diversity: {byte_patterns['unique_bytes']}")
                
                # File size analysis
                file_size = len(data)
                if file_ext in {'.exe', '.dll'} and file_size < 30000:
                    suspicion_score += 20
                    reasons.append("Small executable (possible dropper)")
                
                # Path analysis
                if any(suspicious_path in filepath.lower() for suspicious_path in ['tmp', 'temp', 'appdata']):
                    suspicion_score += 25
                    reasons.append("Suspicious file path")
                
                return {
                    'suspicion_score': suspicion_score,
                    'reasons': reasons,
                    'entropy': entropy,
                    'chi_squared': chi_squared,
                    'byte_variance': byte_patterns['byte_variance'],
                    'unique_bytes': byte_patterns['unique_bytes'],
                    'enhanced': True,
                    'file_size': file_size,
                    'file_extension': file_ext
                }
                
            except Exception as e:
                return {'suspicion_score': 0, 'reasons': [], 'error': str(e), 'enhanced': False}
        
        def calculate_entropy(self, data):
            """Calculate Shannon entropy"""
            if not data:
                return 0
            
            byte_counts = [0] * 256
            for byte in data:
                byte_counts[byte] += 1
            
            entropy = 0
            total = len(data)
            for count in byte_counts:
                if count > 0:
                    p = count / total
                    entropy -= p * math.log2(p)
            
            return entropy
    
    print("INFO: Enhanced statistical analyzer enabled")
    
except ImportError as e:
    ENHANCED_ANALYSIS = False
    print(f"INFO: Enhanced ML analyzer not available ({e}). Using basic analysis.")

class FileAnalyzer:
    """Analyzes files for malware-like characteristics"""
    
    SUSPICIOUS_EXTENSIONS = {
        '.exe', '.dll', '.scr', '.bat', '.cmd', '.pif', '.com',
        '.vbs', '.js', '.jar', '.ps1', '.msi', '.reg', '.lnk'
    }
    
    SUSPICIOUS_PATHS = {
        'windows': [
            r'%TEMP%', r'%APPDATA%', r'%LOCALAPPDATA%',
            r'%USERPROFILE%\Desktop', r'%USERPROFILE%\Documents',
            r'%PROGRAMDATA%', r'%WINDIR%\Temp',
            r'%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu'
        ],
        'linux': [
            '/tmp', '/var/tmp', '/dev/shm',
            '/home/*/Desktop', '/home/*/Downloads',
            '/usr/local/bin', '/opt'
        ],
        'darwin': [
            '/tmp', '/var/tmp', '/Users/*/Desktop',
            '/Users/*/Downloads', '/Applications',
            '/Library/LaunchAgents', '/Library/LaunchDaemons'
        ]
    }
    
    @staticmethod
    def calculate_entropy(data):
        """Calculate Shannon entropy of data"""
        if not data:
            return 0
        
        entropy = 0
        for x in range(256):
            p_x = float(data.count(bytes([x]))) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy
    
    @staticmethod
    def get_file_hash(filepath, max_size=50*1024*1024):
        """Calculate SHA256 and MD5 hashes of file (with size limit for performance)"""
        try:
            file_size = os.path.getsize(filepath)
            
            # For very large files, only hash the first portion
            if file_size > max_size:
                with open(filepath, 'rb') as f:
                    data = f.read(max_size)
                    sha256_hash = hashlib.sha256(data)
                    md5_hash = hashlib.md5(data)
                    
                    return {
                        'sha256': sha256_hash.hexdigest(),
                        'md5': md5_hash.hexdigest(),
                        'partial_hash': True,
                        'hashed_bytes': len(data)
                    }
            
            # For smaller files, hash the entire file
            sha256_hash = hashlib.sha256()
            md5_hash = hashlib.md5()
            
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
                    md5_hash.update(chunk)
            
            return {
                'sha256': sha256_hash.hexdigest(),
                'md5': md5_hash.hexdigest(),
                'partial_hash': False,
                'hashed_bytes': file_size
            }
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_file(self, filepath):
        """Analyze file for suspicious characteristics"""
        try:
            stat = os.stat(filepath)
            file_ext = Path(filepath).suffix.lower()
            
            # Read file for entropy calculation
            entropy = 0
            magic_bytes = b''
            try:
                with open(filepath, 'rb') as f:
                    data = f.read(8192)  # Read first 8KB for analysis
                    if data:
                        entropy = self.calculate_entropy(data)
                        magic_bytes = data[:16]
            except:
                pass
            
            # Calculate suspicion score
            suspicion_score = 0
            reasons = []
            
            # Extension check
            if file_ext in self.SUSPICIOUS_EXTENSIONS:
                suspicion_score += 30
                reasons.append(f"Suspicious extension: {file_ext}")
            
            # High entropy (likely packed/encrypted)
            if entropy > 7.0:
                suspicion_score += 25
                reasons.append(f"High entropy: {entropy:.2f}")
            
            # Small executable files (droppers)
            if file_ext in {'.exe', '.dll'} and stat.st_size < 50000:
                suspicion_score += 20
                reasons.append("Small executable")
            
            # Very large files
            if stat.st_size > 50 * 1024 * 1024:  # 50MB
                suspicion_score += 15
                reasons.append("Large file size")
            
            # Path-based scoring
            current_platform = platform.system().lower()
            if current_platform in self.SUSPICIOUS_PATHS:
                for suspicious_path in self.SUSPICIOUS_PATHS[current_platform]:
                    if suspicious_path.replace('%', '').replace('*', '') in filepath:
                        suspicion_score += 25
                        reasons.append(f"Suspicious path: {suspicious_path}")
                        break
            
            return {
                'suspicion_score': suspicion_score,
                'reasons': reasons,
                'entropy': entropy,
                'magic_bytes': magic_bytes.hex() if magic_bytes else '',
                'file_size': stat.st_size,
                'file_extension': file_ext
            }
            
        except Exception as e:
            return {'error': str(e)}

class MalwareFileHandler(FileSystemEventHandler):
    """Handles file system events and filters for suspicious files"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.analyzer = FileAnalyzer()
        
        # Use enhanced analyzer if available and ML mode is enabled
        if ENHANCED_ANALYSIS and monitor.ml_mode:
            self.enhanced_analyzer = EnhancedFileAnalyzer()
            if monitor.verbose:
                print("Enhanced statistical analyzer loaded")
        else:
            self.enhanced_analyzer = None
            
        self.processed_files = set()
        self.lock = threading.Lock()
    
    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path, 'created')
    
    def on_modified(self, event):
        if not event.is_directory:
            self.process_file(event.src_path, 'modified')
    
    def on_moved(self, event):
        if not event.is_directory:
            self.process_file(event.dest_path, 'moved')
    
    def process_file(self, filepath, event_type):
        """Process and analyze a file for suspicious characteristics"""
        try:
            # Avoid processing the same file multiple times rapidly
            with self.lock:
                file_key = f"{filepath}:{event_type}:{int(time.time())}"
                if file_key in self.processed_files:
                    return
                self.processed_files.add(file_key)
            
            # Clean up old entries to prevent memory leaks
            if len(self.processed_files) > 10000:
                self.processed_files.clear()
            
            if not os.path.exists(filepath):
                return
            
            # Skip our own output directory
            if str(self.monitor.output_dir) in filepath:
                return
            
            # Analyze file
            if self.enhanced_analyzer and self.monitor.ml_mode:
                # Use enhanced ML analysis
                analysis = self.enhanced_analyzer.comprehensive_analysis(filepath)
            else:
                # Use basic rule-based analysis
                analysis = self.analyzer.analyze_file(filepath)
            
            # Apply filtering
            if not self.monitor.ml_mode:
                # Non-ML mode: use rule-based filtering
                if analysis.get('suspicion_score', 0) < self.monitor.min_suspicion_score:
                    return
            
            # Add file size limits for very large files to reduce noise
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            if file_size > 10 * 1024 * 1024:  # 10MB
                # For large files, be more selective about preservation
                if analysis.get('suspicion_score', 0) < self.monitor.preserve_threshold + 10:
                    if self.monitor.verbose:
                        print(f"Large file skipped (size: {file_size/1024/1024:.1f}MB, score: {analysis.get('suspicion_score', 0)})")
                    return
            
            # Get file metadata
            metadata = self.get_file_metadata(filepath, event_type, analysis)
            
            # Log the event
            self.monitor.log_event(filepath, metadata)
            
            # Preserve the file if it's suspicious enough
            if analysis.get('suspicion_score', 0) >= self.monitor.preserve_threshold:
                self.monitor.preserve_file(filepath, metadata)
            
        except Exception as e:
            if self.monitor.verbose:
                print(f"Error processing {filepath}: {e}")
    
    def get_file_metadata(self, filepath, event_type, analysis):
        """Collect comprehensive metadata about the file"""
        metadata = {
            'filepath': filepath,
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis
        }
        
        try:
            stat = os.stat(filepath)
            metadata.update({
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:]
            })
        except Exception as e:
            metadata['stat_error'] = str(e)
        
        # Get file hashes
        hashes = self.analyzer.get_file_hash(filepath)
        metadata['hashes'] = hashes
        
        # Try to get process attribution
        if psutil:
            try:
                # This is a simplified approach - in practice, you'd want
                # more sophisticated process tracking
                metadata['system_info'] = {
                    'platform': platform.system(),
                    'python_version': platform.python_version(),
                    'cpu_count': psutil.cpu_count(),
                    'memory_total': psutil.virtual_memory().total
                }
            except:
                pass
        
        return metadata

class MalwareMonitor:
    """Main monitoring class"""
    
    def __init__(self, output_dir="./malware_cache", verbose=False, ml_mode=True,
                 min_suspicion_score=20, preserve_threshold=40):
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.ml_mode = ml_mode
        self.min_suspicion_score = min_suspicion_score
        self.preserve_threshold = preserve_threshold
        
        # Create output directory structure
        self.setup_output_directory()
        
        # Initialize components
        self.observer = Observer()
        self.handler = MalwareFileHandler(self)
        self.event_log = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Session directory
        self.session_dir = self.output_dir / datetime.now().strftime("%Y-%m-%d") / f"session_{self.session_id}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Preserved files directory
        self.preserved_dir = self.session_dir / "preserved_files"
        self.preserved_dir.mkdir(exist_ok=True)
        
        print(f"Session directory: {self.session_dir}")
        if self.verbose:
            print(f"ML mode: {'enabled' if self.ml_mode else 'disabled'}")
            print(f"Minimum suspicion score: {self.min_suspicion_score}")
            print(f"Preservation threshold: {self.preserve_threshold}")
    
    def setup_output_directory(self):
        """Create the output directory structure"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create README
        readme_path = self.output_dir / "README.md"
        if not readme_path.exists():
            with open(readme_path, 'w') as f:
                f.write("""# Malware File Monitor Cache

This directory contains files and metadata captured by the malware monitoring tool.

## Structure:
- `YYYY-MM-DD/` - Daily directories
  - `session_YYYYMMDD_HHMMSS/` - Individual monitoring sessions
    - `preserved_files/` - Suspicious files that were preserved
    - `events.json` - Log of all file system events
    - `metadata.json` - Session metadata

## Files:
- Original filename is preserved with timestamp prefix
- SHA256 hashes are used for deduplication
- Metadata includes analysis results and system information
""")
    
    def add_watch_path(self, path):
        """Add a path to monitor"""
        if os.path.exists(path):
            self.observer.schedule(self.handler, path, recursive=True)
            if self.verbose:
                print(f"Monitoring: {path}")
        else:
            print(f"WARNING: Path does not exist: {path}")
    
    def log_event(self, filepath, metadata):
        """Log a file system event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'filepath': filepath,
            'metadata': metadata
        }
        
        self.event_log.append(event)
        
        if self.verbose:
            score = metadata.get('analysis', {}).get('suspicion_score', 0)
            print(f"[{event['timestamp']}] {filepath} (score: {score})")
            
            reasons = metadata.get('analysis', {}).get('reasons', [])
            if reasons:
                for reason in reasons:
                    print(f"  - {reason}")
    
    def preserve_file(self, filepath, metadata):
        """Preserve a suspicious file"""
        try:
            # Create safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = Path(filepath).name
            safe_name = f"{timestamp}_{original_name}"
            
            # Check for duplicates using hash
            file_hash = metadata.get('hashes', {}).get('sha256', '')
            if file_hash:
                # Check if we already have this file
                existing_files = list(self.preserved_dir.glob(f"*{file_hash[:8]}*"))
                if existing_files:
                    if self.verbose:
                        print(f"Duplicate file skipped (hash: {file_hash[:8]}...) - already preserved as {existing_files[0].name}")
                    return
                
                # Include hash in filename
                safe_name = f"{timestamp}_{file_hash[:8]}_{original_name}"
            
            dest_path = self.preserved_dir / safe_name
            
            # Copy the file
            shutil.copy2(filepath, dest_path)
            
            # Save metadata
            metadata_path = dest_path.with_suffix(dest_path.suffix + '.meta.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"PRESERVED: {filepath} -> {dest_path}")
            
        except Exception as e:
            print(f"ERROR preserving {filepath}: {e}")
    
    def save_session_data(self):
        """Save session data to disk"""
        try:
            # Save events log
            events_path = self.session_dir / "events.json"
            with open(events_path, 'w') as f:
                json.dump(self.event_log, f, indent=2)
            
            # Save session metadata
            metadata_path = self.session_dir / "metadata.json"
            session_metadata = {
                'session_id': self.session_id,
                'start_time': datetime.now().isoformat(),
                'platform': platform.system(),
                'python_version': platform.python_version(),
                'ml_mode': self.ml_mode,
                'min_suspicion_score': self.min_suspicion_score,
                'preserve_threshold': self.preserve_threshold,
                'total_events': len(self.event_log),
                'preserved_files': len(list(self.preserved_dir.glob("*"))) // 2  # Divide by 2 for .meta files
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(session_metadata, f, indent=2)
                
        except Exception as e:
            print(f"ERROR saving session data: {e}")
    
    def start_monitoring(self, paths=None):
        """Start monitoring file system"""
        if paths is None:
            # Default paths based on platform
            system = platform.system().lower()
            if system == 'windows':
                paths = [
                    os.path.expandvars(r'%TEMP%'),
                    os.path.expandvars(r'%APPDATA%'),
                    os.path.expandvars(r'%LOCALAPPDATA%'),
                    os.path.expandvars(r'%USERPROFILE%\Desktop'),
                    os.path.expandvars(r'%USERPROFILE%\Downloads')
                ]
            elif system == 'linux':
                paths = [
                    '/tmp',
                    '/var/tmp',
                    os.path.expanduser('~/Desktop'),
                    os.path.expanduser('~/Downloads')
                ]
            elif system == 'darwin':
                paths = [
                    '/tmp',
                    '/var/tmp',
                    os.path.expanduser('~/Desktop'),
                    os.path.expanduser('~/Downloads')
                ]
            else:
                paths = ['/tmp']
        
        # Add watch paths
        for path in paths:
            self.add_watch_path(path)
        
        # Start observer
        self.observer.start()
        print(f"Monitoring started. Session: {self.session_id}")
        
        try:
            while True:
                time.sleep(1)
                
                # Periodically save session data
                if len(self.event_log) % 100 == 0 and len(self.event_log) > 0:
                    self.save_session_data()
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.observer.stop()
            self.save_session_data()
        
        self.observer.join()
        print("Monitoring stopped.")

def main():
    parser = argparse.ArgumentParser(description="Malware File Monitor")
    parser.add_argument('--output-dir', '-o', default='./malware_cache',
                        help='Output directory for cached files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--no-ml', action='store_true',
                        help='Disable ML mode (use rule-based filtering)')
    parser.add_argument('--min-score', type=int, default=20,
                        help='Minimum suspicion score to log events')
    parser.add_argument('--preserve-threshold', type=int, default=40,
                        help='Suspicion score threshold for file preservation')
    parser.add_argument('--paths', nargs='+',
                        help='Custom paths to monitor')
    parser.add_argument('--test-mode', action='store_true',
                        help='Enable test mode with lower thresholds')
    
    args = parser.parse_args()
    
    # Adjust settings for test mode
    if args.test_mode:
        args.min_score = 10
        args.preserve_threshold = 20
        args.verbose = True
        print("TEST MODE: Lowered thresholds for testing")
    
    # Create monitor
    monitor = MalwareMonitor(
        output_dir=args.output_dir,
        verbose=args.verbose,
        ml_mode=not args.no_ml,
        min_suspicion_score=args.min_score,
        preserve_threshold=args.preserve_threshold
    )
    
    # Start monitoring
    monitor.start_monitoring(args.paths)

if __name__ == "__main__":
    main()
