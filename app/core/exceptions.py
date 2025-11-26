from fastapi import  Request
from fastapi.responses import JSONResponse

# custom exception class
class CustomError(Exception):
    def __init__(self,message:str, status_code:int =400):
        self.message=message
        self.status_code= status_code 

# function  for global exception handler 
async def custom_error_handler(request:Request, exc:CustomError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
                "data": {},
                "status":exc.status_code,
                "message": exc.message,
                "error": True,
        
        }
    )

# we need to register in main.py 