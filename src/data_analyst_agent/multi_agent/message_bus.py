from .communication.message import AgentMessage
class MessageBus:
    def __init__(self): self.events = []; self.subscribers = []
    def publish(self, message: AgentMessage):
        self.events.append(message)
        for subscriber in self.subscribers: subscriber(message)
    def subscribe(self, callback): self.subscribers.append(callback)
