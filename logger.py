from datetime import datetime


class AgentLogger:

    def __init__(self):
        self.logs = []

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    def print(self):
        print("\n" + "=" * 60)
        print("🤖 AGENT EXECUTION TRACE")
        print("=" * 60)

        for log in self.logs:
            print(log)

        print("=" * 60)