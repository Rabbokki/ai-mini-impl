import requests
import json

# 회원가입 테스트
url = "http://localhost:8000/api/auth/register"
data = {
    "username": "testuser",
    "password": "testpassword",
    "email": "test@example.com"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}") 