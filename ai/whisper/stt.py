import whisper
import torch
import numpy as np

def load_model(model_name="tiny"):
    """
    Whisper 모델을 로드합니다.
    Args:
        model_name (str): 모델 크기 (tiny, base, small, medium, large)
    Returns:
        model: 로드된 Whisper 모델
    """
    return whisper.load_model(model_name)

def transcribe_audio(audio_path, model=None):
    """
    오디오 파일을 텍스트로 변환합니다.
    Args:
        audio_path (str): 오디오 파일 경로
        model: Whisper 모델 (기본값: None)
    Returns:
        str: 변환된 텍스트
    """
    if model is None:
        model = load_model()
    
    # 오디오 파일을 텍스트로 변환
    result = model.transcribe(audio_path)
    return result["text"]

def main():
    # 예제 실행
    print("Whisper STT 예제를 실행합니다...")
    
    # 모델 로드
    print("Whisper tiny 모델을 로드합니다...")
    model = load_model("tiny")
    
    # 오디오 파일 경로 설정 (예제)
    audio_path = "example.mp3"  # 실제 오디오 파일 경로로 변경해주세요
    
    try:
        # 오디오 파일 변환
        print(f"오디오 파일을 변환합니다: {audio_path}")
        text = transcribe_audio(audio_path, model)
        
        print("\n변환 결과:")
        print("-" * 50)
        print(text)
        print("-" * 50)
        
    except FileNotFoundError:
        print(f"오류: 오디오 파일을 찾을 수 없습니다: {audio_path}")
    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()


