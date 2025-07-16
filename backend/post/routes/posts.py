from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import List
from datetime import datetime
import uuid
import os

from models.post import (
    PostCreate, PostUpdate, PostListResponse, PostDetailResponse,
    PostCreateResponse, PostUpdateResponse, PostDeleteResponse, PostStatus,
    ImageUploadResponse, ImageDeleteResponse, ImageInfo
)
from database.mongodb import get_mongodb
from utils.image_utils import image_utils

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
        
        collection = mongodb.get_posts_collection()
        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="데이터베이스 컬렉션을 가져올 수 없습니다"
            )
        
        # 새로운 글 ID 생성
        post_id = str(uuid.uuid4())
        
        # 현재 시간
        current_time = datetime.now()
        
        # 이미지 처리
        images_info = []
        if post_data.images:
            for temp_filename in post_data.images:
                try:
                    # 임시 파일을 정식 업로드 폴더로 이동
                    permanent_filename = image_utils.move_temp_to_permanent(temp_filename, post_id)
                    
                    # 이미지 정보 저장
                    file_info = image_utils.get_file_info(permanent_filename)
                    images_info.append({
                        "filename": permanent_filename,
                        "original_filename": temp_filename,
                        "file_path": os.path.join("uploads/images", permanent_filename),
                        "file_size": file_info["file_size"] if file_info else 0,
                        "upload_date": current_time
                    })
                except HTTPException:
                    # 임시 파일 이동 실패 시 다른 임시 파일들 정리
                    for temp_file in post_data.images:
                        image_utils.delete_temp_file(temp_file)
                    raise
        
        # 글 데이터 저장
        new_post = {
            "id": post_id,
            "title": post_data.title,
            "content": post_data.content,
            "status": post_data.status,
            "images": images_info,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        # MongoDB 문서 생성 및 저장
        document = mongodb.create_post_document(new_post)
        result = collection.insert_one(document)
        
        if not result.inserted_id:
            # 저장 실패 시 업로드된 이미지들 삭제
            for img_info in images_info:
                image_utils.delete_permanent_file(img_info["filename"])
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
        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="데이터베이스 컬렉션을 가져올 수 없습니다"
            )
        
        # 게시된 글만 조회 (삭제되지 않은 글)
        query = {"status": {"$ne": PostStatus.DELETED}}
        cursor = collection.find(query).sort("created_at", -1)
        
        posts = []
        for doc in cursor:
            # 이미지 정보 변환
            images = []
            for img_data in doc.get("images", []):
                images.append(ImageInfo(
                    filename=img_data["filename"],
                    original_filename=img_data["original_filename"],
                    file_path=img_data["file_path"],
                    file_size=img_data["file_size"],
                    upload_date=img_data["upload_date"]
                ))
            
            posts.append(PostListResponse(
                id=doc["post_id"],
                title=doc["title"],
                status=doc["status"],
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
                images=images
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

@router.post("/images/upload", response_model=ImageUploadResponse)
async def upload_temp_image(file: UploadFile = File(...)):
    """임시 이미지 업로드 (최대 3장, 5MB 제한)"""
    try:
        # 임시 폴더에 이미지 저장
        temp_filename, file_size = await image_utils.save_temp_image(file)
        
        return ImageUploadResponse(
            message="이미지가 임시로 업로드되었습니다",
            filename=temp_filename,
            file_size=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 업로드 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/images/temp/{filename}", response_model=ImageDeleteResponse)
async def delete_temp_image(filename: str):
    """임시 이미지 삭제 (업로드 취소)"""
    try:
        image_utils.delete_temp_file(filename)
        
        return ImageDeleteResponse(
            message="임시 이미지가 삭제되었습니다",
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{post_id}", response_model=PostDetailResponse)
async def get_post_detail(post_id: str):
    """글 상세 조회"""
    try:
        # MongoDB 연결 확인
        if not mongodb.check_connection():
            if not mongodb.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="데이터베이스 연결에 실패했습니다"
                )
        
        collection = mongodb.get_posts_collection()
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="데이터베이스 컬렉션을 가져올 수 없습니다"
            )
        
        # 글 조회
        post_doc = collection.find_one({"post_id": post_id})
        if not post_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 글을 찾을 수 없습니다"
            )
        
        # 삭제된 글은 조회 불가
        if post_doc["status"] == PostStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 글을 찾을 수 없습니다"
            )
        
        # 이미지 정보 변환
        images = []
        for img_data in post_doc.get("images", []):
            images.append(ImageInfo(
                filename=img_data["filename"],
                original_filename=img_data["original_filename"],
                file_path=img_data["file_path"],
                file_size=img_data["file_size"],
                upload_date=img_data["upload_date"]
            ))
        
        return PostDetailResponse(
            id=post_doc["post_id"],
            title=post_doc["title"],
            content=post_doc["content"],
            status=post_doc["status"],
            created_at=post_doc["created_at"],
            updated_at=post_doc["updated_at"],
            images=images
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"글 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """헬스 체크"""
    try:
        if not mongodb.check_connection():
            mongodb.connect()
        
        collection = mongodb.get_posts_collection()
        if not collection:
            return {
                "status": "unhealthy", 
                "database": "collection_error",
                "error": "컬렉션을 가져올 수 없습니다"
            }
        
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