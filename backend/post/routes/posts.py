from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
import uuid

from models.post import (
    PostCreate, PostUpdate, PostListResponse,
    PostCreateResponse, PostUpdateResponse, PostDeleteResponse, PostStatus
)
from database.mongodb import get_mongodb

router = APIRouter(prefix="/posts", tags=["posts"])

# MongoDB 클라이언트 가져오기
mongodb = get_mongodb()

@router.post("/", response_model=PostCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post_data: PostCreate):
    """글 작성"""
    try:
        # MongoDB 연결 확인
        if not mongodb.check_connection():
            if not mongodb.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="데이터베이스 연결에 실패했습니다"
                )
        
        # 새로운 글 ID 생성
        post_id = str(uuid.uuid4())
        
        # 현재 시간
        current_time = datetime.now()
        
        # 글 데이터 저장
        new_post = {
            "id": post_id,
            "title": post_data.title,
            "content": post_data.content,
            "author": post_data.author,
            "status": post_data.status,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        # MongoDB 문서 생성 및 저장
        document = mongodb.create_post_document(new_post)
        collection = mongodb.get_posts_collection()
        result = collection.insert_one(document)
        
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="글 저장에 실패했습니다"
            )
        
        return PostCreateResponse(
            message="글이 성공적으로 작성되었습니다",
            post_id=post_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"글 작성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/", response_model=List[PostListResponse])
async def get_posts():
    """글 목록 조회"""
    try:
        # MongoDB 연결 확인
        if not mongodb.check_connection():
            if not mongodb.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="데이터베이스 연결에 실패했습니다"
                )
        
        collection = mongodb.get_posts_collection()
        
        # 게시된 글만 조회 (삭제되지 않은 글)
        query = {"status": {"$ne": PostStatus.DELETED}}
        cursor = collection.find(query).sort("created_at", -1)
        
        posts = []
        for doc in cursor:
            posts.append(PostListResponse(
                id=doc["post_id"],
                title=doc["title"],
                author=doc["author"],
                status=doc["status"],
                created_at=doc["created_at"],
                updated_at=doc["updated_at"]
            ))
        
        return posts
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"글 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )



@router.put("/{post_id}", response_model=PostUpdateResponse)
async def update_post(post_id: str, post_data: PostUpdate):
    """글 수정"""
    try:
        # MongoDB 연결 확인
        if not mongodb.check_connection():
            if not mongodb.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="데이터베이스 연결에 실패했습니다"
                )
        
        collection = mongodb.get_posts_collection()
        
        # 글 존재 여부 확인
        existing_post = collection.find_one({"post_id": post_id})
        if not existing_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 글을 찾을 수 없습니다"
            )
        
        # 삭제된 글은 수정 불가
        if existing_post["status"] == PostStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 글을 찾을 수 없습니다"
            )
        
        # 변경된 필드만 업데이트
        update_data = post_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now()
            
            result = collection.update_one(
                {"post_id": post_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="글 수정에 실패했습니다"
                )
        
        return PostUpdateResponse(
            message="글이 성공적으로 수정되었습니다",
            post_id=post_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"글 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{post_id}", response_model=PostDeleteResponse)
async def delete_post(post_id: str):
    """글 삭제"""
    try:
        # MongoDB 연결 확인
        if not mongodb.check_connection():
            if not mongodb.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="데이터베이스 연결에 실패했습니다"
                )
        
        collection = mongodb.get_posts_collection()
        
        # 글 존재 여부 확인
        existing_post = collection.find_one({"post_id": post_id})
        if not existing_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 글을 찾을 수 없습니다"
            )
        
        # 이미 삭제된 글인지 확인
        if existing_post["status"] == PostStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 글을 찾을 수 없습니다"
            )
        
        # 소프트 삭제 (상태만 변경)
        result = collection.update_one(
            {"post_id": post_id},
            {"$set": {
                "status": PostStatus.DELETED,
                "updated_at": datetime.now()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="글 삭제에 실패했습니다"
            )
        
        return PostDeleteResponse(
            message="글이 성공적으로 삭제되었습니다",
            post_id=post_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"글 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """헬스 체크"""
    try:
        if not mongodb.check_connection():
            mongodb.connect()
        
        collection = mongodb.get_posts_collection()
        total_posts = collection.count_documents({})
        published_posts = collection.count_documents({"status": PostStatus.PUBLISHED})
        
        return {
            "status": "healthy", 
            "database": "connected",
            "total_posts": total_posts,
            "published_posts": published_posts
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        } 