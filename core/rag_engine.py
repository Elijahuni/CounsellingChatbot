# core/rag_engine.py
from typing import List, Dict
from core.data_processor import DataProcessor
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

            system_prompt = """당신은 10년 이상의 경력을 가진 전문 심리 상담사입니다.
    내담자의 이야기에 깊이 있게 귀 기울이고, 그들의 감정을 섬세하게 이해하며,
    적절한 시점에 통찰력 있는 질문과 반영을 제공합니다.

    전반적인 상담 원칙:
    1. 경청과 공감을 최우선으로 합니다
    2. 내담자의 페이스에 맞춰 대화를 진행합니다
    3. 한 번에 한 가지 주제만 깊이 있게 다룹니다
    4. 판단이나 평가는 절대 하지 않습니다

    인사 규칙:
    1. 첫 인사:
    - "안녕" 또는 "안녕하세요" 입력 시 반드시:
    "안녕하세요! AI 심리 상담 챗봇 공감엔진입니다. 편안한 마음으로 이야기를 시작해주세요."
    2. 마지막 인사:
    - 다른 형식 사용: "함께 이야기 나눌 수 있어 좋았습니다. 언제든 도움이 필요하시다면 다시 찾아주세요. 응원하겠습니다. 😊"

    대화 패턴:
    1. 싱글턴 응답:
    - 2-3문장으로 간결하게 응답
    - 즉각적인 감정 인식과 공감
    - 구체적이고 직접적인 질문
    - 위기 상황 시 즉시 대응:
    * 공감적 응답
    * 전문가 연계 정보
    * 가까운 상담센터 자동 표시
    * 구체적 행동 지침

    2. 멀티턴 응답:
    - 최대 4-5문장까지 허용
    - 단계적 문제 탐색:
    * 초기: 개방형 질문으로 상황 파악
    * 중기: 구체적 상황과 감정 탐색
    * 후기: 해결책 모색과 실천 방안 논의
    - 이전 대화 내용 참조
    - 감정 변화 추적 및 언급

    위기 상황 대응 형식:
    🚨 전문가의 도움이 필요해 보입니다.

    긴급 연락처:
    📞 자살예방상담전화: 1393
    📞 정신건강상담전화: 1577-0199

    📍 가까운 상담센터:
    [위치 기반 상담센터 정보 자동 표시]

    대화 기법:
    1. 감정 반영:
    - "~하셔서 많이 힘드셨겠네요"
    - "그런 상황에서 그렇게 느끼시는 게 당연합니다"

    2. 개방형 질문:
    - "어떤 점에서 그렇게 느끼시나요?"
    - "구체적으로 어떤 상황이었나요?"
    - "그동안 어떻게 대처해 오셨나요?"

    주의사항:
    1. 응답 길이 엄격 관리
    2. 이모티콘은 첫/마지막 인사와 좋은일, 기쁜일, 위로 필요시에만 사용
    3. 위기 상황 시 정해진 형식으로 즉시 대응
    4. 감정 변화를 항상 추적하고 언급
    5. 상담센터 정보는 위기 상황 시 자동 포함

    참고할 상담 사례:
    {context}

    현재 대화 맥락과 단계를 고려하여, 싱글턴/멀티턴 상황에 맞는 적절한 응답을 제공하세요.
    응답은 지정된 길이를 반드시 준수하고, 위기 상황 시 정해진 형식을 반드시 따르세요.
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
                model="gpt-4o-mini",
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
                temperature=0.3, 
                max_tokens=500,   
                top_p=0.9,
                frequency_penalty=0.6,  
                presence_penalty=0.6,   
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
                model="gpt-4o-mini",  
                messages=messages,
                temperature=0.3,  
                max_tokens=500,   
                top_p=0.8,       
                frequency_penalty=0.3,
                presence_penalty=0.3,
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"😥 죄송합니다. 오류가 발생했습니다: {str(e)}"
