# AI-Based Occupancy Meter System

An intelligent occupancy detection system that uses YOLO (You Only Look Once) for real-time person detection and counting, with MQTT integration for building management systems.

## Features

- **Real-time Person Detection**: Uses YOLOv8 for accurate person detection and counting
- **Multiple Input Sources**: Supports local cameras, video files, and RTSP streams from IP cameras
- **MQTT Integration**: Publishes occupancy data to MQTT topics for integration with dashboards and building management systems
- **Average Calculation**: Calculates and publishes average occupancy over configurable time windows
- **High Performance**: Optimized for low latency (< 5 seconds)
- **Scalable**: Supports multiple rooms with configurable room identifiers
- **Monitoring**: Comprehensive logging and performance metrics
- **Reliable**: Robust error handling and MQTT reconnection logic

## Requirements

- Python 3.8 or higher
- Camera, video file, or RTSP stream for input
- MQTT broker (e.g., Mosquitto, HiveMQ, AWS IoT Core)
- CUDA-capable GPU (optional, for faster inference)
- Network access (if using RTSP streams from IP cameras)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. The YOLOv8 model will be automatically downloaded on first run. Alternatively, you can download it manually:
   - YOLOv8n (nano): Lightweight, fast, good for CPU
   - YOLOv8s (small): Balanced performance
   - YOLOv8m (medium): Better accuracy
   - YOLOv8l (large): High accuracy
   - YOLOv8x (xlarge): Highest accuracy

## Configuration

Edit `config.yaml` to configure the system:

```yaml
# Room Configuration
room:
  identifier: "room1"
  building: "building"

# MQTT Configuration
mqtt:
  broker_host: "localhost"
  broker_port: 1883
  topic_prefix: "building/room1"
  qos: 1
  keepalive: 60
  username: null  # Set if authentication required
  password: null  # Set if authentication required

# Detection Configuration
detection:
  model_path: "yolov8n.pt"  # YOLOv8 model
  confidence_threshold: 0.5
  device: "cpu"  # "cpu" or "cuda" for GPU
  input_source: 0  # Camera index or video file path

# Average Calculation
averaging:
  time_window_seconds: 60  # Time window for average calculation
  update_interval_seconds: 5  # How often to publish updates

# Logging
logging:
  level: "INFO"
  log_file: "occupancy_meter.log"
```

### Configuration Options

- **room.identifier**: Unique identifier for the room
- **mqtt.broker_host**: MQTT broker hostname or IP address
- **mqtt.broker_port**: MQTT broker port (default: 1883)
- **mqtt.topic_prefix**: Base topic prefix (e.g., "building/room1")
- **mqtt.qos**: Quality of Service level (0, 1, or 2)
- **detection.model_path**: Path to YOLO model file
- **detection.confidence_threshold**: Minimum confidence for detections (0.0-1.0)
- **detection.device**: "cpu" or "cuda" for GPU acceleration
- **detection.input_source**: Camera index (0, 1, 2...), video file path, or RTSP stream URL
- **averaging.time_window_seconds**: Time window for average occupancy calculation
- **averaging.update_interval_seconds**: Interval between MQTT publications

### Using RTSP Streams

The system supports RTSP (Real-Time Streaming Protocol) streams from IP cameras and network video sources. To use an RTSP stream, set the `input_source` in your `config.yaml` to the RTSP URL.

#### RTSP URL Format

Common RTSP URL formats:

```yaml
# Basic RTSP URL
detection:
  input_source: "rtsp://username:password@ip_address:port/stream_path"

# Examples:
# Hikvision camera
input_source: "rtsp://admin:password123@192.168.1.100:554/Streaming/Channels/101"

# Dahua camera
input_source: "rtsp://admin:password123@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0"

# Generic RTSP stream
input_source: "rtsp://192.168.1.100:8554/live"

# RTSP with authentication
input_source: "rtsp://user:pass@192.168.1.100:554/stream1"
```

#### Configuration Example for RTSP

```yaml
detection:
  model_path: "yolov8n.pt"
  confidence_threshold: 0.5
  device: "cpu"
  input_source: "rtsp://admin:password123@192.168.1.100:554/Streaming/Channels/101"
```

#### RTSP Stream Tips

1. **Network Requirements**: Ensure stable network connectivity between the system and the camera
2. **Authentication**: Include username and password in the RTSP URL if required by your camera
3. **Stream Path**: Check your camera's documentation for the correct RTSP stream path
4. **Port**: Default RTSP port is 554, but some cameras use different ports
5. **Codec Support**: Most modern IP cameras support H.264/H.265 which OpenCV can handle

#### Troubleshooting RTSP Streams

If you encounter issues with RTSP streams:

