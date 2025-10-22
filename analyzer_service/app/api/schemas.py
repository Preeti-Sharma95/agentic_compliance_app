from pydantic import BaseModel, EmailStr
from typing import Optional

# Base schema for a user
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

# Schema for creating a new user (includes password)
class UserCreate(UserBase):
    password: str
    is_admin: bool = False

# Schema for returning a user from the API (omits password)
class UserOut(UserBase):
    id: int
    is_admin: bool

    class Config:
        # This tells Pydantic to read the data from ORM models (like SQLAlchemy)
        from_attributes = True

# Schema for the token response
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Schema for data embedded within a token
class TokenData(BaseModel):
    username: Optional[str] = None
    token_type: Optional[str] = None