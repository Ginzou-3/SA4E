#!/usr/bin/env python3
import sys
import json
import random
import argparse


def generate_extended_tracks(num_tracks, length_of_track, prob_caesar=0.2, prob_bottleneck=0.2):
    all_tracks = []
    for t in range(1, num_tracks + 1):
        track_id = str(t)
        segments = []
        # Erstes Segment: Start-&-Goal (fest)
        start_segment_id = f"start-and-goal-{t}"
        if length_of_track == 1:
            next_segments = [start_segment_id]
        else:
            next_segments = [f"segment-{t}-1"]
        segments.append({
            "segmentId": start_segment_id,
            "type": "start-goal",
            "nextSegments": next_segments
        })
        # Restliche Segmente: zufällige Typen (normal, caesar, bottleneck)
        for c in range(1, length_of_track):
            seg_id = f"segment-{t}-{c}"
            seg_type = random.choices(
                population=["normal", "caesar", "bottleneck"],
                weights=[1 - (prob_caesar + prob_bottleneck), prob_caesar, prob_bottleneck],
                k=1
            )[0]
            if c == length_of_track - 1:
                next_segs = [start_segment_id]
            else:
                next_segs = [f"segment-{t}-{c + 1}"]
            segments.append({
                "segmentId": seg_id,
                "type": seg_type,
                "nextSegments": next_segs
            })
        all_tracks.append({
            "trackId": track_id,
            "segments": segments
        })
    return {"tracks": all_tracks}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("num_tracks", type=int, help="Anzahl der Tracks")
    parser.add_argument("length_of_track", type=int, help="Anzahl der Segmente pro Track")
    parser.add_argument("output_file", help="Ausgabedatei (JSON)")
    parser.add_argument("--prob-caesar", type=float, default=0.2, help="Wahrscheinlichkeit für 'caesar'-Segmente")
    parser.add_argument("--prob-bottleneck", type=float, default=0.2,
                        help="Wahrscheinlichkeit für 'bottleneck'-Segmente")
    args = parser.parse_args()

    if args.prob_caesar + args.prob_bottleneck > 1:
        print("Die Summe der Wahrscheinlichkeiten für caesar und bottleneck darf 1 nicht überschreiten.")
        sys.exit(1)

    track_data = generate_extended_tracks(args.num_tracks, args.length_of_track, args.prob_caesar, args.prob_bottleneck)
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(track_data, f, indent=2)
    print(f"Erweiterte Streckenbeschreibung wurde in '{args.output_file}' gespeichert.")


if __name__ == "__main__":
    main()
