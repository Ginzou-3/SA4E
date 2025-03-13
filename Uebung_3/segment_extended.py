#!/usr/bin/env python3
import json
import time
import argparse
import random
from confluent_kafka import Consumer, Producer


def create_consumer(broker, group_id, topic):
    conf = {
        "bootstrap.servers": broker,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "log_level": 0
    }
    consumer = Consumer(conf)
    consumer.subscribe([topic])
    return consumer


def create_producer(broker):
    conf = {
        "bootstrap.servers": broker,
        "log_level": 0
    }
    producer = Producer(conf)
    return producer


def run_segment(segment_id, next_segments, broker, seg_type, start_cmd=False, max_rounds=3, wagen_list=None):
    consumer = create_consumer(broker, f"group-{segment_id}", segment_id)
    producer = create_producer(broker)

    if seg_type == "start-goal":
        start_times = {}
        rounds = {}
        if start_cmd and wagen_list:
            print(f"[{segment_id}] Starte das Rennen. Sende initiale Token ...")
            for w in wagen_list:
                token = {
                    "wagenId": w,
                    "runde": 1,
                    "startTimestamp": time.time(),
                    "trackId": "1",
                    "greetedCaesar": False
                }
                start_times[w] = token["startTimestamp"]
                rounds[w] = 1
                for nxt in next_segments:
                    producer.produce(nxt, json.dumps(token).encode("utf-8"))
            producer.flush()
        print(f"[{segment_id}] Warte auf eingehende Token (max. Runden: {max_rounds}) ...")
        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    print(f"[{segment_id}] Consumer-Fehler: {msg.error()}")
                    continue
                token = json.loads(msg.value().decode("utf-8"))
                wagen = token["wagenId"]
                new_round = token["runde"] + 1
                if new_round > max_rounds:
                    # Check if the token has greeted Caesar
                    if not token.get("greetedCaesar", False):
                        print(
                            f"[{segment_id}] Wagen '{wagen}' hat Caesar noch nicht gegrüßt. Der Wagen muss Caesar grüßen, bevor er die Ziellinie überquert.")
                        # Do not finish: force the token to repeat the current lap.
                        token["runde"] = max_rounds
                        for nxt in next_segments:
                            producer.produce(nxt, json.dumps(token).encode("utf-8"))
                        producer.flush()
                    else:
                        total = time.time() - start_times.get(wagen, time.time())
                        print(f"[{segment_id}] Wagen '{wagen}' hat das Ziel erreicht! Laufzeit: {total:.2f} s")
                        # Token wird nicht weitergeleitet.
                else:
                    token["runde"] = new_round
                    for nxt in next_segments:
                        producer.produce(nxt, json.dumps(token).encode("utf-8"))
                    producer.flush()
        except KeyboardInterrupt:
            print(f"[{segment_id}] Beende ...")
        finally:
            consumer.close()
    else:
        print(f"[{segment_id}] Segmenttyp '{seg_type}'. Warte auf Token ...")
        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    print(f"[{segment_id}] Consumer-Fehler: {msg.error()}")
                    continue
                token = json.loads(msg.value().decode("utf-8"))
                if seg_type == "caesar":
                    # If not already greeted, mark the token and print a greeting message.
                    if not token.get("greetedCaesar", False):
                        token["greetedCaesar"] = True
                        print(f"[{segment_id}] Wagen '{token['wagenId']}' grüßt Caesar!")
                    else:
                        print(f"[{segment_id}] Wagen '{token['wagenId']}' hat Caesar bereits gegrüßt.")
                    time.sleep(0.5)
                elif seg_type == "bottleneck":
                    delay = random.uniform(1.0, 3.0)
                    print(f"[{segment_id}] Bottleneck: Verzögere Wagen '{token['wagenId']}' um {delay:.2f} s")
                    time.sleep(delay)
                # For normal segments, no additional delay is introduced.
                for nxt in next_segments:
                    producer.produce(nxt, json.dumps(token).encode("utf-8"))
                producer.flush()
        except KeyboardInterrupt:
            print(f"[{segment_id}] Beende ...")
        finally:
            consumer.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment-id", required=True, help="Segment-ID (z.B. 'segment-1-2' oder 'start-and-goal-1')")
    parser.add_argument("--next-segments", required=True, nargs="+", help="Liste der nächsten Segment-IDs")
    parser.add_argument("--broker", default="localhost:9092", help="Kafka Broker Adresse")
    parser.add_argument("--type", required=True, choices=["start-goal", "normal", "caesar", "bottleneck"],
                        help="Segmenttyp")
    parser.add_argument("--start", action="store_true", help="Für start-goal: initial Tokens senden")
    parser.add_argument("--runden", type=int, default=3, help="Maximale Runden (nur start-goal)")
    parser.add_argument("--wagen", nargs="+", help="Liste der Wagen-IDs (nur start-goal)")
    args = parser.parse_args()

    run_segment(args.segment_id, args.next_segments, args.broker, args.type, start_cmd=args.start,
                max_rounds=args.runden, wagen_list=args.wagen)


if __name__ == "__main__":
    main()
