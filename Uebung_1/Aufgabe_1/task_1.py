import tkinter as tk
import threading
import time
import math
import random

# Parameter für die Simulation#
PHASE_INCREMENT = 0.05  # Geschwindigkeit des eigenen Aufleuchtens
K = 0.01  # Kopplungsstärke
UPDATE_INTERVAL = 0.01  # Aktualisierungsintervall in Sekunden

# Schnelle Synchronisation: Erhöhe K oder verringere PHASE_INCREMENT.
# Langsame Synchronisation: Verringere K oder erhöhe PHASE_INCREMENT.
# Flüssige Animationen: Verringere UPDATE_INTERVAL.

class Firefly:
    def __init__(self, x, y, grid, canvas, rect, pause_event):
        self.x = x
        self.y = y
        self.phase = random.uniform(0, 2 * math.pi)  # Zufällige Anfangsphase
        self.grid = grid
        self.canvas = canvas
        self.rect = rect
        self.neighbors = []  # Nachbarn werden später hinzugefügt
        self.lock = threading.Lock()
        self.running = True
        self.pause_event = pause_event

    def add_neighbors(self):
        # Torus-Nachbarn bestimmen
        self.neighbors = [
            self.grid[(self.x - 1) % len(self.grid)][self.y],  # oben
            self.grid[(self.x + 1) % len(self.grid)][self.y],  # unten
            self.grid[self.x][(self.y - 1) % len(self.grid[0])],  # links
            self.grid[self.x][(self.y + 1) % len(self.grid[0])],  # rechts
        ]

    def update_phase(self):
        # Phase aktualisieren (Kuramoto-Modell)
        with self.lock:
            delta_phase = PHASE_INCREMENT
            for neighbor in self.neighbors:
                with neighbor.lock:
                    delta_phase += K * math.sin(neighbor.phase - self.phase)
            self.phase = (self.phase + delta_phase) % (2 * math.pi)

    def run(self):
        while self.running:
            self.pause_event.wait()  # Wartet, bis die Pause aufgehoben wird
            self.update_phase()
            # Farbe basierend auf Phase ändern
            brightness = int((1 + math.sin(self.phase)) * 127.5)
            color = f"#{brightness:02x}{brightness:02x}00"  # Grün
            self.canvas.itemconfig(self.rect, fill=color)
            time.sleep(UPDATE_INTERVAL)

class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.threads = []
        self.grid = []
        self.canvas = None
        self.fireflies = []
        self.grid_size = tk.IntVar(value=5)
        self.pause_event = threading.Event()
        self.pause_event.set()  # Startet unpausiert

        self.build_ui()

    def build_ui(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(control_frame, text="Grid Size:").pack(side=tk.LEFT, padx=5)
        self.grid_size_entry = tk.Entry(control_frame, textvariable=self.grid_size, width=5)
        self.grid_size_entry.pack(side=tk.LEFT)

        self.start_button = tk.Button(control_frame, text="Start", command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = tk.Button(control_frame, text="Pause", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(control_frame, text="Stop", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(self.root, width=500, height=500, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def toggle_pause(self):
        if self.pause_event.is_set():  # Wenn nicht pausiert
            self.pause_event.clear()
            self.pause_button.config(text="Continue")
        else:  # Wenn pausiert
            self.pause_event.set()
            self.pause_button.config(text="Pause")

    def stop_simulation(self):
        self.running = False
        self.pause_event.set()  # Stellt sicher, dass Threads nicht blockiert sind
        for firefly in self.fireflies:
            firefly.running = False
        self.threads = []
        self.fireflies = []
        self.grid = []
        self.canvas.delete("all")
        self.grid_size_entry.config(state=tk.NORMAL)
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

    def initialize_grid(self):
        self.grid = []
        self.fireflies = []
        self.threads = []
        self.canvas.delete("all")
        size = self.grid_size.get()
        rect_size = 500 // size

        for x in range(size):
            row = []
            for y in range(size):
                rect = self.canvas.create_rectangle(
                    x * rect_size, y * rect_size,
                    (x + 1) * rect_size, (y + 1) * rect_size,
                    fill="black"
                )
                firefly = Firefly(x, y, self.grid, self.canvas, rect, self.pause_event)
                row.append(firefly)
                self.fireflies.append(firefly)
            self.grid.append(row)

        for row in self.grid:
            for firefly in row:
                firefly.add_neighbors()

    def start_simulation(self):
        if not self.running:
            self.running = True
            self.grid_size_entry.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.initialize_grid()
            for firefly in self.fireflies:
                thread = threading.Thread(target=firefly.run, daemon=True)
                thread.start()
                self.threads.append(thread)

def main():
    root = tk.Tk()
    root.title("Zaghafte erste Glühwürmchen")
    app = SimulationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
