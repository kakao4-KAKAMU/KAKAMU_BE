from uuid import UUID

def key_as_uuid(key: str):
    return UUID(key.split(":")[2])

def key_as_int(key: str):
    return int(key.split(":")[2])