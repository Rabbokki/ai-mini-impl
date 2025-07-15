from pymongo import MongoClient
from datetime import datetime

try:
    # MongoDB 연결
    client = MongoClient('mongodb://localhost:27017/')
    db = client['mini_project']
    users = db['users']
    
    print("=== MongoDB 연결 성공 ===")
    
    # 모든 사용자 조회
    all_users = list(users.find())
    print(f"\n총 사용자 수: {len(all_users)}")
    
    print("\n=== 저장된 사용자 목록 ===")
    for i, user in enumerate(all_users, 1):
        print(f"{i}. Username: {user.get('username')}")
        print(f"   Email: {user.get('email')}")
        print(f"   가입일: {user.get('created_at')}")
        print(f"   ID: {user.get('_id')}")
        print("-" * 30)
    
    # 특정 사용자 검색 (testuser)
    test_user = users.find_one({"username": "testuser"})
    if test_user:
        print("\n=== 'testuser' 사용자 정보 ===")
        print(f"Username: {test_user.get('username')}")
        print(f"Email: {test_user.get('email')}")
        print(f"Password: {test_user.get('password')}")
        print(f"가입일: {test_user.get('created_at')}")
    else:
        print("\n'testuser' 사용자를 찾을 수 없습니다.")
        
except Exception as e:
    print(f"오류 발생: {e}")
    print("MongoDB가 실행중인지 확인해주세요.") 