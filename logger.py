from datetime import datetime
from console_output import print_json


class AgentLogger:

    def __init__(self):
        self.logs = []

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    def print(self):
        print_json("AGENT EXECUTION TRACE", self.logs)
