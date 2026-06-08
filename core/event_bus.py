class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, channel, callback):
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)

    def publish(self, channel, data=None):
        if channel in self._subscribers:
            for callback in self._subscribers[channel]:
                callback(data)


bus = EventBus()
