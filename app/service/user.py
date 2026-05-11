import hashlib
import bcrypt

pwd_context = None

def get_password_hash(password: str) -> str:
    password_hash = hashlib.sha256(password.encode()).hexdigest().encode()
    hashed = bcrypt.hashpw(password_hash, bcrypt.gensalt())
    return hashed.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_hash = hashlib.sha256(plain_password.encode()).hexdigest().encode()
    return bcrypt.checkpw(password_hash, hashed_password.encode())
