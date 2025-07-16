from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    """글 상태 열거형"""
    PUBLISHED = "published"
    DELETED = "deleted"

class ImageInfo(BaseModel):
    """이미지 정보 모델"""
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    upload_date: datetime

class PostCreate(BaseModel):
    """글 작성 시 사용하는 모델"""
    title: str
    content: str
    status: PostStatus = PostStatus.PUBLISHED
    images: Optional[List[str]] = []  # 임시 업로드된 이미지 파일명 리스트
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError('제목은 비어있을 수 없습니다')
        if len(v) > 100:
            raise ValueError('제목은 100자를 초과할 수 없습니다')
        return v.strip()
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError('내용은 비어있을 수 없습니다')
        return v.strip()
    
    @validator('images')
    def validate_images(cls, v):
        if v is None:
            return []
        if len(v) > 3:
            raise ValueError('이미지는 최대 3장까지 업로드할 수 있습니다')
        return v

class PostUpdate(BaseModel):
    """글 수정 시 사용하는 모델"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[PostStatus] = None
    images: Optional[List[str]] = None  # 수정할 이미지 파일명 리스트
    
    @validator('title')
    def title_validation(cls, v):
        if v is not None:
            if not v or v.strip() == "":
                raise ValueError('제목은 비어있을 수 없습니다')
            if len(v) > 100:
                raise ValueError('제목은 100자를 초과할 수 없습니다')
            return v.strip()
        return v
    
    @validator('content')
    def content_validation(cls, v):
        if v is not None:
            if not v or v.strip() == "":
                raise ValueError('내용은 비어있을 수 없습니다')
            return v.strip()
        return v
    
    @validator('images')
    def validate_images(cls, v):
        if v is not None and len(v) > 3:
            raise ValueError('이미지는 최대 3장까지 업로드할 수 있습니다')
        return v



class PostListResponse(BaseModel):
    """글 목록 응답 시 사용하는 모델"""
    id: str
    title: str
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    images: List[ImageInfo] = []  # 이미지 정보 목록
    
    class Config:
        from_attributes = True

class PostDetailResponse(BaseModel):
    """글 상세 조회 응답 모델"""
    id: str
    title: str
    content: str
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    images: List[ImageInfo] = []
    
    class Config:
        from_attributes = True

class PostCreateResponse(BaseModel):
    """글 작성 후 응답 모델"""
    message: str
    post_id: str

class PostUpdateResponse(BaseModel):
    """글 수정 후 응답 모델"""
    message: str
    post_id: str

class PostDeleteResponse(BaseModel):
    """글 삭제 후 응답 모델"""
    message: str
    post_id: str 

class ImageUploadResponse(BaseModel):
    """이미지 업로드 응답 모델"""
    message: str
    filename: str
    file_size: int

class ImageDeleteResponse(BaseModel):
    """이미지 삭제 응답 모델"""
    message: str
    filename: str 