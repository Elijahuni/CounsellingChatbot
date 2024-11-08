import streamlit as st
from data_processor import DataProcessor
from rag_engine import RAGEngine
from db_handler import DatabaseHandler
from location_service import LocationService
import json
import pandas as pd
import os

# 페이지 설정
st.set_page_config(
    page_title="AI 심리 상담 챗봇",
    page_icon="🤗",
    layout="wide"
)

# 데이터 프로세서 및 RAG 엔진 초기화
@st.cache_resource(show_spinner=True)
def initialize_rag():
    try:
        data_processor = DataProcessor()
        
        # 데이터 파일 경로
        single_turn_file = "total_kor_counsel_bot.jsonl"
        multi_turn_file = "total_kor_multiturn_counsel_bot.jsonl"
        wellness_file = "wellness.csv"
        
        # 파일 존재 확인
        available_files = []
        for file_path in [single_turn_file, multi_turn_file, wellness_file]:
            if os.path.exists(file_path):
                available_files.append(file_path)
            
        if not available_files:
            st.error("사용 가능한 데이터 파일을 찾을 수 없습니다.")
            return None
            
        st.info(f"사용 가능한 데이터 파일: {', '.join(available_files)}")
        
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
                                continue
                    
                    st.success(f"멀티턴 데이터 로드 완료: {sum(1 for d in data_processor.counseling_data if d['type'] == 'multi')}개")
                except Exception as e:
                    st.error(f"멀티턴 데이터 로드 중 오류: {str(e)}")

            # Wellness 데이터 로드 부분 수정
            if os.path.exists(wellness_file):
                try:
                    # CSV 파일 로드
                    wellness_df = pd.read_csv(wellness_file, encoding='utf-8')
                    
                    # 컬럼명 체크 및 데이터 처리
                    if '유저' in wellness_df.columns and '챗봇' in wellness_df.columns:
                        for _, row in wellness_df.iterrows():
                            if pd.notna(row['유저']) and pd.notna(row['챗봇']):
                                data_processor.counseling_data.append({
                                    'input': str(row['유저']).strip(),
                                    'output': str(row['챗봇']).strip(),
                                    'type': 'wellness',
                                    'category': row.get('구분', '')  # 구분 정보도 저장
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

            # FAISS 인덱스 생성 또는 로드
            if os.path.exists("faiss_index.idx"):
                data_processor.load_index("faiss_index.idx")
                st.success("기존 인덱스 로드 완료")
            else:
                if data_processor.create_embeddings():
                    data_processor.save_index("faiss_index.idx")
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
        
        # RAG 엔진 초기화
        rag_engine = RAGEngine(data_processor, st.secrets["OPENAI_API_KEY"])
        return rag_engine
        
    except Exception as e:
        st.error(f"초기화 중 오류 발생: {str(e)}")
        return None

# 위험 상황 감지 함수
def detect_crisis(text: str) -> bool:
    crisis_keywords = [
        # 자해/자살 관련
        '자살', '죽고싶다', '죽을래', '자해', 
        
        # 폭력 관련
        '살인', '살해', '타살', '학대',
        
        # 위험 도구 관련
        '농약', '수면제', '청산가리', 
        
        # 극단적 상황
        '목숨', '유서', '시체',
        
        # 심각한 범죄
        '마약', '폭행', '성폭력', '감금'
    ]
    return any(keyword in text for keyword in crisis_keywords)

# 전문가 연계 정보
CRISIS_RESOURCES = """
🚨 전문가의 도움이 필요해 보입니다.

긴급 연락처:
📞 자살예방상담전화: 1393
📞 정신건강상담전화: 1577-0199
"""

def main():
    # 데이터베이스 핸들러 초기화
    if 'db_handler' not in st.session_state:
        st.session_state.db_handler = DatabaseHandler()
    
    # 세션 상태 초기화
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.messages = []
        # 새로운 대화 세션 생성
        st.session_state.current_session_id = st.session_state.db_handler.create_session()
    
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
    st.title("🤗 AI 심리 상담 챗봇 공감엔진")
    st.write("안녕하세요! AI 심리 상담 챗봇 공감엔진 입니다. 편안한 마음으로 이야기를 시작해주세요.")
    
    # 채팅 이력 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력 처리
    if prompt := st.chat_input("고민이나 감정을 이야기해주세요..."):
        # 위험 상황 감지
        crisis_detected = detect_crisis(prompt)
        
        # 사용자 메시지 저장
        st.session_state.db_handler.save_message(
            session_id=st.session_state.current_session_id,
            role="user",
            content=prompt,
            crisis_detected=crisis_detected
        )
        
        # 사용자 메시지 표시
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 응답 생성
        if crisis_detected:
            response = f"{st.session_state.rag_engine.get_response(prompt, st.session_state.messages)}\n\n{CRISIS_RESOURCES}"
        else:
            response = st.session_state.rag_engine.get_response(prompt, st.session_state.messages)
        
        # 어시스턴트 메시지 저장
        st.session_state.db_handler.save_message(
            session_id=st.session_state.current_session_id,
            role="assistant",
            content=response,
            crisis_detected=crisis_detected
        )
        
        # 어시스턴트 메시지 표시
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
    
    # 사이드바 구성
    with st.sidebar:
        st.header("💭 상담 정보")
        message_count = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
        st.write("💌 전체 대화 수:", message_count)
        
        # 대화 내보내기 버튼
        if st.button("📥 대화 내보내기"):
            if st.session_state.current_session_id:
                export_data = st.session_state.db_handler.export_session_data(
                    st.session_state.current_session_id
                )
                if export_data:
                    st.download_button(
                        label="💾 JSON 파일로 저장",
                        data=export_data,
                        file_name=f"chat_session_{st.session_state.current_session_id}.json",
                        mime="application/json"
                    )
        
        # 대화 초기화 버튼
        if st.button("🔄 대화 초기화"):
            if st.session_state.current_session_id:
                # 현재 세션 종료
                st.session_state.db_handler.end_session(st.session_state.current_session_id)
                # 새로운 세션 시작
                st.session_state.current_session_id = st.session_state.db_handler.create_session()
            st.session_state.messages = []
            st.experimental_rerun()
        
        with st.expander("ℹ️ 안내사항"):
            st.write("""
            - 💝 일상적인 고민 상담을 제공합니다
            - 🏥 긴급한 상황은 전문가와 상담하세요
            - 🔒 모든 대화는 비공개입니다
            - 💾 대화 내용은 데이터베이스에 안전하게 저장됩니다
            """)
            
        # 통계 정보 표시
        with st.expander("📊 상담 통계"):
            if st.session_state.current_session_id:
                emotion_stats = st.session_state.db_handler.get_emotion_statistics(
                    st.session_state.current_session_id
                )
                if emotion_stats:
                    st.write("감정 분석 결과:")
                    for emotion, score in emotion_stats:
                        st.progress(float(score), text=f"{emotion}: {score:.2f}")
        # 여기에 위치 서비스 추가
        st.markdown("---")  # 구분선 추가
        st.header("📍 주변 상담센터 찾기")
        location_service = LocationService()
        
        # 위치 입력 받기
        location_data = location_service.get_location_input()
        
        if location_data:
            # 지도 표시
            st.subheader("🗺️ 현재 위치")
            location_service.show_map(location_data)
            
            # 주변 상담센터 검색
            st.subheader("🏥 주변 상담센터")
            centers = location_service.find_nearby_counseling_centers(location_data)
            
            if centers:
                for center in centers:
                    with st.expander(f"📍 {center['name']}"):
                        st.write(f"주소: {center['address']}")
                        st.write(f"전화: {center['phone']}")
                        st.write(f"거리: {center['distance']}")
            else:
                st.info("주변에 상담센터가 없습니다.")

if __name__ == "__main__":
    main()
