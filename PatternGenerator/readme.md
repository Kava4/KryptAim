# 🎯 Pattern Generator - AimSync Recoil Analyzer

**Standalone tool for generating anti-recoil patterns from GIFs/images**  
Integrates with `AimSync` via manual copy-paste to `Recoil/weapon_data.py`

---

## 📚 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Workflow](#workflow)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The **Pattern Generator** is a dedicated tool for creating recoil compensation patterns directly from visual references (GIFs/images). It works independently of the main AimSync application and focuses on:

1. **Analyzing** GIFs/images with bullet impact dots and crosshair positions
2. **Extracting** movement trajectories frame-by-frame  
3. **Generating** anti-recoil patterns ready for manual refinement
4. **Exporting** to Python format compatible with `weapon_data.py`

---

## ✨ Features

### Core Capabilities

- ✅ **GIF/Image Analysis**: Parse animated GIFs and static images
- ✅ **Bullet Impact Detection**: Identify muzzle flash, impact markers, tracer fire
- ✅ **Crosshair Tracking**: Locate cursor position for manual refinement
- ✅ **Pattern Generation**: Auto-calculate recoil compensation vectors
- ✅ **Hybrid Approach**: Auto-detection + manual point editing
- ✅ **AK47 Calibration**: Match existing `assault_rifle` patterns (Phase 1 focus)
- ✅ **Python Export**: Generate code blocks ready to append to weapon_data.py
- ✅ **Visual Feedback**: Real-time analysis progress and results

### Technical Features

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| OpenCV Analysis | Frame-by-frame processing | Detect bullet impact points |
| Numpy Math | Vector calculations | Calculate movement deltas |
| CustomTkinter UI | Modern GUI | Point visualization and editing |
| JSON Export | Pattern metadata storage | Save analysis results |
| Python Code Gen | Direct weapon_data.py format | Easy integration |

---

## 🎬 Workflow

### Scenario 1: Generate from GIF (Recommended)

```
1. Open PatternGenerator GUI (python gui.py)
2. Select or drag-drop AK47 spray GIF from patterns/ folder
3. Click "Analyze & Generate Pattern"
4. Review auto-detected pattern in console logs
5. Manually refine points if needed (future phase)
6. Export JSON or Python code block
7. Copy to weapon_data.py assault_rifle section
```

### Scenario 2: Calibrate Against Existing Pattern

```
1. Load user-generated pattern from saved_patterns/
2. Upload sensitivity calibration video/image  
3. App calculates required adjustments (future feature)
4. Export calibrated version
```

---

## 📦 Installation

### Requirements

The Pattern Generator needs the following Python packages:

**Core Dependencies** (add to `PatternGenerator/requirements.txt`):

```txt
# Image processing and analysis
opencv-python>=4.8.0
numpy>=1.24.0
Pillow>=10.0.0

# GUI framework
customtkinter>=5.2.0

# Utilities
pyyaml>=6.0
tqdm>=4.66.0  # Progress bars
```

**Install Command**:

```bash
cd PatternGenerator
pip install -r requirements.txt
pip install customtkinter opencv-python numpy Pillow pyyaml tqdm
```

---

## 🚀 Usage

### Quick Start

```bash
# Launch the application
python gui.py

# Drag-and-drop a GIF into the input area
# OR use the Select button

# Click "Analyze & Generate Pattern"

# Review analysis results in console logs

# Copy generated code and paste to weapon_data.py
```

### Command Line (Optional)

```bash
# Direct analysis without GUI
python analyze.py --input patterns/ak47_spray.gif --output output.json

# Generate Python file for weapon_data.py
python export.py --json-file output.json --format python --weapon assault_rifle
```

---

## 🏗️ Architecture

### Project Structure

```
PatternGenerator/
├── gui.py                    # Main CustomTkinter application window
├── engine/                   # Core analysis modules
│   ├── __init__.py          # Module exports
│   ├── image_analyzer.py    # Frame parsing and feature detection
│   ├── trajectory_detector.py  # Recoil vector calculation
│   └── pattern_calculator.py  # Pattern generation and export logic
├── patterns/                 # Sample GIFs/images with bullet dots
├── saved_patterns/           # User-created patterns
├── outputs/                  # Analysis results directory
├── config.yaml               # Application settings
└── requirements.txt          # Dependencies list

📄 README.md (this file)
```

### Module Responsibilities

| Module | Responsibility | Key Functions |
|--------|---------------|---------------|
| **ImageAnalyzer** | Parse GIFs, extract frames, detect features | `analyze_file()`, `detect_impact_points()` |
| **TrajectoryDetector** | Calculate recoil vectors per frame | `track_trajectory()`, `compute_delta()` |
| **PatternCalculator** | Generate final pattern and export | `calculate_pattern()`, `export_json()`, `export_python()` |

