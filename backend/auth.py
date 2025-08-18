from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

SECRET_KEY = "gjklpigfde4567uhgfcvbnmitfrwq3456743wa"
ALGORITHM = "HS256"

# fixed typo: deprecated not depreceated
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Create JWT token
def create_jwt(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload = {
        "sub": str(user_id),  # JWT expects subject to be string
        "exp": exp
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# Verify JWT token
def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)  # ✅ missing return


# Verify password
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)  # ✅ missing return
