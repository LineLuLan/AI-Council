from annotated_types import T
import requests
from config import settings

def stack_auth_request(method, endpoint, **kwargs):
  res = requests.request(
    method,
    f'https://api.stack-auth.com/{endpoint}',
    headers={
      'x-stack-access-type': 'server',
      # You should store these in environment variables
      'x-stack-project-id': settings.X_STACK_PROJECT_ID,
      'x-stack-publishable-client-key': settings.X_STACK_PUBLISHABLE_CLIENT_KEY,
      'x-stack-secret-server-key': settings.X_STACK_SECRET_SERVER_KEY,
      **kwargs.pop('headers', {}),
    },
    **kwargs,
  )
  if res.status_code >= 400:
    raise Exception(f"Stack Auth API request failed with {res.status_code}: {res.text}")
  return res.json()

def verify_stack_token(token: str):
    print(f"\n🔍 Verifying Token: {token[:10]}... (truncated)")

    url = 'https://api.stack-auth.com/api/v1/users/me'
    
    headers = {
        # CHANGE THIS: Use 'x-stack-access-token' instead of 'Authorization'
        'x-stack-access-token': token,
        
        # Keep identifying as the SERVER
        'x-stack-access-type': 'server',
        'x-stack-project-id': settings.X_STACK_PROJECT_ID,
        'x-stack-secret-server-key': settings.X_STACK_SECRET_SERVER_KEY,
        
        'Content-Type': 'application/json'
    }

    try:
        res = requests.get(url, headers=headers)
        
        # --- DEBUG LOGGING ---
        print(f"Stack API Status: {res.status_code}")
        
        if res.status_code == 200:
            user_data = res.json()
            # Handle potential response nesting
            final_user = user_data.get('user', user_data)
            print(f"✅ Token Valid! User: {final_user.get('email')}")
            return final_user
            
        else:
            print(f"❌ Token Rejected. Response: {res.text}")
            return None

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def create_stack_user(email: str, password: str, **kwargs):
    """
    Creates a new user in Stack Auth.
    Accepts extra fields like 'display_name' via **kwargs.
    """
    url = "https://api.stack-auth.com/api/v1/users"
    
    headers = {
        'x-stack-access-type': 'server',
        'x-stack-project-id': settings.X_STACK_PROJECT_ID,
        'x-stack-secret-server-key': settings.X_STACK_SECRET_SERVER_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "primary_email": email,
        "password": password,
        "primary_email_verified": True,
        "primary_email_auth_enabled": True,

        # This merges any extra arguments (like display_name) into the payload
        **kwargs 
    }

    try:
        res = requests.post(url, json=payload, headers=headers)
        
        if res.status_code in [200, 201]:
            return res.json()
        else:
            # Print error for debugging
            print(f"❌ Stack Create Error: {res.text}")
            raise Exception(f"Stack Auth Creation Failed: {res.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        raise e