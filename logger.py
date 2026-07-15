from datetime import datetime


class AgentLogger:

    def __init__(self):
        self.logs = []

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    def print(self):
        print("\n===== AGENT EXECUTION TRACE =====")
        for message in self.logs:
            print(message)
