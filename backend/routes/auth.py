from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.database import users
from datetime import datetime
from bson import ObjectId
from typing import Optional

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime

@router.post("/register")
async def register(user: UserCreate):
    # 사용자 중복 체크
    if users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다")
    
    # 새로운 사용자 데이터 생성
    new_user = {
        "username": user.username,
        "password": user.password,  # 실제 프로젝트에서는 반드시 암호화해야 합니다!
        "email": user.email,
        "created_at": datetime.utcnow()
    }
    
    # DB에 사용자 추가
    result = users.insert_one(new_user)
    
    return {"message": "회원가입이 완료되었습니다", "user_id": str(result.inserted_id)}

@router.get("/users")
async def get_all_users():
    """모든 사용자 조회"""
    all_users = list(users.find())
    user_list = []
    
    for user in all_users:
        user_data = {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"]
        }
        user_list.append(user_data)
    
    return {"users": user_list, "total_count": len(user_list)}

@router.get("/users/{user_id}")
async def get_user_by_id(user_id: str):
    """특정 사용자 조회 (ID로)"""
    try:
        # ObjectId 형식 확인
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="잘못된 사용자 ID 형식입니다")
        
        user = users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.get("/users/username/{username}")
async def get_user_by_username(username: str):
    """특정 사용자 조회 (username으로)"""
    user = users.find_one({"username": username})
    
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"]
    }

@router.put("/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate):
    """사용자 정보 수정"""
    try:
        # ObjectId 형식 확인
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="잘못된 사용자 ID 형식입니다")
        
        # 기존 사용자 확인
        existing_user = users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 업데이트할 데이터 준비 (None이 아닌 값만)
        update_data = {}
        if user_update.username is not None:
            # username 중복 체크 (다른 사용자와)
            duplicate_user = users.find_one({
                "username": user_update.username,
                "_id": {"$ne": ObjectId(user_id)}
            })
            if duplicate_user:
                raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")
            update_data["username"] = user_update.username
            
        if user_update.password is not None:
            update_data["password"] = user_update.password
            
        if user_update.email is not None:
            update_data["email"] = user_update.email
        
        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 데이터가 없습니다")
        
        # 수정일시 추가
        update_data["updated_at"] = datetime.utcnow()
        
        # 사용자 정보 업데이트
        result = users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="사용자 정보 수정에 실패했습니다")
        
        # 업데이트된 사용자 정보 반환
        updated_user = users.find_one({"_id": ObjectId(user_id)})
        return {
            "message": "사용자 정보가 수정되었습니다",
            "user": {
                "id": str(updated_user["_id"]) if updated_user and "_id" in updated_user else None,
                "username": updated_user["username"] if updated_user and "username" in updated_user else None,
                "email": updated_user["email"] if updated_user and "email" in updated_user else None,
                "created_at": updated_user["created_at"] if updated_user and "created_at" in updated_user else None,
                "updated_at": updated_user.get("updated_at") if updated_user else None
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
        # ObjectId 형식 확인
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="잘못된 사용자 ID 형식입니다")
        
        # 기존 사용자 확인
        existing_user = users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 사용자 삭제
        result = users.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="사용자 삭제에 실패했습니다")
        
        return {
            "message": "사용자가 삭제되었습니다",
            "deleted_user": {
                "id": str(existing_user["_id"]),
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
            "id": str(existing_user["_id"]),
            "username": existing_user["username"],
            "email": existing_user["email"]
        }
    }

