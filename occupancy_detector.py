"""
AI-based Occupancy Meter System
Uses YOLO for person detection and MQTT for data publishing
"""

import cv2
import time
import logging
import yaml
from collections import deque
from datetime import datetime
from typing import Optional
from ultralytics import YOLO
import paho.mqtt.client as mqtt
import json


class OccupancyDetector:
    """YOLO-based person detection and counting system"""
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.5, device: str = "cpu"):
        """
        Initialize the occupancy detector
        
        Args:
            model_path: Path to YOLO model file
            confidence_threshold: Minimum confidence for person detection
            device: Device to run inference on ("cpu" or "cuda")
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.current_count = 0
        self.logger = logging.getLogger(__name__)
        
    def detect_people(self, frame) -> int:
        """
        Detect and count people in a frame
        
        Args:
            frame: Input image frame (numpy array)
            
        Returns:
            Number of people detected
        """
        try:
            # Run YOLO inference
            results = self.model(frame, conf=self.confidence_threshold, device=self.device, verbose=False)
            
            # Count people (class 0 in COCO dataset is 'person')
            person_count = 0
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Check if detected object is a person (class 0)
                        if int(box.cls) == 0:
                            person_count += 1
            
            self.current_count = person_count
            return person_count
            
        except Exception as e:
            self.logger.error(f"Error during detection: {e}")
            return 0


class MQTTClient:
    """MQTT client for publishing occupancy data"""
    
    def __init__(self, broker_host: str, broker_port: int, topic_prefix: str, 
                 qos: int = 1, keepalive: int = 60, username: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize MQTT client
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            topic_prefix: Prefix for all topics (e.g., "building/room1")
            qos: Quality of Service level (0, 1, or 2)
            keepalive: Keepalive interval in seconds
            username: MQTT username (optional)
            password: MQTT password (optional)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic_prefix = topic_prefix
        self.qos = qos
        self.keepalive = keepalive
        self.logger = logging.getLogger(__name__)
        
        # Initialize MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        
        if username and password:
            self.client.username_pw_set(username, password)
        
        self.connected = False
        self.publish_count = 0
        self.failed_publish_count = 0
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response from the server"""
        if rc == 0:
            self.connected = True
            self.logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            self.logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the server"""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection. Return code: {rc}")
        else:
            self.logger.info("Disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for when a message is published"""
        self.publish_count += 1
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, self.keepalive)
            self.client.loop_start()
            # Wait for connection
            timeout = 5
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            return self.connected
        except Exception as e:
            self.logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish_current_occupancy(self, count: int):
        """Publish current occupancy count"""
        topic = f"{self.topic_prefix}/occupancy/current"
        payload = json.dumps({
            "count": count,
            "timestamp": datetime.now().isoformat(),
            "room": self.topic_prefix.split("/")[-1] if "/" in self.topic_prefix else "unknown"
        })
        return self._publish(topic, payload)
    
    def publish_average_occupancy(self, average: float, time_window: int):
        """Publish average occupancy over time window"""
        topic = f"{self.topic_prefix}/occupancy/average"
        payload = json.dumps({
            "average": round(average, 2),
            "time_window_seconds": time_window,
            "timestamp": datetime.now().isoformat(),
            "room": self.topic_prefix.split("/")[-1] if "/" in self.topic_prefix else "unknown"
        })
        return self._publish(topic, payload)
    
    def _publish(self, topic: str, payload: str) -> bool:
        """Internal method to publish message"""
        if not self.connected:
            self.logger.warning("MQTT client not connected. Attempting to reconnect...")
            if not self.connect():
                self.failed_publish_count += 1
                return False
        
        try:
            result = self.client.publish(topic, payload, qos=self.qos)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                return True
            else:
                self.failed_publish_count += 1
                self.logger.error(f"Failed to publish to {topic}. Return code: {result.rc}")
                return False
        except Exception as e:
            self.failed_publish_count += 1
            self.logger.error(f"Error publishing to {topic}: {e}")
            return False