---

## 📋 Example: AK47 Spray Analysis

### Step 1: Load Sample GIF

```bash
# Navigate to PatternGenerator directory
cd PatternGenerator

# Launch GUI
python gui.py
```

### Step 2: Select Input File

- Drag-drop `patterns/ak47_spray.gif` OR click "Select GIF/Image"
- Verify file loads in preview panel

### Step 3: Analyze Pattern

Click **"Analyze & Generate Pattern"** button. Console shows:

```
[10:15:23] Starting analysis of ak47_spray.gif
[10:15:28] Extracted 18 movement points
[10:15:29] Detected bullet impact at (frame=0, pos=(245, 180))
[10:15:30] Pattern calculation complete!
[10:15:30] Pattern saved to: outputs/ak47_spray_generated.json
```

### Step 4: Review Results

Check the JSON output file for pattern data:

```json
{
  "name": "AK47 Spray - Auto Generated",
  "weapon": "assault_rifle",
  "fps": 60,
  "points": [
    {"x": 0, "y": -8.5, "duration_ms": 600},
    {"x": -12.3, "y": -6.2, "duration_ms": 500}
  ],
  "metadata": {
    "source_file": "ak47_spray.gif",
    "analysis_timestamp": "2024-01-15T10:15:30"
  }
}
```

### Step 5: Export Python Code Block

Generated code block for `weapon_data.py`:

```python
# Add this to Assault Rifle section:
self.assault_rifle = [
    (0, -8.5, 0.1),
    (-12.3, -6.2, 0.1),
    # ... additional points from analysis
]
```

### Step 6: Append to weapon_data.py

- Open `Recoil/weapon_data.py` in your text editor
- Navigate to `assault_rifle` section
- Copy and paste the generated code block
- Ensure tuple format `(x, y, duration)` is correct
- Save file and test in AimSync

---

## 🎨 Advanced Usage Tips

### Manual Refinement (Future Phase)

Once auto-generation reaches 60-70% quality:

1. Load generated pattern from `saved_patterns/`
2. Use interactive canvas to click/edit points
3. Visual feedback shows:
   - 🔵 Blue = Auto-generated points
   - 🟢 Green = Manually refined points  
   - 🟡 Yellow = Suggested corrections
4. Export after refinement

### Calibration Against AK47 (Phase 1 Focus)

To match existing `assault_rifle` pattern:

1. Analyze new GIF with Pattern Generator
2. Load reference pattern from `weapon_data.py`
3. Compare side-by-side in visualizer (future feature)
4. Adjust generated points to match reference structure
5. Export calibrated version

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: "Error opening file"

**Cause**: File path contains spaces or special characters  
**Fix**: Use full absolute path, or rename file without spaces

#### Issue: "GIF parsing failed"

**Cause**: GIF corrupted or non-sequential frames  
**Fix**: Convert to video first, then extract frames; use animated GIFs only

#### Issue: No points detected

**Cause**: Low contrast in GIF, static image treated as single frame  
**Fix**: Use high-contrast images with visible bullet dots/crosshair

---

## 📊 Expected Output Quality

| Metric | Target | Notes |
|--------|--------|-------|
| Auto-Detection Accuracy | 60-70% | Manual refinement expected |
| Pattern Completeness | 80%+ | Some points may need adjustment |
| Export Speed | <5 seconds per GIF | Depends on file size and FPS |

---

## 🔄 Integration with AimSync

The Pattern Generator is **standalone** - it doesn't integrate directly with the main app. Instead:

1. Use Pattern Generator to create JSON or Python code
2. Manually copy content to `Recoil/weapon_data.py`
3. Test in AimSync by loading weapon profiles
4. Return to Pattern Generator for further refinement if needed

---

## 🎯 Next Phases (Roadmap)

### Phase 2: Interactive Refinement UI

- [ ] Canvas-based point editor
- [ ] Click-to-add manual points
- [ ] Visual distinction between auto/manual points
- [ ] Drag-to-modify existing points
- [ ] Undo/redo functionality

### Phase 3: Advanced Calibration

- [ ] Reference pattern overlay system
- [ ] Sensitivity-independent adjustment logic
- [ ] Side-by-side comparison view
- [ ] Automatic calibration suggestions

---

## 📄 License & Disclaimer

This tool is for educational purposes. Use automation responsibly and check game terms of service.

**Built with ❤️ for the AimSync community**

---

## 🆘 Support

Issues or questions?

- **GitHub**: Report bugs or request features
- **Ko-fi**: Support development at https://ko-fi.com/kava4  
- **Public Demo**: Check landing page for examples
