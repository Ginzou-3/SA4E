#!/usr/bin/env python3
import json
import subprocess
import time
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", action="store_true",
                        help="Start-&-Goal-Segmente schicken sofort Token ins Rennen.")
    parser.add_argument("--runden", type=int, default=3,
                        help="Anzahl der Runden pro Wagen")
    parser.add_argument("--wagen", nargs="+", default=["A", "B", "C"],
                        help="Liste der Wagen-IDs")
    parser.add_argument("--broker", default="localhost:9092",
                        help="Kafka Broker Adresse")
    parser.add_argument("--json-file", default="kurs.json",
                        help="Name der JSON-Datei mit der Streckenbeschreibung")
    args = parser.parse_args()

    # 1) JSON-Datei lesen
    with open(args.json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    processes = []

    # 2) Für jede Strecke und jedes Segment passendes Skript starten
    for track in data["tracks"]:
        for seg in track["segments"]:
            segment_id = seg["segmentId"]
            seg_type = seg["type"]
            next_segments = seg["nextSegments"]

            if seg_type == "start-goal":
                cmd = [
                    "python",
                    "segment_start_and_goal.py",
                    "--segment-id", segment_id,
                    "--next-segments"
                ] + next_segments + [
                    "--broker", args.broker,
                    "--runden", str(args.runden)
                ]
                # Wagen-IDs anhängen
                cmd += ["--wagen"] + args.wagen

                # Falls --start übergeben wurde, hängt man es auch hier an
                if args.start:
                    cmd.append("--start")

                print("Starte Start/Goal-Segment:", cmd)
                p = subprocess.Popen(cmd)
                processes.append(p)

            else:
                cmd = [
                    "python",
                    "segment_normal.py",
                    "--segment-id", segment_id,
                    "--next-segments"
                ] + next_segments + [
                    "--broker", args.broker
                ]
                print("Starte normales Segment:", cmd)
                p = subprocess.Popen(cmd)
                processes.append(p)

    print("Alle Segmente wurden gestartet.")
    print("\nMit STRG+C können Sie alle Prozesse beenden.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Beende alle Prozesse.")
        for p in processes:
            p.terminate()
        print("Fertig.")

if __name__ == "__main__":
    main()
