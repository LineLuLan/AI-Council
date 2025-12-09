from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
import requests

# Import your local modules
from auth.stack_auth import verify_stack_token
from llm import chat_with_local_model
from models import ChatRequest, User
from config import settings


app = FastAPI()

# 1. Point OAuth2 to our local '/token' endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 2. The Bridge: Create the /token endpoint
# Swagger UI sends the username/password here when you click "Authorize"
@app.post("/token")
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    print(f"\n--- ATTEMPTING LOGIN FOR: {form_data.username} ---")
    
    # Check if Keys are loaded (common mistake!)
    if not settings.X_STACK_PROJECT_ID:
        print("❌ ERROR: X_STACK_PROJECT_ID is missing or empty in .env")
        raise HTTPException(status_code=500, detail="Server config error: Missing Project ID")

    stack_login_url = "https://api.stack-auth.com/api/v1/auth/password/sign-in"
    
    payload = {
        "email": form_data.username, 
        "password": form_data.password
    }
    
    headers = {
        'x-stack-access-type': 'server',
        'x-stack-project-id': settings.X_STACK_PROJECT_ID,
        'x-stack-publishable-client-key': settings.X_STACK_PUBLISHABLE_CLIENT_KEY,
        'x-stack-secret-server-key': settings.X_STACK_SECRET_SERVER_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(stack_login_url, json=payload, headers=headers)
        
        # --- DEBUG LOGGING ---
        print(f"Stack Auth Status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Stack Auth Error Response: {response.text}") # <--- THIS IS KEY
            raise HTTPException(status_code=400, detail=f"Login failed: {response.text}")
            
        data = response.json()
        print("✅ Login Successful!")
        
        return {
            "access_token": data["access_token"], 
            "token_type": "bearer"
        }
        
    except Exception as e:
        print(f"❌ Python Exception: {e}")
        raise HTTPException(status_code=400, detail=str(e))
# 3. Dependency to get current user from token

@app.get("/users/me")
def get_current_user(token: str = Depends(oauth2_scheme)):
    # 1. Debug: Print the raw token receiving from frontend/Swagger
    # print(f"Raw Token received in main: {token}") 

    # 2. Verify
    user_data = verify_stack_token(token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token", # This matches the error in your screenshot
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Return User Object
    return User(
        username=user_data.get("id"),
        email=user_data.get("primary_email")
    )

# 4. Protected Route
@app.get("/hello")
def say_hello(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "message": "Hello World!", 
        "logged_in_as": current_user.email
    }


@app.post("/chat")
def talk_to_ai(
    chat_request: ChatRequest, 
    current_user: Annotated[User, Depends(get_current_user)]
):
    # Log who is asking (optional)
    print(f"User {current_user.email} is asking: {chat_request.prompt}")
    
    # Call Ollama
    ai_response = chat_with_local_model(chat_request.prompt, chat_request.model)
    
    return {
        "user": current_user.email,
        "prompt": chat_request.prompt,
        "response": ai_response
    }