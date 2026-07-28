from enum import Enum
class Permission(str, Enum): READ = "read"; WRITE = "write"; DELETE = "delete"
class SessionStatus(str, Enum): DISCONNECTED = "disconnected"; CONNECTED = "connected"; FAILED = "failed"
