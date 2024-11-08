# 🤗 AI 심리 상담 챗봇 공감엔진

## 📌 프로젝트 소개
'공감 엔진'은 RAG(Retrieval-Augmented Generation)와 OpenAI GPT를 활용한 AI 심리 상담 챗봇입니다. 사용자의 감정을 이해하고 공감적인 대화를 통해 심리적 지원을 제공합니다.

## ⚙️ 주요 기능
- 💭 맥락 기반 상담 대화
- 😊 실시간 감정 상태 분석
- 🚨 위기 상황 감지 및 전문가 연계
- 📍 주변 상담센터 찾기
- 💾 상담 내용 저장 및 관리

## 🛠️ 기술 스택
- **Frontend**: Streamlit
- **AI/ML**: OpenAI GPT, SentenceTransformer
- **Database**: SQLite
- **APIs**: Kakao Maps API
- **기타**: FAISS, Folium

## 🚀 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/Elijahuni/CounsellingChatbot.git
cd CounsellingChatbot
```

2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

4. 환경변수 설정
- `.streamlit` 폴더 생성
- `secrets.toml` 파일 생성 및 API 키 설정
```toml
OPENAI_API_KEY = "your-openai-api-key"
KAKAO_API_KEY = "your-kakao-api-key"
```

5. 실행
```bash
streamlit run app.py
```

## 📁 프로젝트 구조
```
counsellingchatbot/
├── app.py                  # 메인 애플리케이션
├── data_processor.py       # 데이터 처리 모듈
├── db_handler.py          # 데이터베이스 관리
├── rag_engine.py          # RAG 엔진
├── location_service.py    # 위치 서비스
├── requirements.txt       # 필요 패키지 목록
└── .streamlit/
    └── secrets.toml       # API 키 설정
```

## ⚠️ 주의사항
- API 키는 반드시 .streamlit/secrets.toml 파일에 설정해야 합니다
- 위치 서비스 사용을 위해 Kakao 개발자 계정이 필요합니다
- 실행 전 필요한 데이터 파일이 올바른 위치에 있는지 확인하세요

## 📝 라이선스
This project is MIT licensed.

---
## 📞 연락처
프로젝트에 대한 문의나 제안사항이 있으시다면 Issues를 통해 연락주세요.

## 🙏 감사의 글
이 프로젝트는 [교육 기관/과정명]의 일환으로 진행되었습니다.
