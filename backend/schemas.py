from pydantic import BaseModel , field_validator , EmailStr , Field


class UserCreate(BaseModel):
    email : EmailStr
    password:str = Field(min_length=8)
    
class UserLogin(BaseModel):
    email:EmailStr
    password:str = Field(min_length=8)  
    
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"