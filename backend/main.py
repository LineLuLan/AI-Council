from inspect import stack
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
import pydantic
import requests
import traceback
from sqlalchemy.orm import Session


# Import your local modules
from auth.stack_auth import create_stack_user, verify_stack_token
from llm import chat_with_local_model
from models import ChatRequest, User, RegisterRequest
from db import get_db
from config import settings
from datetime import datetime, timezone


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

@app.post("/register")
def register_user(user_in: RegisterRequest, db: requests.Session = Depends(get_db)):
    print(f"\n--- REGISTER ATTEMPT: {user_in.email} ---")
    
    try:
        # 1. Check local DB
        if db.query(User).filter(User.email == user_in.email).first():
            print("❌ Error: Email already exists locally.")
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2. Create in Stack Auth
        print("... Calling Stack Auth ...")
        try:
            stack_user = create_stack_user(
                email=user_in.email, 
                password=user_in.password,
                display_name=user_in.display_name
            )
            stack_id = stack_user['id']
            print(f"✅ Stack Auth Created. ID: {stack_id}")
            
            # Timestamp logic
            signup_millis = stack_user.get('signed_up_at_millis')
            if signup_millis:
                created_dt = datetime.fromtimestamp(signup_millis / 1000.0, tz=timezone.utc)
            else:
                created_dt = datetime.now(timezone.utc)

        except Exception as e:
            print(f"❌ Stack Auth Failed: {e}")
            raise HTTPException(status_code=400, detail=f"Stack Error: {str(e)}")

        # 3. Create in Local DB
        print("... Saving to Postgres ...")
        try:
            new_local_user = User(
                stack_id=stack_id,
                email=user_in.email,
                display_name=user_in.display_name,
                is_verified=True, 
                created_at=created_dt,
           
            )
            db.add(new_local_user)
            db.commit()
            db.refresh(new_local_user)
            print("✅ Postgres Saved Successfully!")
            
            return {
                "message": "User created successfully", 
                "id": new_local_user.id
            }
            
        except Exception as e:
            db.rollback()
            print("❌ POSTGRES SAVE FAILED!")
            # THIS PRINTS THE REAL REASON TO YOUR TERMINAL
            traceback.print_exc() 
            raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

    except Exception as e:
        # Catch-all for anything else
        print("❌ CRITICAL UNHANDLED ERROR:")
        traceback.print_exc()
        raise e

@app.get("/users")
def get_all_users(db: requests.Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.get("/users/me")
def get_current_user(token: str = Depends(oauth2_scheme)):
    # 1. Debug: Print the raw token receiving from frontend/Swagger
    # print(f"Raw Token received in main: {token}") 

    # 2. Verify
    user_data = verify_stack_token(token)
    print(user_data.keys())
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token", # This matches the error in your screenshot
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Return User Object
    return User(
        stack_id=user_data.get("id"),
        email=user_data.get("primary_email"),
        display_name=user_data.get("display_name"),
        is_verified=user_data.get("primary_email_verified")
    )
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: requests.Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@app.post("/chat")
def talk_to_ai(
    chat_request: ChatRequest, 
    current_user: Annotated[User, Depends(get_current_user)]
):
    print(f"User {current_user.email} asking: {chat_request.prompt}")
    
    # 1. Get the user's custom instructions (if any)
    # The 'current_user' object comes from the DB, so it has the new field
    user_custom_prompt = current_user.custom_system_prompt
    
    # 2. Call LLM with the prompt AND the instruction
    ai_response = chat_with_local_model(
        prompt=chat_request.prompt, 
        system_instruction=user_custom_prompt, # <--- Passing it here
        model=chat_request.model
    )
    
    return {
        "user": current_user.email,
        "prompt": chat_request.prompt,
        "response": ai_response
    }

# OPTIONAL: Endpoint to UPDATE the custom prompt
class UpdateSystemPromptRequest(pydantic.BaseModel):
    system_prompt: str

@app.put("/users/me/system-prompt")
def update_my_prompt(
    body: UpdateSystemPromptRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    # Update the field
    current_user.custom_system_prompt = body.system_prompt
    db.commit()
    return {"message": "System prompt updated!", "new_prompt": current_user.custom_system_prompt}