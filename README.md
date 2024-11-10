# 🤗 AI 감정 케어 챗봇 '공감엔진'

## 📋 소개
공감엔진은 사용자의 감정을 분석하고 맞춤형 대화를 제공하는 AI 기반 심리 케어 챗봇입니다. RAG 아키텍처와 감정 분석을 통해 맥락을 이해하고 공감적인 대화를 제공하며, "누구나, 언제나, 어디서나" 접근할 수 있는 심리 케어 서비스를 지향합니다.

## 🚀 주요 기능
- 실시간 감정 분석 및 맞춤형 상담
- RAG 기반 맥락 이해 응답 생성
- 위기 상황 자동 감지 및 전문가 연계
- 위치 기반 상담센터 정보 제공
- 감정 변화 추적 및 시각화

## 🛠 기술 스택
- Frontend: Streamlit, Tailwind CSS
- Backend: Python, SQLite
- AI/ML: OpenAI GPT, SentenceTransformer, FAISS
- 외부 API: Kakao Maps API

## 📁 프로젝트 구조
```
├── app.py                 # 메인 애플리케이션
├── core/                  # 핵심 모듈
│   ├── data_processor.py  # 데이터 처리 모듈
│   ├── db_handler.py      # 데이터베이스 관리
│   ├── rag_engine.py      # RAG 엔진
│   └── summarizer.py      # 대화 요약 모듈
├── components/            # UI 컴포넌트
│   ├── emotion_analyzer.py # 감정 분석기
│   ├── location_service.py # 위치 서비스
│   ├── theme_manager.py   # 테마 관리
│   └── feedback_handler.py # 피드백 처리
├── requirements.txt       # 필요 패키지 목록
└── .streamlit/
    └── secrets.toml       # API 키 설정
```

## 🔧 설치 방법
1. 저장소 클론
```bash
git clone https://github.com/Elijahuni/CounsellingChatbot.git
cd CounsellingChatbot
```

2. 필요 패키지 설치
```bash
pip install -r requirements.txt
```

3. API 키 설정
```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "your-openai-api-key"
KAKAO_API_KEY = "your-kakao-api-key"
```

4. 실행
```bash
streamlit run app.py
```

## ⚠️ 주의사항
- API 키는 반드시 .streamlit/secrets.toml 파일에 설정해야 합니다
- 위치 서비스 사용을 위해 Kakao 개발자 계정이 필요합니다
- 실행 전 필요한 데이터 파일이 올바른 위치에 있는지 확인하세요
- 데이터 파일 구조:
  - data/total_kor_counsel_bot.jsonl(https://github.com/MrBananaHuman/CounselGPT)
  - data/total_kor_multiturn_counsel_bot.jsonl(https://github.com/MrBananaHuman/CounselGPT)
  - data/wellness.csv(AIHUB 웰니스 데이터셋)

## 📝 라이선스
This project is MIT licensed.

## 📞 연락처
프로젝트에 대한 문의나 제안사항이 있으시다면 Issues를 통해 연락주세요.

## 🙏 감사의 글
이 프로젝트는 수도권 ICT이노베이션 스퀘어의 AI 프로젝트 과정의 일환으로 진행되었습니다.