class OccupancyMeter:
    """Main occupancy meter system"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the occupancy meter system
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.detector = OccupancyDetector(
            model_path=self.config['detection']['model_path'],
            confidence_threshold=self.config['detection']['confidence_threshold'],
            device=self.config['detection']['device']
        )
        
        mqtt_config = self.config['mqtt']
        self.mqtt_client = MQTTClient(
            broker_host=mqtt_config['broker_host'],
            broker_port=mqtt_config['broker_port'],
            topic_prefix=mqtt_config['topic_prefix'],
            qos=mqtt_config['qos'],
            keepalive=mqtt_config['keepalive'],
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password')
        )
        
        # Occupancy tracking
        self.occupancy_history = deque(maxlen=1000)  # Store occupancy readings with timestamps
        self.time_window = self.config['averaging']['time_window_seconds']
        self.update_interval = self.config['averaging']['update_interval_seconds']
        
        # Performance metrics
        self.start_time = time.time()
        self.frame_count = 0
        self.last_publish_time = time.time()
        self.running = False
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config['logging']
        log_level = getattr(logging, log_config['level'].upper())
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_config['log_file'])
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def _calculate_average_occupancy(self) -> float:
        """Calculate average occupancy over the configured time window"""
        if not self.occupancy_history:
            return 0.0
        
        current_time = time.time()
        cutoff_time = current_time - self.time_window
        
        # Filter readings within time window
        recent_readings = [
            count for timestamp, count in self.occupancy_history
            if timestamp >= cutoff_time
        ]
        
        if not recent_readings:
            return 0.0
        
        return sum(recent_readings) / len(recent_readings)
    
    def _log_performance_metrics(self):
        """Log system performance metrics"""
        uptime = time.time() - self.start_time
        fps = self.frame_count / uptime if uptime > 0 else 0
        
        self.logger.info(
            f"Performance Metrics - "
            f"Uptime: {uptime:.1f}s, "
            f"FPS: {fps:.2f}, "
            f"Frames Processed: {self.frame_count}, "
            f"MQTT Published: {self.mqtt_client.publish_count}, "
            f"MQTT Failed: {self.mqtt_client.failed_publish_count}, "
            f"MQTT Connected: {self.mqtt_client.connected}"
        )
    
    def run(self):
        """Main execution loop"""
        self.logger.info("Starting Occupancy Meter System")
        
        # Connect to MQTT
        if not self.mqtt_client.connect():
            self.logger.error("Failed to connect to MQTT broker. Exiting.")
            return
        
        # Open video source
        input_source = self.config['detection']['input_source']
        if isinstance(input_source, int):
            cap = cv2.VideoCapture(input_source)
        else:
            cap = cv2.VideoCapture(input_source)
        
        if not cap.isOpened():
            self.logger.error(f"Failed to open video source: {input_source}")
            self.mqtt_client.disconnect()
            return
        
        self.logger.info(f"Video source opened: {input_source}")
        self.running = True
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    self.logger.warning("Failed to read frame. Retrying...")
                    time.sleep(0.1)
                    continue
                
                # Detect people
                start_detection = time.time()
                count = self.detector.detect_people(frame)
                detection_time = time.time() - start_detection
                
                # Store occupancy reading
                current_time = time.time()
                self.occupancy_history.append((current_time, count))
                self.frame_count += 1
                
                # Publish current occupancy (every frame, but throttled by update_interval)
                if current_time - self.last_publish_time >= self.update_interval:
                    # Publish current occupancy
                    self.mqtt_client.publish_current_occupancy(count)
                    
                    # Calculate and publish average occupancy
                    avg_occupancy = self._calculate_average_occupancy()
                    self.mqtt_client.publish_average_occupancy(avg_occupancy, self.time_window)
                    
                    self.last_publish_time = current_time
                    
                    self.logger.info(
                        f"Occupancy - Current: {count}, "
                        f"Average ({self.time_window}s): {avg_occupancy:.2f}, "
                        f"Detection Time: {detection_time*1000:.1f}ms"
                    )
                    
                    # Log performance metrics periodically
                    if self.frame_count % 100 == 0:
                        self._log_performance_metrics()
                
                # Check latency
                if detection_time > 5.0:
                    self.logger.warning(f"Detection latency exceeds 5 seconds: {detection_time:.2f}s")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal. Shutting down...")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            cap.release()
            self.mqtt_client.disconnect()
            self.running = False
            self.logger.info("Occupancy Meter System stopped")
            self._log_performance_metrics()


if __name__ == "__main__":
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    meter = OccupancyMeter(config_path)
    meter.run()

