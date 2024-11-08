# summarizer.py
from openai import OpenAI
import pandas as pd
from datetime import datetime

class ChatSummarizer:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def generate_summary(self, conversation_history):
        """대화 내용 요약 생성"""
        try:
            formatted_history = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history
            ])

            summary_prompt = f"""
            다음 상담 대화를 요약해주세요. 주요 문제, 감정 상태, 제안된 해결책을 포함해 주세요:

            {formatted_history}

            요약 형식:
            1. 주요 호소 문제:
            2. 내담자의 감정 상태:
            3. 제안된 해결 방안:
            4. 상담 진행 상태:
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 전문 심리 상담사입니다. 상담 내용을 전문적으로 요약해주세요."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"요약 생성 중 오류 발생: {str(e)}"

    def generate_session_report(self, session_data):
        """상담 세션 보고서 생성"""
        try:
            messages = session_data['messages']
            conversation = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in messages
            ])

            report_prompt = f"""
            다음 상담 세션에 대한 전문적인 보고서를 작성해주세요:

            {conversation}

            보고서 형식:
            1. 세션 개요
            2. 주요 문제점 분석
            3. 내담자의 심리상태 평가
            4. 사용된 상담 기법
            5. 진전 상황
            6. 향후 권장 사항
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 전문 심리 상담사입니다. 상담 세션에 대한 전문적인 보고서를 작성해주세요."},
                    {"role": "user", "content": report_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"보고서 생성 중 오류 발생: {str(e)}"

    def export_to_excel(self, session_data):
        """세션 데이터를 Excel 파일로 변환"""
        try:
            # 메시지 데이터 변환
            messages_df = pd.DataFrame(session_data['messages'])
            emotions_df = pd.DataFrame(session_data['emotions'])

            # Excel 작성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"counseling_session_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename) as writer:
                messages_df.to_excel(writer, sheet_name='Messages', index=False)
                emotions_df.to_excel(writer, sheet_name='Emotions', index=False)
                
                # 요약 정보 시트 추가
                summary = self.generate_summary([{
                    'role': row['role'],
                    'content': row['content']
                } for _, row in messages_df.iterrows()])
                
                summary_df = pd.DataFrame({'Summary': [summary]})
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

            return filename

        except Exception as e:
            return f"Excel 파일 생성 중 오류 발생: {str(e)}"