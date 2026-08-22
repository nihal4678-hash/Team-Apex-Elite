from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    email: str
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str
