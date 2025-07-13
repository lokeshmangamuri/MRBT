# import threading
# import time
#
#
# class Intention:
#     def __init__(self, agent_id, action, target, status, timestamp=None):
#         self.agent_id = agent_id
#         self.action = action
#         self.target = target
#         self.status = status
#         self.timestamp = timestamp or time.time()
#
#     def __repr__(self):
#         return (
#             f"<Intention {self.agent_id} {self.action} {self.target} "
#             f"{self.status} @ {self.timestamp}>"
#         )
#
#
# class IntentionManager:
#     def __init__(self):
#         self._intentions = {}
#         self._lock = threading.Lock()
#         self._subscribers = []
#         self._messages = []
#         self._message_lock = threading.Lock()
#
#     def update_intention(self, agent_id, action, target, status):
#         with self._lock:
#             intention = Intention(agent_id, action, target, status)
#             self._intentions[agent_id] = intention
#         self._notify_subscribers()
#
#     def clear_intention(self, agent_id):
#         with self._lock:
#             if agent_id in self._intentions:
#                 del self._intentions[agent_id]
#         self._notify_subscribers()
#
#     def get_all_intentions(self):
#         with self._lock:
#             return dict(self._intentions)
#
#     def subscribe(self, callback_fn):
#         self._subscribers.append(callback_fn)
#
#     def _notify_subscribers(self):
#         current = self.get_all_intentions()
#         for cb in self._subscribers:
#             cb(current)
#
#     def broadcast_message(self, agent_id, message):
#         with self._message_lock:
#             self._messages.append({"from": agent_id, "message": message})
#
#     def get_messages(self):
#         with self._message_lock:
#             msgs = list(self._messages)
#             self._messages.clear()
#             return msgs
#
#     def detect_conflicts(self):
#         with self._lock:
#             target_map = {}
#             for i in self._intentions.values():
#                 key = i.target
#                 if key not in target_map:
#                     target_map[key] = []
#                 target_map[key].append(i)
#             conflicts = []
#             for t, intents in target_map.items():
#                 if len(intents) > 1:
#                     conflicts.append((t, intents))
#             return conflicts
#
#
# # Singleton shared across all agents
# GLOBAL_INTENTION_MANAGER = IntentionManager()
# from datetime import datetime
#
# class Intention:
#     def __init__(self, agent_id, action, target, status):
#         self.agent_id = agent_id
#         self.action = action
#         self.target = target
#         self.status = status
#         self.timestamp = datetime.utcnow().isoformat()
#
#     def __repr__(self):
#         return (
#             f"<Intention agent={self.agent_id} action={self.action} "
#             f"target={self.target} status={self.status} timestamp={self.timestamp}>"
#         )
#
# class IntentionManager:
#     def __init__(self):
#         self._intentions = {}
#         self._subscribers = []
#
#     def update_intention(self, agent_id, action, target, status):
#         self._intentions[str(agent_id)] = Intention(agent_id, action, target, status)
#         print(f"[IntentionManager] UPDATED intentions: {self._intentions}")
#         self._notify()
#
#     def clear_intention(self, agent_id):
#         if str(agent_id) in self._intentions:
#             del self._intentions[str(agent_id)]
#             print(f"[IntentionManager] CLEARED intention of agent {agent_id}")
#             self._notify()
#
#     def get_all_intentions(self):
#         print(f"[IntentionManager] GET ALL intentions: {self._intentions}")
#         return dict(self._intentions)
#
#     def subscribe(self, fn):
#         self._subscribers.append(fn)
#         print(f"[IntentionManager] SUBSCRIBER REGISTERED: {fn}")
#
#     def _notify(self):
#         current = self.get_all_intentions()
#         for cb in self._subscribers:
#             print(f"[IntentionManager] NOTIFYING subscriber: {cb}")
#             cb(current)
#
# GLOBAL_INTENTION_MANAGER = IntentionManager()
# intention_manager.py

import threading
import time


class Intention:
    def __init__(self, agent_id, action, target, status, timestamp=None):
        self.agent_id = agent_id
        self.action = action
        self.target = target
        self.status = status
        self.timestamp = timestamp or time.time()

    def __repr__(self):
        return (
            f"<Intention {self.agent_id} {self.action} {self.target} "
            f"{self.status} @ {self.timestamp}>"
        )


class IntentionManager:
    def __init__(self):
        self._intentions = {}
        self._lock = threading.Lock()
        self._subscribers = []
        self._messages = []
        self._message_lock = threading.Lock()

    def update_intention(self, agent_id, action, target, status):
        """Call when an agent starts or updates its current action."""
        with self._lock:
            intention = Intention(agent_id, action, target, status)
            self._intentions[agent_id] = intention
        self._notify_subscribers()

    def clear_intention(self, agent_id):
        """Call when an agent completes or abandons its action."""
        with self._lock:
            if agent_id in self._intentions:
                del self._intentions[agent_id]
        self._notify_subscribers()

    def get_all_intentions(self):
        with self._lock:
            return dict(self._intentions)

    def subscribe(self, callback_fn):
        """Subscribe to intention‐updates: callback_fn gets the full dict."""
        self._subscribers.append(callback_fn)

    def _notify_subscribers(self):
        current = self.get_all_intentions()
        for cb in self._subscribers:
            cb(current)

    def broadcast_message(self, agent_id, message):
        """Generic message bus for negotiation, failures, etc."""
        with self._message_lock:
            self._messages.append({"from": agent_id, "message": message})

    def get_messages(self):
        with self._message_lock:
            msgs = list(self._messages)
            self._messages.clear()
            return msgs

    def detect_conflicts(self):
        """Find targets that more than one agent is working on."""
        with self._lock:
            target_map = {}
            for intent in self._intentions.values():
                key = intent.target
                target_map.setdefault(key, []).append(intent)
            return [(t, its) for t, its in target_map.items() if len(its) > 1]


# Singleton to import from anywhere:
GLOBAL_INTENTION_MANAGER = IntentionManager()
