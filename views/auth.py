from fastapi import APIRouter, status, Form, Depends
from pydantic import EmailStr
from passlib.context import CryptContext
from database.mongodb import users_collection , Company_collection, user_company_collection
from bson import ObjectId
from models.auth import RegisterSchema , LoginSchema, CompanyLoginSchema
from fastapi import HTTPException
from datetime import datetime, timedelta
from config.setting import settings
import jwt
from middleware.middleware import verify_token
from fastapi.responses import JSONResponse

auth_router = APIRouter(prefix="/api/v1/auth",tags=["Authenticate User"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@auth_router.post("/register",
                  status_code=status.HTTP_201_CREATED)
async def RegisterUser(register:RegisterSchema):
    existing_user = await users_collection.find_one({"email": register.email})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = pwd_context.hash(register.password)

    user_data = {
        "name": register.name,
        "email": register.email,
        "password": hashed_password
    }

    await users_collection.insert_one(user_data)

    return {"message": "User registered successfully!"}

@auth_router.post("/login")
async def login(login:LoginSchema):
    user = await users_collection.find_one({"email": login.email})
    if not user or not pwd_context.verify(login.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user["_id"]),
        "email": str(login.email),
        "exp": expire
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

@auth_router.get("/me")
async def get_user_profile(user_id: str = Depends(verify_token)):
    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        print(user)
        if user:
            user['_id'] = str(user['_id'])  # Convert ObjectId to string
            # Remove password from user data
            del user['password']
            return JSONResponse({"success": "User Details sent successfully", "user": user})
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user details: {str(e)}"
        )

@auth_router.post("/company-login")
async def company_login(email: str = Form(), password: str = Form()):
    user = await Company_collection.find_one({"email": email})
    if not user:
        return JSONResponse(status_code=401, content={"message": "Invalid credentials"})
    
    saved_password = user.get("password")
    if password != saved_password:
        return JSONResponse(status_code=401, content={"message": "Invalid credentials"})

    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user["_id"]),
        "email": str(email),
        "exp": expire
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

@auth_router.post("/company-user-login")
async def login(login:LoginSchema):
    user = await user_company_collection.find_one({"email": login.email})
    if user['password'] != login.password:
        return JSONResponse(status_code=401, content={"message": "Invalid credentials"})

    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user["_id"]),
        "email": str(login.email),
        "exp": expire
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}