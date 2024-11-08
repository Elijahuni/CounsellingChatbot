from typing import List, Dict
from data_processor import DataProcessor
from openai import OpenAI

class RAGEngine:
    def __init__(self, data_processor: DataProcessor, openai_api_key: str):
        self.data_processor = data_processor
        self.client = OpenAI(api_key=openai_api_key)
        
    def generate_context(self, query: str) -> str:
        """유사 상담 사례를 기반으로 컨텍스트 생성"""
        similar_cases = self.data_processor.find_similar_cases(query, k=2)  # 유사 사례 수 조정
        
        context = "다음은 유사한 상담 사례들입니다:\n\n"
        for i, case in enumerate(similar_cases, 1):
            context += f"사례 {i}:\n"
            if case.get('type') == 'multi':  # 멀티턴 대화인 경우
                context += f"대화 내용:\n{case['input']}\n상담사 답변:\n{case['output']}\n\n"
            else:  # 싱글턴 대화인 경우
                context += f"내담자: {case['input']}\n상담사: {case['output']}\n\n"
            
        return context
    
    def get_response(self, query: str, chat_history: List[Dict]) -> str:
        """RAG 기반 응답 생성"""
        try:
            # 컨텍스트 생성
            context = self.generate_context(query)
            
            # 히스토리 길이로 대화 단계 파악
            is_initial = len(chat_history) <= 2
            
            # 시스템 프롬프트 구성
            system_prompt = """당신은 10년 이상의 경력을 가진 전문 심리 상담사입니다. 
            내담자의 이야기에 깊이 있게 귀 기울이고, 그들의 감정을 섬세하게 이해하며, 
            적절한 시점에 통찰력 있는 질문과 반영을 제공합니다.

전반적인 상담 원칙:
1. 경청과 공감을 최우선으로 합니다
2. 내담자의 페이스에 맞춰 대화를 진행합니다
3. 한 번에 한 가지 주제만 깊이 있게 다룹니다
4. 판단이나 평가는 절대 하지 않습니다

상황별 대응 방식:

1. 첫 응답 시 (처음 2회 대화):
- 따뜻한 인사로 시작: "안녕하세요. 편안한 마음으로 말씀해 주세요."
- 개방형 질문으로 탐색: "어떤 점에서 그렇게 느끼시나요?"
- 응답 예시: "그런 감정이 드시는군요. 언제부터 그런 느낌이 있으셨나요?"

2. 탐색 단계 (3-4회차 대화):
- 감정 반영: "~하셔서 많이 힘드셨겠네요."
- 구체화 요청: "그때 어떤 생각이 드셨나요?"
- 시간적 맥락 탐색: "그 전에도 비슷한 경험이 있으셨나요?"

3. 심화 단계 (5-6회차 대화):
- 내담자의 통찰 유도: "그런 상황에서 본인은 어떻게 대처하고 싶으신가요?"
- 변화 가능성 탐색: "어떻게 달라지길 원하시나요?"
- 내담자의 자원 발견: "지금까지 어떤 방법이 도움이 되셨나요?"

4. 정리/마무리 단계 (7회차 이상):
- 지금까지의 대화 요약
- 작은 실천 방안 제시
- 다음 대화 독려

대화 기법:

1. 감정 반영:
- "~하셔서 많이 힘드셨겠네요"
- "그런 상황에서 그렇게 느끼시는 게 당연합니다"

2. 개방형 질문:
- "어떤 점에서 그렇게 느끼시나요?"
- "그때 어떤 생각이 드셨나요?"
- "구체적으로 어떤 상황이었나요?"

3. 명료화:
- "제가 이해한 것이 맞나요?"
- "그러니까 ~라는 말씀이신가요?"

주의사항:
1. 답변은 2-3문장으로 짧게 유지
2. 이모티콘은 첫 인사와 마지막 인사에만 사용
3. 내담자가 더 많이 이야기하도록 유도
4. '사우님' 호칭 사용 금지, 항상 '내담자님' 사용

위험 신호 감지 시:
- 자해, 자살 관련 언급이 있을 경우 즉시 전문기관 정보 제공
- 학대, 폭력 상황 시 적절한 기관 연계 고려

참고할 상담 사례:
{context}

현재 대화 단계를 고려하여 적절한 깊이와 방향성을 가진 응답을 제공하세요.
"""
            
            # 메시지 구성
            messages = [
                {"role": "system", "content": system_prompt.format(context=context)}
            ]
            
            # 대화 히스토리 추가 (최근 4개 메시지만)
            recent_history = chat_history[-4:] if len(chat_history) > 4 else chat_history
            messages.extend(recent_history)
            
            # 현재 질문 추가
            messages.append({"role": "user", "content": query})
            
            # GPT 응답 생성
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.3,
                max_tokens=500,  # 짧은 응답 유도
                top_p=0.9,
                frequency_penalty=0.7,  # 반복 줄이기
                presence_penalty=0.7    # 새로운 주제 도입 억제
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"😥 죄송합니다. 오류가 발생했습니다: {str(e)}"
            
            # 메시지 구성
            messages = [
                {"role": "system", "content": system_prompt.format(context=context)}
            ]
            
            # 대화 히스토리 추가 (최근 4개 메시지만)
            recent_history = chat_history[-4:] if len(chat_history) > 4 else chat_history
            messages.extend(recent_history)
            
            # 현재 질문 추가
            messages.append({"role": "user", "content": query})
            
            # GPT 응답 생성
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,  # 자연스러운 대화를 위해 약간 높임
                max_tokens=500,   # 짧은 응답 유도
                top_p=0.9,
                frequency_penalty=0.6,  # 반복 줄이기
                presence_penalty=0.6,   # 새로운 주제 도입 억제
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"😥 죄송합니다. 오류가 발생했습니다: {str(e)}"
            
            # 메시지 구성
            messages = [
                {"role": "system", "content": system_prompt.format(context=context)}
            ]
            
            # 대화 히스토리 추가 (최근 3개 메시지만)
            recent_history = chat_history[-3:] if len(chat_history) > 3 else chat_history
            messages.extend(recent_history)
            
            # 현재 질문 추가
            messages.append({"role": "user", "content": query})
            
            # GPT 응답 생성
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # mini 모델 사용
                messages=messages,
                temperature=0.3,  # 일관성을 위해 낮춤
                max_tokens=500,   # 토큰 수 증가
                top_p=0.8,       # 더 집중된 응답을 위해 조정
                frequency_penalty=0.3,
                presence_penalty=0.3,
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"😥 죄송합니다. 오류가 발생했습니다: {str(e)}"
