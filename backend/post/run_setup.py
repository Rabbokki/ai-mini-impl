#!/usr/bin/env python3
"""
MongoDB + FastAPI 빠른 설정 및 실행 스크립트

사용법:
    python run_setup.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """명령어 실행"""
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] {description} 완료")
            return True
        else:
            print(f"[ERROR] {description} 실패: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] {description} 중 오류: {e}")
        return False

def check_mongodb():
    """MongoDB 연결 확인"""
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        client.close()
        return True
    except:
        return False

def main():
    """메인 함수"""
    print("Mini Blog API 빠른 설정을 시작합니다!\n")
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"현재 디렉토리: {current_dir}\n")
    
    # 1. MongoDB 상태 확인
    print("1. MongoDB 상태 확인")
    if check_mongodb():
        print("[OK] MongoDB 연결 성공")
    else:
        print("[ERROR] MongoDB 연결 실패")
        print("\nMongoDB를 설치하고 실행해주세요:")
        print("   Windows: net start MongoDB")
        print("   macOS: brew services start mongodb-community")
        print("   Docker: docker run -d --name mongodb -p 27017:27017 mongo:latest")
        
        response = input("\nMongoDB를 실행했나요? (y/N): ")
        if response.lower() != 'y':
            print("MongoDB를 실행한 후 다시 시도해주세요.")
            sys.exit(1)
    
    # 2. 의존성 설치 확인
    print("\n2. Python 의존성 확인")
    try:
        import fastapi, pymongo, uvicorn
        print("[OK] 필수 의존성 확인 완료")
    except ImportError as e:
        print(f"[ERROR] 의존성 부족: {e}")
        print("pip install -r ../../../requirements.txt 를 실행해주세요.")
        sys.exit(1)
    
    # 3. 데이터베이스 초기화
    print("\n3. 데이터베이스 초기화")
    db_init_path = "database/init_db.py"
    if os.path.exists(db_init_path):
        if run_command(f"python {db_init_path}", "데이터베이스 초기화"):
            print("[OK] 데이터베이스 설정 완료")
        else:
            print("[WARNING] 데이터베이스 초기화에 문제가 있지만 계속 진행합니다.")
    else:
        print(f"[ERROR] {db_init_path} 파일을 찾을 수 없습니다.")
    
    # 4. FastAPI 실행 옵션
    print("\n4. FastAPI 실행")
    print("다음 중 선택하세요:")
    print("   1. 바로 실행 (자동)")
    print("   2. 수동 실행 안내")
    
    choice = input("선택 (1 또는 2): ").strip()
    
    if choice == "1":
        print("\nFastAPI 애플리케이션을 실행합니다...")
        print("API 문서: http://localhost:8000/docs")
        print("종료하려면 Ctrl+C를 누르세요\n")
        
        try:
            # app.py 실행
            subprocess.run([sys.executable, "app.py"], check=True)
        except KeyboardInterrupt:
            print("\n[OK] 애플리케이션이 정상적으로 종료되었습니다.")
        except FileNotFoundError:
            print("[ERROR] app.py 파일을 찾을 수 없습니다.")
            print("현재 디렉토리에 app.py가 있는지 확인해주세요.")
    
    else:
        print("\n수동 실행 방법:")
        print("   1. 터미널에서 다음 명령어를 실행하세요:")
        print("      python app.py")
        print("   2. 브라우저에서 다음 주소로 접속하세요:")
        print("      http://localhost:8000/docs")
        print("   3. API 테스트를 시작하세요!")
    
    print("\n설정이 완료되었습니다!")

if __name__ == "__main__":
    main() 