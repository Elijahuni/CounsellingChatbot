# app.py

import streamlit as st
import json
import pandas as pd
import os

# 핵심 모듈 import
from core.data_processor import DataProcessor
from core.rag_engine import RAGEngine
from core.db_handler import DatabaseHandler
from core.summarizer import ChatSummarizer

# 컴포넌트 import
from components.location_service import LocationService
from components.emotion_analyzer import EmotionAnalyzer
from components.theme_manager import ThemeManager
from components.feedback_handler import FeedbackHandler

# 페이지 설정
st.set_page_config(
    page_title="AI 감정 케어 챗봇 공감엔진",
    page_icon="🤗",
    layout="wide"
)

# 데이터 프로세서 및 RAG 엔진 초기화
@st.cache_resource(show_spinner=True)
def initialize_rag():
    try:
        # 현재 작업 디렉토리 확인
        current_dir = os.getcwd()
        st.write(f"현재 작업 디렉토리: {current_dir}")
        
        data_processor = DataProcessor()
        
        # 데이터 파일 경로 설정
        single_turn_file = "data/total_kor_counsel_bot.jsonl"
        multi_turn_file = "data/total_kor_multiturn_counsel_bot.jsonl"
        wellness_file = "data/wellness.csv"
        
        # data 디렉토리 존재 확인
        data_dir = "data"
        if not os.path.exists(data_dir):
            st.error(f"데이터 디렉토리를 찾을 수 없습니다: {data_dir}")
            return None
            
        # 데이터 디렉토리 내용 확인
        st.write("데이터 디렉토리 내용:")
        st.write(os.listdir(data_dir))
        
        # 파일 존재 및 권한 확인
        for file_path in [single_turn_file, multi_turn_file, wellness_file]:
            exists = os.path.exists(file_path)
            readable = os.access(file_path, os.R_OK) if exists else False
            st.write(f"파일: {file_path}")
            st.write(f"  - 존재 여부: {exists}")
            st.write(f"  - 읽기 권한: {readable}")
            if exists:
                file_size = os.path.getsize(file_path)
                st.write(f"  - 파일 크기: {file_size:,} bytes")

        # Initialize counseling_data list if not exists
        if not hasattr(data_processor, 'counseling_data') or not data_processor.counseling_data:
            data_processor.counseling_data = []
            
            # 싱글턴 데이터 로드
            if os.path.exists(single_turn_file):
                try:
                    with open(single_turn_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        progress_bar = st.progress(0)
                        
                        for i, line in enumerate(lines):
                            try:
                                data = json.loads(line.strip())
                                data_processor.counseling_data.append({
                                    'input': data['input'],
                                    'output': data['output'],
                                    'type': 'single'
                                })
                                progress_bar.progress((i + 1) / len(lines))
                            except json.JSONDecodeError:
                                st.warning(f"JSON 파싱 오류 (라인 {i+1})")
                                continue
                    st.success(f"싱글턴 데이터 로드 완료: {sum(1 for d in data_processor.counseling_data if d['type'] == 'single')}개")
                except Exception as e:
                    st.error(f"싱글턴 데이터 로드 중 오류: {str(e)}")

            # 멀티턴 데이터 로드
            if os.path.exists(multi_turn_file):
                try:
                    with open(multi_turn_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines:
                            try:
                                dialogue_data = json.loads(line.strip())
                                if isinstance(dialogue_data, list):
                                    processed_input = ""
                                    processed_output = ""
                                    current_speaker = None
                                    current_utterance = ""
                                    
                                    for turn in dialogue_data:
                                        speaker = turn.get('speaker', '')
                                        utterance = turn.get('utterance', '')
                                        
                                        if current_speaker and current_speaker != speaker:
                                            if current_speaker == "내담자":
                                                processed_input += f"{current_utterance}\n"
                                            else:
                                                processed_output += f"{current_utterance}\n"
                                            current_utterance = f"{utterance}"
                                        else:
                                            current_utterance += f" {utterance}"
                                        
                                        current_speaker = speaker
                                    
                                    if current_speaker == "내담자":
                                        processed_input += f"{current_utterance}\n"
                                    else:
                                        processed_output += f"{current_utterance}\n"
                                    
                                    if processed_input.strip() and processed_output.strip():
                                        data_processor.counseling_data.append({
                                            'input': processed_input.strip(),
                                            'output': processed_output.strip(),
                                            'type': 'multi'
                                        })
                            except (json.JSONDecodeError, KeyError) as e:
                                st.warning(f"멀티턴 데이터 파싱 오류: {str(e)}")
                                continue
                    
                    st.success(f"멀티턴 데이터 로드 완료: {sum(1 for d in data_processor.counseling_data if d['type'] == 'multi')}개")
                except Exception as e:
                    st.error(f"멀티턴 데이터 로드 중 오류: {str(e)}")

            # Wellness 데이터 로드
            if os.path.exists(wellness_file):
                try:
                    wellness_df = pd.read_csv(wellness_file, encoding='utf-8')
                    
                    if '유저' in wellness_df.columns and '챗봇' in wellness_df.columns:
                        for _, row in wellness_df.iterrows():
                            if pd.notna(row['유저']) and pd.notna(row['챗봇']):
                                data_processor.counseling_data.append({
                                    'input': str(row['유저']).strip(),
                                    'output': str(row['챗봇']).strip(),
                                    'type': 'wellness',
                                    'category': row.get('구분', '')
                                })
                        
                        wellness_count = sum(1 for d in data_processor.counseling_data if d['type'] == 'wellness')
                        if wellness_count > 0:
                            st.success(f"Wellness 데이터 로드 완료: {wellness_count}개")
                        else:
                            st.warning("유효한 Wellness 데이터가 없습니다.")
                    else:
                        st.warning("CSV 파일의 필수 컬럼(유저, 챗봇)이 없습니다.")
                        
                except Exception as e:
                    st.warning(f"Wellness 데이터 로드 중 오류: {str(e)}")
                    st.write("CSV 파일 구조를 확인해주세요. (필요한 컬럼: 구분, 유저, 챗봇)")

            # FAISS 인덱스 처리
            if os.path.exists("data/faiss_index.idx"):
                data_processor.load_index("data/faiss_index.idx")
                st.success("기존 인덱스 로드 완료")
            else:
                if data_processor.create_embeddings():
                    data_processor.save_index("data/faiss_index.idx")
                    st.success("새 인덱스 생성 완료")
                else:
                    st.error("인덱스 생성 실패")
                    return None

            # 데이터 로드 상태 표시
            total_data = len(data_processor.counseling_data)
            single_turn_count = sum(1 for d in data_processor.counseling_data if d.get('type') == 'single')
            multi_turn_count = sum(1 for d in data_processor.counseling_data if d.get('type') == 'multi')
            wellness_count = sum(1 for d in data_processor.counseling_data if d.get('type') == 'wellness')
            
            st.success(f"""
            📊 데이터 현황:
            - 싱글턴 데이터: {single_turn_count}개
            - 멀티턴 데이터: {multi_turn_count}개
            - Wellness 데이터: {wellness_count}개
            - 총 데이터: {total_data}개
            """)

        # OPENAI_API_KEY 확인
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            st.error("OPENAI_API_KEY가 설정되지 않았습니다.")
            return None

        # RAG 엔진 초기화
        rag_engine = RAGEngine(data_processor, api_key)
        st.success("RAG 엔진 초기화 완료")
        
        return rag_engine
        
    except Exception as e:
        st.error(f"초기화 중 오류 발생: {str(e)}")
        import traceback
        st.error(f"상세 오류: {traceback.format_exc()}")
        return None

# 위험 상황 감지 함수
def detect_crisis(text: str) -> bool:
    crisis_keywords = [
        # 자해/자살 관련
        '자살', '죽고싶다', '죽을래', '자해', '죽고'
        # 폭력 관련
        '살인', '살해', '타살', '학대',
        # 위험 도구 관련
        '농약', '수면제', '청산가리',
        # 극단적 상황
        '목숨', '유서', '시체',
        # 심각한 범죄
        '마약', '폭행', '성폭력', '감금'
        # 극단적 감정
        '절망', '비참', '끔찍', '고통스럽다'
    ]
    return any(keyword in text for keyword in crisis_keywords)

# 위기 상황 리소스 생성 함수
def get_crisis_information(location_data=None, location_service=None):
    """위기 상황 시 제공할 정보 생성"""
    # 기본 위기 정보
    crisis_info = """
🚨 전문가의 도움이 필요해 보입니다.

긴급 연락처:
📞 자살예방상담전화: 1393
📞 정신건강상담전화: 1577-0199
"""
    
    # 위치 기반 상담센터 정보 추가
    if location_service:
        try:
            # IP 기반 위치 정보 가져오기를 시도하고, 실패하면 서울 중심부 좌표 사용
            default_location = {
                "lat": 37.5665,  # 서울시청 좌표
                "lon": 126.9780,
                "address": "서울시청"
            }
            location = location_data if location_data else default_location
            
            centers = location_service.find_nearby_counseling_centers(location)
            if centers:
                crisis_info += "\n\n가까운 상담센터 정보:"
                # 가장 가까운 3개 상담센터만 표시
                for center in centers[:3]:
                    crisis_info += f"""
🏥 {center['name']}
   📍 주소: {center['address']}
   📞 전화: {center['phone']}
   🚶 거리: {center['distance']}"""
                
                crisis_info += "\n\n💡 더 정확한 위치의 상담센터를 찾으려면 사이드바의 '주변 상담센터 찾기'에서 위치를 입력해주세요."
        except Exception as e:
            print(f"상담센터 정보 조회 중 오류: {str(e)}")
            crisis_info += "\n\n💡 사이드바의 '주변 상담센터 찾기'에서 위치를 입력하시면 가까운 상담센터를 확인하실 수 있습니다."
    
    return crisis_info

def main():
    # 데이터베이스 핸들러 초기화
    if 'db_handler' not in st.session_state:
        st.session_state.db_handler = DatabaseHandler()
    # 컴포넌트 초기화
    if 'components' not in st.session_state:
        st.session_state.components = {
            'emotion_analyzer': EmotionAnalyzer(),
            'theme_manager': ThemeManager(),
            'location_service': LocationService(),
            'feedback_handler': FeedbackHandler(st.session_state.db_handler)
        }
    # 세션 상태 초기화
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.messages = []
        st.session_state.emotion_result = None  # emotion_result 초기화
        st.session_state.current_session_id = st.session_state.db_handler.create_session()

    # 테마 적용 (기본 테마)
    st.session_state.components['theme_manager'].apply_theme('중립')
    
    # RAG 엔진 초기화
    if not st.session_state.initialized:
        with st.spinner("시스템을 초기화하는 중..."):
            rag_engine = initialize_rag()
            if rag_engine:
                st.session_state.rag_engine = rag_engine
                st.session_state.initialized = True
            else:
                st.error("시스템 초기화에 실패했습니다.")
                return
    
    # 제목
    st.title("🤗 AI 감정 케어 챗봇 공감엔진")
    st.write("안녕하세요! 저는 AI 감정 케어 챗봇 공감엔진입니다.")
    st.write("기쁜 일이든 힘든 일이든, 마음속 이야기를 편하게 나눠보세요. 저는 언제나 당신의 이야기를 들을 준비가 되어 있습니다.")
    st.write("무엇이든 부담 없이 이야기해 주세요!")

    # 채팅 이력 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input("고민이나 감정을 이야기해주세요..."):
         # 1. 감정 분석 수행
        emotion_result = st.session_state.components['emotion_analyzer'].analyze_emotion(prompt)
        st.session_state.emotion_result = emotion_result
        
        # 2. 감정 결과 추출
        emotion_detected = emotion_result.get('dominant_emotion') if emotion_result else None
        
        # 3. 위기 상황 감지
        crisis_detected = detect_crisis(prompt)
        
        # 4. 사용자 메시지 저장
        message_id = st.session_state.db_handler.save_message(
            session_id=st.session_state.current_session_id,
            role="user",
            content=prompt,
            emotion_detected=emotion_detected,
            crisis_detected=crisis_detected
        )
        
        # 5. 감정에 따른 테마 적용
        if emotion_detected:
            st.session_state.components['theme_manager'].apply_theme(emotion_detected)
        
        # 6. 메시지 목록에 추가
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "emotion_detected": emotion_detected,
            "crisis_detected": crisis_detected
        })
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 7. 챗봇 응답 생성
        if crisis_detected:
            # 위기 상황 처리
            location_service = st.session_state.components['location_service']
            location_data = location_service.get_current_location_by_ip()
            crisis_info = get_crisis_information(location_data, location_service)
            response = f"{st.session_state.rag_engine.get_response(prompt, st.session_state.messages)}\n\n{crisis_info}"
        else:
            response = st.session_state.rag_engine.get_response(prompt, st.session_state.messages)
        
        # 8. 어시스턴트 메시지 저장
        st.session_state.db_handler.save_message(
            session_id=st.session_state.current_session_id,
            role="assistant",
            content=response,
            emotion_detected=None,  # 챗봇 응답은 감정 분석하지 않음
            crisis_detected=crisis_detected
        )
        
        # 9. 어시스턴트 메시지 표시
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "emotion_detected": None,
            "crisis_detected": crisis_detected
        })
        with st.chat_message("assistant"):
            st.markdown(response)
            
            # 마지막 인사를 포함하는 응답인 경우 요약본 생성
            if "함께 이야기 나눌 수 있어 좋았습니다" in response:
                # 요약 생성기 초기화
                summarizer = ChatSummarizer(st.secrets["OPENAI_API_KEY"])
                
                # 대화 요약 생성
                summary = summarizer.generate_summary(st.session_state.messages)
                
                # 세션 보고서 생성
                session_report = summarizer.generate_session_report({
                    'messages': st.session_state.messages
                })
                
                # 요약 및 보고서 표시
                st.markdown("---")
                st.subheader("📋 상담 요약")
                st.markdown(summary)
                
                st.subheader("📊 상담 보고서")
                st.markdown(session_report)
                
                # Excel 파일 생성 및 다운로드 버튼
                excel_file = summarizer.export_to_excel({
                    'messages': st.session_state.messages,
                    'emotions': st.session_state.emotion_result if 'emotion_result' in st.session_state else []
                })
                
                if os.path.exists(excel_file):
                    with open(excel_file, "rb") as file:
                        st.download_button(
                            label="📥 상담 내용 다운로드",
                            data=file,
                            file_name=f"counseling_summary_{st.session_state.current_session_id}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
    
    # 사이드바 구성
    with st.sidebar:
        st.header("💭 상담 정보")
        message_count = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
        st.write("💌 전체 대화 수:", message_count)
        
        # 감정 분석 결과 표시
        with st.expander("😊 감정 분석"):
            if st.session_state.current_session_id and st.session_state.emotion_result:
                st.session_state.components['emotion_analyzer'].display_emotion_analysis(
                    st.session_state.emotion_result
                )
        # 위치 서비스는 별도의 탭으로 분리
        st.markdown("---")  # 구분선 추가
        st.subheader("📍 주변 상담센터 찾기")
        location_service = LocationService()
        
        # 위치 정보 입력 받기
        location_data = location_service.get_location_input()
        
        if location_data:
            # 지도 표시
            location_service.show_map_and_centers()

        # 나머지 사이드바 메뉴들
        st.markdown("---")  # 구분선 추가
        # 피드백 시스템
        with st.expander("📝 상담 피드백"):
            st.session_state.components['feedback_handler'].show_feedback_form(
                st.session_state.current_session_id
            )

        # 통계 정보
        with st.expander("📊 상담 통계"):
            emotion_stats = st.session_state.db_handler.get_emotion_statistics(
                st.session_state.current_session_id
            )
            if emotion_stats:
                st.write("감정 변화 추이:")
                for emotion, score in emotion_stats:
                    st.progress(float(score), text=f"{emotion}: {score:.2f}")
            
            # 피드백 통계
            st.session_state.components['feedback_handler'].show_feedback_statistics()

        # 데이터 내보내기
        if st.button("📥 데이터 내보내기"):
            # 대화 내용
            export_data = st.session_state.db_handler.export_session_data(
                st.session_state.current_session_id
            )
            if export_data:
                st.download_button(
                    label="💾 대화 내용 저장",
                    data=export_data,
                    file_name=f"chat_session_{st.session_state.current_session_id}.json",
                    mime="application/json"
                )
            
            # 피드백 데이터
            # feedback_data = st.session_state.components['feedback_handler'].export_feedback_data()
            # if feedback_data:
            #    st.download_button(
            #        label="📊 피드백 데이터 저장",
            #        data=feedback_data,
            #        file_name="feedback_data.csv",
            #        mime="text/csv"
            #    )

if __name__ == "__main__":
    main()