# components/feedback_handler.py
import streamlit as st
from datetime import datetime
import pandas as pd

class FeedbackHandler:
    def __init__(self, db_handler):
        self.db_handler = db_handler
        self.rating_emoji = {
            1: "😢",
            2: "🙁",
            3: "😐",
            4: "🙂",
            5: "😊"
        }

    def show_feedback_form(self, session_id):
        """상담 만족도 평가 폼 표시"""
        st.write("### 상담 만족도 평가")
        
        # 평점 입력
        rating = st.slider(
            "상담은 어떠셨나요?",
            min_value=1,
            max_value=5,
            value=3,
            help="1(매우 불만족)부터 5(매우 만족)까지 선택해주세요"
        )
        st.write(f"선택하신 평가: {self.rating_emoji[rating]}")
        
        # 상세 피드백
        feedback_text = st.text_area(
            "상담에 대한 의견을 자유롭게 작성해주세요 (선택사항)",
            placeholder="상담 경험에 대한 의견을 들려주세요..."
        )
        
        # 개선사항 체크박스
        improvement_areas = st.multiselect(
            "개선이 필요한 부분을 선택해주세요 (복수 선택 가능)",
            ["응답 속도", "대화 자연스러움", "공감 능력", "문제 해결력", "기타"]
        )
        
        # 제출 버튼
        if st.button("평가 제출"):
            self.save_feedback(
                session_id=session_id,
                rating=rating,
                feedback_text=feedback_text,
                improvement_areas=improvement_areas
            )
            return True
        return False

    def save_feedback(self, session_id, rating, feedback_text="", improvement_areas=None):
        """피드백 저장"""
        try:
            feedback_data = {
                "session_id": session_id,
                "rating": rating,
                "feedback_text": feedback_text,
                "improvement_areas": ",".join(improvement_areas) if improvement_areas else "",
                "timestamp": datetime.now()
            }
            
            self.db_handler.save_feedback(feedback_data)
            st.success("피드백이 성공적으로 저장되었습니다. 감사합니다! 🙏")
            
        except Exception as e:
            st.error(f"피드백 저장 중 오류가 발생했습니다: {str(e)}")

    def show_feedback_statistics(self):
        """피드백 통계 표시"""
        try:
            stats = self.db_handler.get_feedback_statistics()
            if not stats:
                st.info("아직 피드백 데이터가 없습니다.")
                return
                
            st.write("### 상담 만족도 통계")
            
            # 평균 평점
            avg_rating = stats.get("average_rating", 0)
            st.metric("평균 평점", f"{avg_rating:.1f} / 5.0")
            
            # 평점 분포
            rating_dist = stats.get("rating_distribution", {})
            if rating_dist:
                st.bar_chart(rating_dist)
                
            # 개선 필요 영역
            improvement_stats = stats.get("improvement_areas", {})
            if improvement_stats:
                st.write("### 개선 필요 영역")
                for area, count in improvement_stats.items():
                    st.progress(count/sum(improvement_stats.values()), 
                              text=f"{area}: {count}건")
                              
        except Exception as e:
            st.error(f"통계 표시 중 오류 발생: {str(e)}")

    def export_feedback_data(self):
        """피드백 데이터 내보내기"""
        try:
            feedback_data = self.db_handler.get_all_feedback()
            if not feedback_data:
                st.info("내보낼 피드백 데이터가 없습니다.")
                return None
                
            df = pd.DataFrame(feedback_data)
            return df.to_csv(index=False)
            
        except Exception as e:
            st.error(f"데이터 내보내기 중 오류 발생: {str(e)}")
            return None