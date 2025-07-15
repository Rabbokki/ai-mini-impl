from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    """글 상태 열거형"""
    PUBLISHED = "published"
    DELETED = "deleted"

class PostCreate(BaseModel):
    """글 작성 시 사용하는 모델"""
    title: str
    content: str
    author: str
    status: PostStatus = PostStatus.PUBLISHED
    
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
    
    @validator('author')
    def author_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError('작성자는 비어있을 수 없습니다')
        return v.strip()

class PostUpdate(BaseModel):
    """글 수정 시 사용하는 모델"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[PostStatus] = None
    
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



class PostListResponse(BaseModel):
    """글 목록 응답 시 사용하는 모델"""
    id: str
    title: str
    author: str
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    
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