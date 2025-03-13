#!/usr/bin/env python3
import json
import time
import argparse
from confluent_kafka import Consumer, Producer

def create_consumer(broker, group_id, topic):
    consumer_conf = {
        'bootstrap.servers': broker,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'debug': 'broker,topic,msg',
        'log_level': 1
    }
    print(f"[DEBUG] create_consumer() => {consumer_conf}")
    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])
    return consumer

def create_producer(broker):
    producer_conf = {
        'bootstrap.servers': broker,
        'debug': 'broker,topic,msg',
        'log_level': 1
    }
    print(f"[DEBUG] create_producer() => {producer_conf}")
    producer = Producer(producer_conf)
    return producer

def run_normal_segment(segment_id, next_segments, broker):
    in_topic = segment_id
    out_topics = next_segments

    consumer = create_consumer(broker, f"group-{segment_id}", in_topic)
    producer = create_producer(broker)

    print(f"[{segment_id}] Warte auf eingehende Tokens…")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"[DEBUG] Consumer-Fehler: {msg.error()}")
                continue

            token_raw = msg.value()
            token = json.loads(token_raw.decode('utf-8'))

            # Direkt weiterleiten
            for ntopic in out_topics:
                print(f"[DEBUG] PRODUCE Weiterleitung an {ntopic} => {token}")
                producer.produce(ntopic, json.dumps(token).encode('utf-8'))

            producer.flush()

    except KeyboardInterrupt:
        print(f"[{segment_id}] Beende…")
    finally:
        consumer.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment-id", required=True)
    parser.add_argument("--next-segments", required=True, nargs="+")
    parser.add_argument("--broker", default="localhost:9092")
    args = parser.parse_args()

    run_normal_segment(
        segment_id=args.segment_id,
        next_segments=args.next_segments,
        broker=args.broker
    )

if __name__ == "__main__":
    main()
