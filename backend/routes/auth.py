
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from backend.database import users, get_next_user_id
from backend.auth_utils import get_password_hash, verify_password, create_access_token, verify_token
from datetime import datetime
from bson import ObjectId
from typing import Optional

router = APIRouter()

security = HTTPBearer()


class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    birth_date: str  # YYYY-MM-DD 형식으로 입력

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[str] = None  # YYYY-MM-DD 형식으로 입력
    is_subscribe: Optional[bool] = None  # 구독 상태 변경

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    birth_date: str
    is_subscribe: bool
    created_at: datetime

@router.post("/register")
async def register(user: UserCreate):
    # 사용자 중복 체크 (username과 email 모두 확인)
    if users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다")
    if users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다")
    
    # 패스워드 해싱
    hashed_password = get_password_hash(user.password)
    
    # 다음 단순 ID 생성
    simple_id = get_next_user_id()
    
    # 새로운 사용자 데이터 생성
    new_user = {
        "id": simple_id,  # 단순 숫자 ID (1, 2, 3, ...)
        "username": user.username,
        "password": hashed_password,  # 해싱된 패스워드 저장
        "email": user.email,
        "birth_date": user.birth_date,
        "is_subscribe": False,  # 회원가입 시 기본값은 구독하지 않음
        "created_at": datetime.utcnow()
    }
    
    # DB에 사용자 추가
    result = users.insert_one(new_user)
    
    return {"message": "회원가입이 완료되었습니다", "user_id": str(result.inserted_id)}


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    # 사용자 조회 (email로 검색)
    user = users.find_one({"email": user_credentials.email})
    if not user:
        raise HTTPException(
            status_code=400, 
            detail="이메일 또는 패스워드가 잘못되었습니다"
        )
    
    # 패스워드 검증
    if not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=400, 
            detail="이메일 또는 패스워드가 잘못되었습니다"
        )
    
    # JWT 토큰 생성 (email 기반)
    access_token = create_access_token(data={"sub": user["email"]})
    
    # 사용자 정보 (패스워드 제외)
    user_info = {
        "id": user.get("id", str(user["_id"])),  # 단순 ID 또는 기존 ObjectId
        "username": user["username"],
        "email": user["email"],
        "birth_date": user.get("birth_date", ""),
        "is_subscribe": user.get("is_subscribe", False),
        "created_at": user["created_at"]
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": user_info
    }

@router.get("/users")
async def get_all_users():
    """모든 사용자 조회"""
    all_users = list(users.find({}, {"password": 0}))  # 패스워드 제외하고 조회
    user_list = []
    
    for user in all_users:
        user_data = {
            "id": user.get("id", str(user["_id"])),
            "username": user["username"],
            "email": user["email"],
            "birth_date": user.get("birth_date", ""),
            "is_subscribe": user.get("is_subscribe", False),
            "created_at": user["created_at"]
        }
        user_list.append(user_data)
    
    return {"users": user_list, "total_count": len(user_list)}

