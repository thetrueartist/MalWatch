# MalWatch

**Advanced Malware File Activity Monitor**

A cross-platform file system monitoring tool designed for malware analysis and incident response. MalWatch intelligently tracks, analyzes, and preserves suspicious file drops in real-time using advanced statistical analysis and machine learning techniques.

*Created because I couldn't find an existing alternative that provided the depth of analysis and real-time preservation capabilities needed for effective malware research and incident response.*

## Features

- 🔍 **Intelligent Detection** - Statistical analysis, ML-based anomaly detection, and behavioral heuristics
- 🧬 **Advanced Analysis** - Shannon entropy, chi-squared testing, PE structure analysis, and string analysis  
- 💾 **Comprehensive Preservation** - Automatic file caching with metadata and hash-based deduplication
- 🌐 **Cross-Platform** - Windows, Linux, and macOS support
- ⚡ **Real-time Monitoring** - Instant detection across multiple high-risk paths
- 📊 **Rich Metadata** - Detailed analysis results, timestamps, and system context

## Installation

    pip install watchdog psutil numpy scikit-learn

## Quick Start

    # Start monitoring with default settings
    python malwatch.py --verbose

    # Monitor specific paths with custom thresholds
    python malwatch.py --paths /tmp /home/user/Downloads --preserve-threshold 50

    # Test mode for evaluation
    python malwatch.py --test-mode

## Usage

### Basic Monitoring

    # Default monitoring (recursively monitors temp directories, desktop, downloads)
    python malwatch.py

    # Verbose output
    python malwatch.py --verbose

    # Custom output directory
    python malwatch.py --output-dir /path/to/cache

### Advanced Configuration

    # Disable ML mode (rule-based only)
    python malwatch.py --no-ml

    # Adjust sensitivity
    python malwatch.py --min-score 30 --preserve-threshold 50

    # Monitor specific paths recursively
    python malwatch.py --paths /tmp /var/log /home/user/Downloads

### Testing

    # Run the malware simulator for testing
    python malware_simulator.py --quick

    # Full simulation
    python malware_simulator.py

## How It Works

MalWatch uses multiple analysis techniques to identify suspicious files:

### Statistical Analysis

- Shannon Entropy: Detects packed/encrypted files (entropy > 7.0)
- Chi-squared Test: Identifies statistical randomness patterns
- Byte Frequency Analysis: Examines distribution patterns for anomalies

### Behavioral Detection

- Path Analysis: Recursively monitors high-risk directories (/tmp, %TEMP%, %APPDATA%) and all subdirectories
- Extension Analysis: Flags suspicious file types (.exe, .dll, .scr, .bat, .ps1) anywhere in monitored trees
- Size Analysis: Detects unusually small executables (droppers) or very large files throughout directory structures

### Machine Learning (Optional)

- Anomaly Detection: Uses Isolation Forest for outlier detection
- Classification: Random Forest classifier for malware prediction
- Feature Engineering: Combines statistical and behavioral features

## Output Structure

    malware_cache/
    ├── README.md
    ├── 2024-01-15/
    │   ├── session_20240115_143022/
    │   │   ├── preserved_files/
    │   │   │   ├── 20240115_143045_a1b2c3d4_malware.exe
    │   │   │   ├── 20240115_143045_a1b2c3d4_malware.exe.meta.json
    │   │   │   └── ...
    │   │   ├── events.json
    │   │   └── metadata.json
    │   └── ...

## Configuration

### Command Line Options

| Option                 | Description                                | Default           |
|------------------------|--------------------------------------------|-------------------|
| --output-dir           | Output directory for cached files          | ./malware_cache   |
| --verbose              | Enable verbose output                      | False             |
| --no-ml                | Disable ML mode (rule-based only)          | False             |
| --min-score            | Minimum suspicion score to log             | 20                |
| --preserve-threshold   | Score threshold for file preservation      | 40                |
| --paths                | Custom paths to monitor                    | Platform defaults |
| --test-mode            | Enable test mode (lower thresholds)        | False             |

### Cross-Platform Support

- Windows: Recursively monitors %TEMP%, %APPDATA%, %LOCALAPPDATA%, Desktop, Downloads and all subdirectories
- Linux: Recursively tracks /tmp, /var/tmp, user directories, and system paths including all subdirectories
- macOS: Comprehensive recursive monitoring of temp directories and user spaces

## Suspicion Scoring

| Factor                   | Score | Description                         |
|--------------------------|-------|-------------------------------------|
| Suspicious extension     | +30   | .exe, .dll, .ps1, .bat, etc.        |
| Very high entropy (>7.5) | +35   | Likely packed/encrypted             |
| High entropy (>7.0)      | +25   | Possibly packed                     |
| High randomness (chi²>400) | +30 | Statistical anomaly                 |
| Low byte variance        | +25   | Possible encryption                 |
| Suspicious path          | +25   | Temp directories, user profiles     |
| Small executable         | +20   | Potential dropper                   |
| Large file (>50MB)       | +15   | Potential payload                   |

## Performance

- Small files (<1MB): ~200ms processing time
- Large files (>50MB): ~1.5s processing time (optimized)
- Throughput: 100+ files/minute for typical workloads
- Memory usage: <100MB for extended monitoring sessions

## Requirements

- Python 3.7+
- Cross-platform support (Windows, Linux, macOS)
- Dependencies: watchdog, psutil, numpy, scikit-learn

## Contributing

Contributions welcome! Areas for improvement:

- YARA rule integration
- Additional ML models
- Performance optimizations
- UI/dashboard

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built for the security research community after I couldn't find an alternative :p 
