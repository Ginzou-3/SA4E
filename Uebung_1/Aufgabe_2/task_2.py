import grpc
import firefly_pb2
import firefly_pb2_grpc
from concurrent import futures
import tkinter as tk
import threading
import time
import math
import random
import logging

# Parameter für die Simulation
PHASE_INCREMENT = 0.1  # Geschwindigkeit des eigenen Aufleuchtens
K = 0.1  # Kopplungsstärke
BLINK_INTERVAL = 0.1  # Intervall für das Blinken der Glühwürmchen in Sekunden
UPDATE_INTERVAL = 5  # Aktualisierungsintervall für das Anfragen bei Nachbarn in Sekunden

# Logging-Initialisierung
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# gRPC Server Code
class FireflyServicer(firefly_pb2_grpc.FireflyServiceServicer):
    def __init__(self, firefly):
        self.firefly = firefly
        self.logger = logging.getLogger(f'FireflyServicer-{self.firefly.port}')

    def SendPhase(self, request, context):
        self.logger.info(f"Received phase request: {request.phase}")
        response = firefly_pb2.PhaseResponse()
        response.phase = self.firefly.phase

        # Phase aktualisieren basierend auf empfangener Phase
        received_phase = request.phase
        self.firefly.phase = (self.firefly.phase + K * math.sin(received_phase - self.firefly.phase)) % (2 * math.pi)

        self.logger.info(f"Returning response phase: {response.phase}")
        return response

def serve(firefly):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    firefly_pb2_grpc.add_FireflyServiceServicer_to_server(FireflyServicer(firefly), server)
    server.add_insecure_port(f'[::]:{firefly.port}')
    logging.info(f"Starting server on port {firefly.port}...")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

class Firefly:
    def __init__(self, x, y, grid, canvas, rect, pause_event, port):
        self.x = x
        self.y = y
        self.phase = random.uniform(0, 2 * math.pi)
        self.grid = grid
        self.canvas = canvas
        self.rect = rect
        self.neighbors = []
        self.lock = threading.Lock()
        self.running = True
        self.pause_event = pause_event
        self.port = port

        # Logging-Initialisierung
        self.logger = logging.getLogger(f'Firefly-{self.port}')

        # Starte gRPC Server für dieses Glühwürmchen
        try:
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
            firefly_pb2_grpc.add_FireflyServiceServicer_to_server(FireflyServicer(self), self.server)
            self.server.add_insecure_port(f'[::]:{self.port}')
            self.server.start()
            self.logger.info(f"Starting server on port {self.port}...")
        except Exception as e:
            self.logger.error(f"Failed to bind to port {self.port}: {e}")

    def add_neighbors(self, neighbors_ports):
        self.neighbors_ports = neighbors_ports

    def update_phase(self):
        with self.lock:
            delta_phase = PHASE_INCREMENT
            self.phase = (self.phase + delta_phase) % (2 * math.pi)

    def sync_with_neighbors(self):
        with self.lock:
            for port in self.neighbors_ports:
                with grpc.insecure_channel(f'localhost:{port}') as channel:
                    stub = firefly_pb2_grpc.FireflyServiceStub(channel)
                    request = firefly_pb2.PhaseRequest(phase=self.phase)
                    self.logger.info(f"Sending phase request to port {port}: {self.phase}")
                    response = stub.SendPhase(request)
                    self.logger.info(f"Received phase response from port {port}: {response.phase}")
                    self.phase = (self.phase + K * math.sin(response.phase - self.phase)) % (2 * math.pi)

    def blink(self):
        while self.running:
            self.pause_event.wait()
            brightness = int((1 + math.sin(self.phase)) * 127.5)
            color = f"#{brightness:02x}{brightness:02x}00"
            self.canvas.itemconfig(self.rect, fill=color)
            time.sleep(BLINK_INTERVAL)

    def run(self):
        threading.Thread(target=self.blink, daemon=True).start()
        while self.running:
            self.pause_event.wait()
            self.update_phase()
            if int(time.time()) % UPDATE_INTERVAL == 0:
                self.sync_with_neighbors()
            time.sleep(BLINK_INTERVAL)

class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.threads = []
        self.grid = []
        self.canvas = None
        self.fireflies = []
        self.grid_size = tk.IntVar(value=3)
        self.pause_event = threading.Event()
        self.pause_event.set()

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
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.config(text="Continue")
        else:
            self.pause_event.set()
            self.pause_button.config(text="Pause")

    def stop_simulation(self):
        self.running = False
        self.pause_event.set()
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
        port_base = 5000

        for x in range(size):
            row = []
            for y in range(size):
                rect = self.canvas.create_rectangle(
                    x * rect_size, y * rect_size,
                    (x + 1) * rect_size, (y + 1) * rect_size,
                    fill="black"
                )
                firefly = Firefly(x, y, self.grid, self.canvas, rect, self.pause_event, port_base)
                row.append(firefly)
                self.fireflies.append(firefly)
                port_base += 1
            self.grid.append(row)

        for x in range(size):
            for y in range(size):
                firefly = self.grid[x][y]
                neighbors_ports = [
                    self.grid[(x - 1) % size][y].port,
                    self.grid[(x + 1) % size][y].port,
                    self.grid[x][(y - 1) % size].port,
                    self.grid[x][(y + 1) % size].port,
                ]
                firefly.add_neighbors(neighbors_ports)

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
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    root.title("Kommunizierende Glühwürmchen")
    app = SimulationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