@router.get("/users/{user_id}")
async def get_user_by_id(user_id: str):
    """특정 사용자 조회 (ID로)"""
    try:
        # 단순 숫자 ID로 먼저 검색
        try:
            simple_id = int(user_id)
            user = users.find_one({"id": simple_id})
        except ValueError:
            # 숫자가 아니면 ObjectId로 검색
            if ObjectId.is_valid(user_id):
                user = users.find_one({"_id": ObjectId(user_id)})
            else:
                user = None
        
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return {
            "id": user.get("id", str(user["_id"])),
            "username": user["username"],
            "email": user["email"],
            "birth_date": user.get("birth_date", ""),
            "is_subscribe": user.get("is_subscribe", False),
            "created_at": user["created_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.get("/users/username/{username}")
async def get_user_by_username(username: str):
    """특정 사용자 조회 (username으로)"""
    user = users.find_one({"username": username})
    
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return {
        "id": user.get("id", str(user["_id"])),
        "username": user["username"],
        "email": user["email"],
        "birth_date": user.get("birth_date", ""),
        "is_subscribe": user.get("is_subscribe", False),
        "created_at": user["created_at"]
    }

@router.put("/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate):
    """사용자 정보 수정"""
    try:
        # 단순 숫자 ID로 먼저 검색, 실패하면 ObjectId로 검색
        user_filter = None
        try:
            simple_id = int(user_id)
            user_filter = {"id": simple_id}
        except ValueError:
            if ObjectId.is_valid(user_id):
                user_filter = {"_id": ObjectId(user_id)}
            else:
                raise HTTPException(status_code=400, detail="잘못된 사용자 ID 형식입니다")
        
        # 기존 사용자 확인
        existing_user = users.find_one(user_filter)
        if not existing_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 업데이트할 데이터 준비 (None이 아닌 값만)
        update_data = {}
        if user_update.username is not None:
            # username 중복 체크 (다른 사용자와)
            if "id" in existing_user:
                duplicate_user = users.find_one({
                    "username": user_update.username,
                    "id": {"$ne": existing_user["id"]}
                })
            else:
                duplicate_user = users.find_one({
                    "username": user_update.username,
                    "_id": {"$ne": existing_user["_id"]}
                })
            
            if duplicate_user:
                raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")
            update_data["username"] = user_update.username
            
        if user_update.password is not None:
            # 패스워드 해싱
            update_data["password"] = get_password_hash(user_update.password)
            
        if user_update.email is not None:
            update_data["email"] = user_update.email
            
        if user_update.birth_date is not None:
            update_data["birth_date"] = user_update.birth_date
            
        if user_update.is_subscribe is not None:
            update_data["is_subscribe"] = user_update.is_subscribe
        
        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 데이터가 없습니다")
        
        # 수정일시 추가
        update_data["updated_at"] = datetime.utcnow()
        
        # 사용자 정보 업데이트
        result = users.update_one(user_filter, {"$set": update_data})
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="사용자 정보 수정에 실패했습니다")
        
        # 업데이트된 사용자 정보 반환
        updated_user = users.find_one(user_filter)
        if not updated_user:
            raise HTTPException(status_code=500, detail="업데이트 후 사용자 정보를 찾을 수 없습니다")
        
        return {
            "message": "사용자 정보가 수정되었습니다",
            "user": {
                "id": updated_user.get("id", str(updated_user["_id"])),
                "username": updated_user["username"],
                "email": updated_user["email"],
                "birth_date": updated_user.get("birth_date", ""),
                "is_subscribe": updated_user.get("is_subscribe", False),
                "created_at": updated_user["created_at"],
                "updated_at": updated_user.get("updated_at")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """사용자 삭제"""
    try:
        # 단순 숫자 ID로 먼저 검색, 실패하면 ObjectId로 검색
        user_filter = None
        try:
            simple_id = int(user_id)
            user_filter = {"id": simple_id}
        except ValueError:
            if ObjectId.is_valid(user_id):
                user_filter = {"_id": ObjectId(user_id)}
            else:
                raise HTTPException(status_code=400, detail="잘못된 사용자 ID 형식입니다")
        
        # 기존 사용자 확인
        existing_user = users.find_one(user_filter)
        if not existing_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 사용자 삭제
        result = users.delete_one(user_filter)
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="사용자 삭제에 실패했습니다")
        
        return {
            "message": "사용자가 삭제되었습니다",
            "deleted_user": {
                "id": existing_user.get("id", str(existing_user["_id"])),
                "username": existing_user["username"],
                "email": existing_user["email"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.delete("/users/username/{username}")
async def delete_user_by_username(username: str):
    """사용자 삭제 (username으로)"""
    # 기존 사용자 확인
    existing_user = users.find_one({"username": username})
    if not existing_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 사용자 삭제
    result = users.delete_one({"username": username})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="사용자 삭제에 실패했습니다")
    
    return {
        "message": "사용자가 삭제되었습니다",
        "deleted_user": {
            "id": existing_user.get("id", str(existing_user["_id"])),
            "username": existing_user["username"],
            "email": existing_user["email"]
        }
    }

