"""
MQTT Test Client for Occupancy Meter System
Subscribes to occupancy topics and displays received messages
"""

import paho.mqtt.client as mqtt
import json
import sys
from datetime import datetime


class OccupancyTestClient:
    """Test client to subscribe and display occupancy data"""
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883,
                 topic_prefix: str = "building/room1", username: str = None,
                 password: str = None):
        """
        Initialize test client
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            topic_prefix: Topic prefix to subscribe to
            username: MQTT username (optional)
            password: MQTT password (optional)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic_prefix = topic_prefix
        self.message_count = 0
        
        # Initialize MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        if username and password:
            self.client.username_pw_set(username, password)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Subscribe to occupancy topics
            current_topic = f"{self.topic_prefix}/occupancy/current"
            average_topic = f"{self.topic_prefix}/occupancy/average"
            
            client.subscribe(current_topic, qos=1)
            client.subscribe(average_topic, qos=1)
            client.subscribe(f"{self.topic_prefix}/occupancy/#", qos=1)
            
            print(f"✓ Subscribed to: {current_topic}")
            print(f"✓ Subscribed to: {average_topic}")
            print(f"✓ Subscribed to: {self.topic_prefix}/occupancy/#")
            print("\n" + "="*60)
            print("Waiting for occupancy messages...")
            print("="*60 + "\n")
        else:
            print(f"✗ Failed to connect. Return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        self.message_count += 1
        
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            # Format timestamp
            timestamp = payload.get('timestamp', 'N/A')
            if timestamp != 'N/A':
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            # Display message based on topic
            if 'current' in topic:
                count = payload.get('count', 'N/A')
                room = payload.get('room', 'N/A')
                print(f"[{timestamp}] 📊 CURRENT OCCUPANCY")
                print(f"   Room: {room}")
                print(f"   Count: {count} people")
                print()
            elif 'average' in topic:
                average = payload.get('average', 'N/A')
                time_window = payload.get('time_window_seconds', 'N/A')
                room = payload.get('room', 'N/A')
                print(f"[{timestamp}] 📈 AVERAGE OCCUPANCY")
                print(f"   Room: {room}")
                print(f"   Average: {average} people")
                print(f"   Time Window: {time_window} seconds")
                print()
            else:
                print(f"[{timestamp}] 📨 Message on {topic}:")
                print(f"   {json.dumps(payload, indent=2)}")
                print()
            
        except json.JSONDecodeError:
            print(f"⚠️  Received non-JSON message on {msg.topic}: {msg.payload.decode()}")
        except Exception as e:
            print(f"⚠️  Error processing message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects"""
        if rc != 0:
            print(f"⚠️  Unexpected disconnection. Return code: {rc}")
        else:
            print("✓ Disconnected from MQTT broker")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.client.disconnect()
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MQTT Test Client for Occupancy Meter')
    parser.add_argument('--host', default='localhost', help='MQTT broker hostname')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--topic', default='building/room1', help='Topic prefix')
    parser.add_argument('--username', default=None, help='MQTT username')
    parser.add_argument('--password', default=None, help='MQTT password')
    
    args = parser.parse_args()
    
    client = OccupancyTestClient(
        broker_host=args.host,
        broker_port=args.port,
        topic_prefix=args.topic,
        username=args.username,
        password=args.password
    )
    
    client.connect()

