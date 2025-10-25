import json
import time
from kafka import KafkaProducer

# --- CONFIGURATION ---
# We connect to 'localhost:9092' because your docker-compose.yml
# advertises this as the PLAINTEXT_HOST listener
KAFKA_BROKER_URL = "localhost:9092" 
TARGET_TOPIC = "weather_alerts"

# This mock message is designed for your system:
# 1. "event_type": "weather_alert" triggers the weather agent's handler.
# 2. "alert_type": "disaster" will trigger the Coordinator's 
#    "WEATHER_DISASTER" high-priority logic.
TEST_MESSAGE = {
    "event_type": "weather_alert",
    "alert_type": "disaster",
    "severity": "critical",
    "zone_id": "zone-central-park",
    "message": "TEST: Hurricane warning detected."
}

# --- SCRIPT ---
def get_producer():
    """Tries to connect to Kafka on the host."""
    retries = 10
    for i in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER_URL],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            print(f"✅ Connected to Kafka at {KAFKA_BROKER_URL}")
            return producer
        except Exception as e:
            print(f"❌ Failed to connect to Kafka. Retrying... ({i+1}/{retries})")
            time.sleep(3)
    raise ConnectionError("Could not connect to Kafka after several retries.")

def send_message(producer, topic, message):
    """Sends the message."""
    try:
        print(f"\n🚀 Sending message to topic '{topic}':")
        print(json.dumps(message, indent=2))
        
        future = producer.send(topic, message)
        record_metadata = future.get(timeout=10)
        
        print("\n✅ Message sent successfully!")
        print(f"   Topic: {record_metadata.topic}")
        print(f"   Partition: {record_metadata.partition}")
        print(f"   Offset: {record_metadata.offset}")
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
    finally:
        producer.flush()
        producer.close()
        print("\nProducer flushed and closed.")

if __name__ == "__main__":
    try:
        # Note: You may need to run 'pip install kafka-python'
        # on your host machine if it's not already installed.
        kafka_producer = get_producer()
        send_message(kafka_producer, TARGET_TOPIC, TEST_MESSAGE)
    except ConnectionError as e:
        print(e)