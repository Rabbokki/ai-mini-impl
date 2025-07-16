import requests
import json
import time

# 서버 URL
base_url = "http://localhost:8000/api/auth"

print("🚀 로그인 시스템 테스트 시작\n")

# 1. 회원가입 테스트
print("1️⃣ 회원가입 테스트")
register_url = f"{base_url}/register"
register_data = {
    "username": "testuser123",
    "password": "securepassword123",
    "email": "testuser123@example.com"
}

try:
    register_response = requests.post(register_url, json=register_data)
    print(f"회원가입 상태코드: {register_response.status_code}")
    print(f"회원가입 응답: {register_response.json()}")
    
    if register_response.status_code == 200:
        print("✅ 회원가입 성공!")
    else:
        print("⚠️  회원가입 실패 또는 이미 존재하는 사용자")
        
except requests.exceptions.RequestException as e:
    print(f"❌ 회원가입 요청 오류: {e}")

print("\n" + "="*50 + "\n")

# 2. 로그인 테스트
print("2️⃣ 로그인 테스트")
login_url = f"{base_url}/login"
login_data = {
    "email": register_data["email"],
    "password": register_data["password"]
}

try:
    login_response = requests.post(login_url, json=login_data)
    print(f"로그인 상태코드: {login_response.status_code}")
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        print("✅ 로그인 성공!")
        print(f"액세스 토큰: {login_result['access_token'][:20]}...")
        print(f"토큰 타입: {login_result['token_type']}")
        print(f"사용자 정보:")
        print(f"  - ID: {login_result['user_info']['id']}")
        print(f"  - 사용자명: {login_result['user_info']['username']}")
        print(f"  - 이메일: {login_result['user_info']['email']}")
        print(f"  - 생성일: {login_result['user_info']['created_at']}")
        
        # 토큰 저장 (추가 테스트용)
        access_token = login_result['access_token']
        
    else:
        print("❌ 로그인 실패")
        print(f"오류 응답: {login_response.json()}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ 로그인 요청 오류: {e}")

print("\n" + "="*50 + "\n")

# 3. 잘못된 로그인 정보로 테스트
print("3️⃣ 잘못된 비밀번호로 로그인 테스트")
wrong_login_data = {
    "email": register_data["email"],
    "password": "wrongpassword"
}

try:
    wrong_login_response = requests.post(login_url, json=wrong_login_data)
    print(f"잘못된 로그인 상태코드: {wrong_login_response.status_code}")
    
    if wrong_login_response.status_code == 400:
        print("✅ 올바른 오류 처리: 잘못된 비밀번호 거부됨")
        print(f"오류 메시지: {wrong_login_response.json()['detail']}")
    else:
        print("⚠️  예상과 다른 응답")
        
except requests.exceptions.RequestException as e:
    print(f"❌ 요청 오류: {e}")

print("\n" + "="*50 + "\n")

# 4. 존재하지 않는 사용자로 로그인 테스트
print("4️⃣ 존재하지 않는 이메일로 로그인 테스트")
nonexistent_login_data = {
    "email": "nonexistent@example.com",
    "password": "anypassword"
}

try:
    nonexistent_response = requests.post(login_url, json=nonexistent_login_data)
    print(f"존재하지 않는 사용자 로그인 상태코드: {nonexistent_response.status_code}")
    
    if nonexistent_response.status_code == 400:
        print("✅ 올바른 오류 처리: 존재하지 않는 사용자 거부됨")
        print(f"오류 메시지: {nonexistent_response.json()['detail']}")
    else:
        print("⚠️  예상과 다른 응답")
        
except requests.exceptions.RequestException as e:
    print(f"❌ 요청 오류: {e}")

print("\n🎉 로그인 시스템 테스트 완료!") 