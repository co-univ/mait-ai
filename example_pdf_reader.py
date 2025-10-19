#!/usr/bin/env python3
"""
PDF 파일 읽기 예제 스크립트

이 스크립트는 로컬 PDF 파일을 읽어서 텍스트 내용을 출력합니다.
"""

from app.utils.utils import read_pdf_file
import sys

def main():
    # 사용 예제 1: 파일 경로를 직접 지정
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # 기본 경로 (원하는 PDF 파일 경로로 변경하세요)
        pdf_path = "sample.pdf"
        print(f"사용법: python example_pdf_reader.py <PDF파일경로>")
        print(f"기본 파일 경로 사용: {pdf_path}\n")
    
    try:
        # PDF 파일 읽기
        print(f"📄 PDF 파일을 읽는 중: {pdf_path}")
        text_content = read_pdf_file(pdf_path)
        
        # 결과 출력
        print("\n" + "="*50)
        print("추출된 텍스트 내용:")
        print("="*50)
        print(text_content)
        print("="*50)
        print(f"\n✅ 총 {len(text_content)} 글자를 추출했습니다.")
        
    except FileNotFoundError as e:
        print(f"❌ 오류: {e}")
        print("파일 경로를 확인해주세요.")
    except ValueError as e:
        print(f"❌ 오류: {e}")
    except Exception as e:
        print(f"❌ PDF 파싱 중 오류 발생: {e}")

if __name__ == "__main__":
    main()

