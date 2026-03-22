# 🚀 Aura-Edu Setup Guide

## Quick Start

### 1. Installation
```bash
# Clone and setup
git clone <repository>
cd aura-edu
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run System
```bash
# Main closed-loop system
python aura_edu_system.py

# API Server (separate terminal)
python -m api.main

# Dashboard (separate terminal)
streamlit run dashboard/app.py
```

## 🎯 System Components

### Core System (`aura_edu_system.py`)
**Main closed-loop neuroadaptive system**
- Vision processing with YOLO
- 4-directional ultrasonic simulation
- Decision engine with reaction monitoring
- 8-motor haptic feedback
- Real-time analytics and logging

### API Layer (`api/main.py`)
**REST API for UI integration**
- Live data streaming
- Historical metrics
- System configuration
- Manual controls
- WebSocket support

### Dashboard (`dashboard/`)
**Monitoring and analytics interface**
- Real-time system status
- Performance metrics
- Left vs right analysis
- Progress tracking

## 🔧 Configuration

Edit `utils/config.py`:

```python
# Vision Settings
camera_index = 0
preprocess_width = 960

# Decision Engine
neglected_side = "LEFT"  # Focus area for rehabilitation
observation_window = 2.0  # Seconds to wait for user reaction
critical_distance = 50.0  # cm - trigger intervention

# Hardware (when available)
esp32_port = "COM3"  # Windows
# esp32_port = "/dev/ttyUSB0"  # Linux
motor_count = 8

# System
battery_capacity = 5000  # mAh
```

## 📊 Key Features

### 1. Wait-and-Observe Approach
- Detects stimuli via camera + ultrasonic sensors
- **Doesn't immediately vibrate**
- Monitors if user responds naturally
- Intervenes only if user fails to react

### 2. Directional Feedback
- **LEFT**: Motors 0,1 activate
- **RIGHT**: Motors 6,7 activate  
- **FRONT**: Motors 3,4 activate
- **BACK**: Motors 2,5 activate

### 3. Comprehensive Analytics
- **Awareness Score**: 0-100 composite metric
- **Left vs Right Analysis**: Critical for neglect assessment
- **Reaction Time**: Speed and consistency tracking
- **Progress Trends**: Daily/weekly improvement

## 🌐 API Endpoints

### Live Data
```bash
GET /live-data
# Returns: current stimuli, decisions, metrics, system status
```

### Metrics
```bash
GET /metrics?period=realtime
GET /metrics/historical?days=7
```

### System Status
```bash
GET /system-status
# Battery, health, component status
```

### Manual Controls
```bash
POST /vibration/trigger
{
  "direction": "LEFT",
  "intensity": 0.7,
  "pattern": "DOUBLE_PULSE"
}
```

### Analytics
```bash
GET /analytics/left-right    # Hemispatial analysis
GET /performance/report    # Full performance report
```

## 🧪 Testing

### Test Vibration System
```python
# In aura_edu_system.py console
system.manual_vibration_test("LEFT", 0.8)
system.manual_vibration_test("RIGHT", 0.5)
```

### Export Session Data
```python
system.export_session_data("json")
# Creates: exports/aura_edu_session_timestamp.json
```

### View System Status
```python
system.print_system_info()
# Shows: FPS, battery, components, metrics
```

## 🔍 Monitoring

### Console Output
```
🧠 Aura-Edu AI-Powered Neuroadaptive System
🎯 Target: Hemispatial Neglect Rehabilitation
============================================================
🚀 Starting Aura-Edu System...
✅ Aura-Edu System started successfully
📊 API available at: http://localhost:8000
🔌 Press Ctrl+C to stop

🔄 Main loop started
🎯 Simulated approaching object from LEFT
⚡ START Motor 0 (LEFT) - Intensity: 0.60
⚡ START Motor 1 (LEFT) - Intensity: 0.60
```

### Performance Metrics
```
🎯 Awareness Score: 73.2
📈 Grade: GOOD
⚖️  Neglect Severity: MILD
📊 Level: 82.3%
⚡ Runtime: 245min
🌡️  Temp: 26.1°C
```

## 🎮 Interactive Features

### Real-time Visualization
- Object detection boxes with direction labels
- Distance measurements from ultrasonic sensors
- Reaction monitoring progress bars
- System health indicators

### Progress Tracking
- Daily success/failure rates
- Left vs right performance comparison
- Awareness score trends
- Personalized recommendations

### Alert System
- Low battery warnings
- Component failure notifications
- Performance degradation alerts
- Intervention frequency monitoring

## 🔌 Hardware Integration (Future)

### ESP32 Connection
```python
# Replace simulation with real hardware
from hardware.esp32_comm import ESP32Controller

esp32 = ESP32Controller(port="COM3", baudrate=115200)
esp32.connect()
```

### Real Sensors
```python
# Replace simulated sensors
from hardware.real_sensors import UltrasonicArray

sensors = UltrasonicArray()
sensors.initialize_hardware()
```

### Vibration Belt
```python
# Replace simulation with real motors
from hardware.motor_controller import MotorBelt

belt = MotorBelt(motor_count=8)
belt.initialize_pwm()
```

## 📈 Performance Optimization

### For Low-Performance Systems
```python
# Reduce processing load
target_fps = 15          # Default: 30
preprocess_width = 640    # Default: 960
detection_confidence = 0.7 # Default: 0.5
```

### For High-Performance Systems
```python
# Maximum accuracy
target_fps = 60
preprocess_width = 1280
detection_confidence = 0.3
```

## 🐛 Troubleshooting

### Common Issues

**Camera not found**
```bash
# Check available cameras
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"

# Update config
camera_index = 1  # Try different indices
```

**YOLO model missing**
```bash
# Auto-download on first run, or manually:
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
mv yolov8n.pt models/
```

**High CPU usage**
- Reduce FPS in config
- Lower camera resolution
- Close background applications

**API not accessible**
```bash
# Check port availability
netstat -an | grep 8000

# Try different port
uvicorn api.main:app --port 8001
```

### Debug Mode
```bash
python aura_edu_system.py --debug
# Enables verbose logging and performance metrics
```

## 📊 Data Export

### Automatic Logs
- Events stored in `data/aura_edu.db`
- Daily metrics computed automatically
- Session summaries generated on shutdown

### Manual Export
```python
# Via API
POST /export?format=csv&days=30

# Via code
system.export_session_data("json")
system.export_session_data("csv")
```

### Export Formats
- **JSON**: Complete structured data
- **CSV**: Flattened tabular format
- **SQLite**: Direct database access

## 🎯 Success Metrics

### Performance Grades
- **A (90-100)**: Excellent - Highly responsive and balanced
- **B (80-89)**: Good - Room for minor improvements  
- **C (70-79)**: Satisfactory - Needs focused improvement
- **D (60-69)**: Poor - Significant intervention needed
- **F (<60)**: Critical - Immediate attention required

### Rehabilitation Progress
1. **Week 1-2**: System learning baseline
2. **Week 3-4**: Initial improvement patterns
3. **Month 2**: Noticeable progress in neglected side
4. **Month 3**: Reduced intervention frequency
5. **Month 6**: Near-independence in daily activities

---

## 🧠 Next Steps

1. **Run the system**: `python aura_edu_system.py`
2. **Open API docs**: http://localhost:8000/docs  
3. **Monitor dashboard**: Streamlit interface
4. **Review metrics**: Track awareness score progress
5. **Export data**: Analyze session performance

**Welcome to the future of neuroadaptive rehabilitation!** 🚀
