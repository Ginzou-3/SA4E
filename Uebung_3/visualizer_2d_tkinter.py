#!/usr/bin/env python3
import tkinter as tk
import threading
import time
import json
from confluent_kafka import Consumer

# Beispiel: 4 Segmente. Für jedes Segment definieren wir eine (x,y)-Position
# im Canvas, an der ein Kreis gezeichnet wird.
SEGMENT_COORDS = {
    "start-and-goal-1": (200, 300),
    "segment-1-1": (200, 100),
    "segment-1-2": (400, 200),
    "segment-1-3": (0, 200),
}


class KafkaVisualizerApp(tk.Tk):
    def __init__(self, broker, topics):
        super().__init__()
        self.title("Race Visualizer 2D")
        self.geometry("600x400")

        # Canvas für die 2D-Darstellung
        self.canvas = tk.Canvas(self, width=600, height=400, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Wagen-Positionen: segmentId -> [wagenId, ...]
        self.positions = {}
        for t in topics:
            self.positions[t] = []

        # Start Consumer-Thread
        self.consumer_thread = KafkaConsumerThread(broker, topics, self.positions)
        self.consumer_thread.start()

        # Zeichnung alle 500ms aktualisieren
        self.update_drawing()

    def update_drawing(self):
        # Canvas leeren
        self.canvas.delete("all")

        # Für jedes Segment einen Kreis zeichnen + Text
        radius = 30
        for seg_id, (x, y) in SEGMENT_COORDS.items():
            # Kreis
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="lightblue")

            # Segment-Name
            self.canvas.create_text(x, y - radius - 10, text=seg_id, fill="black", font=("Arial", 10, "bold"))

            # Wagen-IDs in diesem Segment
            wagen_list = self.positions.get(seg_id, [])
            if wagen_list:
                text = ",".join(wagen_list)
            else:
                text = ""
            # Wagen-IDs direkt in den Kreis schreiben
            self.canvas.create_text(x, y, text=text, fill="black", font=("Arial", 10))

        # Nächste Aktualisierung in 500ms
        self.after(500, self.update_drawing)


class KafkaConsumerThread(threading.Thread):
    """
    Hintergrund-Thread, der laufend Kafka-Nachrichten pollt
    und die Positionen aktualisiert.
    """

    def __init__(self, broker, topics, positions):
        super().__init__()
        self.daemon = True  # Thread endet, wenn Hauptprogramm endet
        self.broker = broker
        self.topics = topics
        self.positions = positions
        self._running = True

        # Consumer erstellen
        conf = {
            "bootstrap.servers": self.broker,
            "group.id": "visualizer-group",
            "auto.offset.reset": "earliest",
            # Minimales Logging
            # "debug": "",
            "log_level": 0
        }
        self.consumer = Consumer(conf)
        self.consumer.subscribe(self.topics)

    def run(self):
        while self._running:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                continue

            token_raw = msg.value()
            token = json.loads(token_raw.decode('utf-8'))

            wagen_id = token["wagenId"]
            current_segment = msg.topic()  # Wir nutzen den Topic-Namen als "Segment"

            # Entfernen aus alten Segmenten
            for seg_id in self.positions.keys():
                if wagen_id in self.positions[seg_id]:
                    self.positions[seg_id].remove(wagen_id)
            # Hinzufügen im aktuellen Segment
            self.positions[current_segment].append(wagen_id)

        self.consumer.close()

    def stop(self):
        self._running = False


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default="localhost:9092")
    parser.add_argument("--topics", nargs="+", default=[
        "start-and-goal-1", "segment-1-1", "segment-1-2", "segment-1-3"
    ], help="Liste der Topics (Segment-IDs)")
    args = parser.parse_args()

    app = KafkaVisualizerApp(args.broker, args.topics)
    app.mainloop()
    # Wenn Fenster geschlossen, Thread stoppen
    app.consumer_thread.stop()


if __name__ == "__main__":
    main()