- **Connection Timeout**: Verify the camera IP address and port are correct
- **Authentication Failed**: Double-check username and password in the RTSP URL
- **Stream Not Found**: Verify the stream path matches your camera's RTSP endpoint
- **Network Issues**: Test the RTSP stream with VLC or ffplay first:
  ```bash
  # Test with VLC
  vlc rtsp://username:password@ip_address:port/stream_path
  
  # Test with ffplay
  ffplay rtsp://username:password@ip_address:port/stream_path
  ```
- **Firewall**: Ensure port 554 (or your camera's RTSP port) is not blocked
- **Bandwidth**: RTSP streams require sufficient network bandwidth; consider reducing stream quality if needed
- **Reconnection**: The system will automatically retry reading frames if the stream temporarily disconnects

## Usage

### Basic Usage

Run the occupancy meter with default configuration:

```bash
python occupancy_detector.py
```

Or specify a custom configuration file:

```bash
python occupancy_detector.py custom_config.yaml
```

### MQTT Topics

The system publishes to the following MQTT topics:

- **Current Occupancy**: `{topic_prefix}/occupancy/current`
  ```json
  {
    "count": 5,
    "timestamp": "2024-01-15T10:30:00.123456",
    "room": "room1"
  }
  ```

- **Average Occupancy**: `{topic_prefix}/occupancy/average`
  ```json
  {
    "average": 4.5,
    "time_window_seconds": 60,
    "timestamp": "2024-01-15T10:30:00.123456",
    "room": "room1"
  }
  ```

### Testing with MQTT Client

Use the provided test client to subscribe to MQTT topics:

```bash
python mqtt_test_client.py
```

Or use a command-line MQTT client like `mosquitto_sub`:

```bash
# Subscribe to all occupancy topics
mosquitto_sub -h localhost -p 1883 -t "building/room1/occupancy/#" -v

# Subscribe to current occupancy only
mosquitto_sub -h localhost -p 1883 -t "building/room1/occupancy/current" -v

# Subscribe to average occupancy only
mosquitto_sub -h localhost -p 1883 -t "building/room1/occupancy/average" -v
```

## System Architecture

```
┌─────────────┐
│ Video Input │
│ (Camera/    │
│  Video File/│
│  RTSP Stream)│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ YOLO Model  │
│ (Person     │
│  Detection) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Occupancy   │
│ Counter     │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│ Average     │────▶│ MQTT        │
│ Calculator  │     │ Publisher   │
└─────────────┘     └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ MQTT Broker │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Dashboards/ │
                    │ BMS Systems │
                    └─────────────┘
```

## Performance

- **Detection Latency**: < 5 seconds (typically < 1 second on CPU, < 0.1 seconds on GPU)
- **Accuracy**: > 90% in controlled test scenarios
- **Frame Rate**: 10-30 FPS depending on hardware and model size
- **MQTT Reliability**: Automatic reconnection and retry logic

## Monitoring

The system logs the following information:

- **Connection Status**: MQTT broker connection/disconnection events
- **Occupancy Updates**: Current and average occupancy counts
- **Performance Metrics**: FPS, uptime, frame count, MQTT publish statistics
- **Errors**: Detection errors, MQTT publish failures, connection issues

Logs are written to both console and the log file specified in `config.yaml`.

## Multi-Room Support

To monitor multiple rooms, run separate instances with different configuration files:

```bash
# Room 1
python occupancy_detector.py config_room1.yaml

# Room 2
python occupancy_detector.py config_room2.yaml
```

Each instance should have:
- Unique `room.identifier`
- Unique `mqtt.topic_prefix` (e.g., "building/room1", "building/room2")
- Potentially different `detection.input_source` (different cameras)

## Troubleshooting

### Camera Not Opening
- Check if the camera index is correct (try 0, 1, 2...)
- Ensure no other application is using the camera
- On Linux, check camera permissions

### MQTT Connection Failed
- Verify MQTT broker is running: `mosquitto -v`
- Check broker hostname and port
- Verify network connectivity
- Check firewall settings

### Low Detection Accuracy
- Adjust `confidence_threshold` in config
- Use a larger YOLO model (yolov8s.pt, yolov8m.pt)
- Ensure good lighting conditions
- Check camera angle and field of view

### High Latency
- Use GPU acceleration: set `device: "cuda"` in config
- Use a smaller YOLO model (yolov8n.pt)
- Reduce input resolution
- Increase `update_interval_seconds` to reduce MQTT publish frequency

### RTSP Stream Issues
- **Stream won't connect**: Verify the RTSP URL format and test with VLC or ffplay
- **Authentication errors**: Check username and password in the RTSP URL
- **Intermittent disconnections**: Check network stability and camera health
- **Slow frame rate**: Network bandwidth may be insufficient; check camera stream settings
- **Black screen or no video**: Verify the stream path is correct for your camera model
- **Connection timeout**: Ensure firewall allows RTSP traffic on port 554 (or custom port)

## License

This project is provided as-is for educational and commercial use.

## Contributing

Contributions are welcome! Please ensure code follows PEP 8 style guidelines and includes appropriate error handling.

