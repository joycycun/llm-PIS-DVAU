from pydantic import BaseModel, Field

class Device(BaseModel):
    id : str 
    type: str
    name:str
    ip:str
    status:str
    location:str
    