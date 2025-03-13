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
        # Weniger Spam: nur bestimmte Subsysteme, Loglevel auf Info
        # 'debug': 'broker,topic,msg',
        'log_level': 0
    }
    print(f"[DEBUG] create_consumer() => {consumer_conf}")
    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])
    return consumer

def create_producer(broker):
    producer_conf = {
        'bootstrap.servers': broker,
        # 'debug': 'broker,topic,msg',
        'log_level': 0
    }
    # print(f"[DEBUG] create_producer() => {producer_conf}")
    producer = Producer(producer_conf)
    return producer

def run_start_and_goal(segment_id, next_segments, broker, start_cmd, runden_max, wagen_liste):
    in_topic = segment_id
    out_topics = next_segments  # in Aufgabe 1 i.d.R. nur ein Segment in nextSegments

    consumer = create_consumer(broker, f"group-{segment_id}", in_topic)
    producer = create_producer(broker)

    startzeiten = {}
    runden_map = {}

    # Wenn --start angegeben ist: Wagen ins Rennen schicken
    if start_cmd:
        print(f"[{segment_id}] Starte das Rennen, schicke erste Tokens …")
        for wagen_id in wagen_liste:
            token = {
                "wagenId": wagen_id,
                "runde": 1,
                "startTimestamp": time.time(),
                "trackId": "1"
            }
            startzeiten[wagen_id] = token["startTimestamp"]
            runden_map[wagen_id] = 1
            for ntopic in out_topics:
                print(f"[DEBUG] PRODUCE Token an Topic={ntopic} => {token}")
                producer.produce(ntopic, json.dumps(token).encode('utf-8'))
        producer.flush()

    print(f"[{segment_id}] Warte auf eingehende Tokens (max. {runden_max} Runden)…")

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
            wagen_id = token["wagenId"]
            aktuelle_runde = token["runde"]

            if wagen_id not in startzeiten:
                # Token zum ersten Mal gesehen
                startzeiten[wagen_id] = token["startTimestamp"]
                runden_map[wagen_id] = aktuelle_runde

            neue_runde = aktuelle_runde + 1
            runden_map[wagen_id] = neue_runde

            if neue_runde > runden_max:
                end_time = time.time()
                total_time = end_time - startzeiten[wagen_id]
                print(f"[{segment_id}] Wagen '{wagen_id}' hat das Ziel erreicht! "
                      f"Gesamtzeit: {total_time:.3f} Sekunden, Runden: {runden_max}")
            else:
                # Weiterleiten
                token["runde"] = neue_runde
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
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--runden", type=int, default=3)
    parser.add_argument("--wagen", nargs="+", default=["Alpha", "Beta"])
    args = parser.parse_args()

    run_start_and_goal(
        segment_id=args.segment_id,
        next_segments=args.next_segments,
        broker=args.broker,
        start_cmd=args.start,
        runden_max=args.runden,
        wagen_liste=args.wagen
    )

if __name__ == "__main__":
    main()
