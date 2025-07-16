import os
import uuid
import shutil
from typing import List, Optional
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from pathlib import Path
import aiofiles

# 설정값
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
UPLOAD_DIR = "uploads/images"
TEMP_DIR = "uploads/temp"

class ImageUtils:
    """이미지 관련 유틸리티 클래스"""
    
    def __init__(self):
        # 업로드 디렉토리 생성
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> bool:
        """이미지 파일 유효성 검사"""
        # 파일명 확인
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="파일명이 없습니다"
            )
        
        # 파일 확장자 확인
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 파일 크기 확인 (임시 파일로 읽어서 체크)
        if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 허용됩니다."
            )
        
        return True
    
    @staticmethod
    async def save_temp_image(file: UploadFile) -> tuple[str, int]:
        """임시 폴더에 이미지 저장"""
        # 파일 유효성 검사
        ImageUtils.validate_image_file(file)
        
        # 파일명이 유효성 검사를 통과했으므로 안전하게 사용
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="파일명이 없습니다"
            )
        
        # 고유한 파일명 생성
        file_extension = Path(file.filename).suffix.lower()
        temp_filename = f"{uuid.uuid4()}{file_extension}"
        temp_file_path = os.path.join(TEMP_DIR, temp_filename)
        
        # 파일 저장 및 크기 체크
        file_size = 0
        try:
            async with aiofiles.open(temp_file_path, 'wb') as buffer:
                while chunk := await file.read(1024):  # 1KB씩 읽기
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        # 파일이 너무 크면 삭제하고 예외 발생
                        await buffer.close()
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 허용됩니다."
                        )
                    await buffer.write(chunk)
            
            return temp_filename, file_size
            
        except HTTPException:
            raise
        except Exception as e:
            # 에러 발생 시 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"파일 저장 중 오류가 발생했습니다: {str(e)}"
            )
    
    @staticmethod
    def move_temp_to_permanent(temp_filename: str, post_id: str) -> str:
        """임시 파일을 정식 업로드 폴더로 이동"""
        temp_file_path = os.path.join(TEMP_DIR, temp_filename)
        
        if not os.path.exists(temp_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="임시 파일을 찾을 수 없습니다"
            )
        
        # 정식 파일명 생성 (post_id 포함)
        file_extension = Path(temp_filename).suffix
        permanent_filename = f"{post_id}_{temp_filename}"
        permanent_file_path = os.path.join(UPLOAD_DIR, permanent_filename)
        
        try:
            shutil.move(temp_file_path, permanent_file_path)
            return permanent_filename
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"파일 이동 중 오류가 발생했습니다: {str(e)}"
            )
    
    @staticmethod
    def delete_temp_file(temp_filename: str):
        """임시 파일 삭제"""
        temp_file_path = os.path.join(TEMP_DIR, temp_filename)
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                print(f"임시 파일 삭제 중 오류: {e}")
    
    @staticmethod
    def delete_permanent_file(filename: str):
        """정식 업로드 파일 삭제"""
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                print(f"파일 삭제 중 오류: {e}")
                return False
        return False
    
    @staticmethod
    def get_file_info(filename: str) -> Optional[dict]:
        """파일 정보 반환"""
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            return {
                "filename": filename,
                "file_path": file_path,
                "file_size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime)
            }
        return None
    
    @staticmethod
    def cleanup_temp_files(max_age_hours: int = 24):
        """오래된 임시 파일들 정리"""
        current_time = datetime.now()
        temp_dir = Path(TEMP_DIR)
        
        if not temp_dir.exists():
            return
        
        for file_path in temp_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age.total_seconds() > max_age_hours * 3600:
                    try:
                        file_path.unlink()
                        print(f"정리된 임시 파일: {file_path.name}")
                    except Exception as e:
                        print(f"임시 파일 정리 중 오류: {e}")

# 전역 유틸리티 인스턴스
image_utils = ImageUtils() 