import enum

class UserRole(str, enum.Enum):
    USER = "user"
    EVENT_MANAGER = "event_manager"