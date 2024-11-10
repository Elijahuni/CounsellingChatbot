# components/emotion_analyzer.py

import streamlit as st
from transformers import pipeline
import re

class EmotionAnalyzer:
    def __init__(self):
        self.classifier = pipeline(
            "sentiment-analysis",
            model="kykim/bert-kor-base",
            tokenizer="kykim/bert-kor-base"
        )
        
        # 감정 키워드 정의
        self.emotion_keywords = {
            "긍정": [
                "행복", "좋다", "신나다", "즐겁다", "감사",
                "성공", "해냈다", "뿌듯", "자랑스럽다",
                "기대", "희망", "설레다",
                "만족", "충분", "편안"
            ],
            "부정": [
                "슬프다", "우울", "외롭다", "허전",
                "화나다", "짜증", "답답", "억울",
                "걱정", "불안", "두렵다", "무섭다",
                "힘들다", "지치다", "피곤", "괴롭다"
            ],
            "중립": [
                "보통", "평범", "일상",
                "궁금", "생각", "고민",
                "예정", "계획", "준비"
            ]
        }
        
        # 강조어 리스트
        self.intensifiers = ["매우", "너무", "정말", "진짜", "완전", "아주"]

    def analyze_emotion(self, text: str):
        """텍스트의 감정 분석"""
        try:
            # BERT 모델을 통한 기본 감정 분석
            result = self.classifier(text)[0]
            base_score = result['score']
            
            # 키워드 기반 감정 분석
            keyword_emotions = self._analyze_keywords(text)
            
            # 강조어 검출
            intensity_modifier = self._check_intensifiers(text)
            
            # 최종 감정 결정
            final_emotion = self._determine_final_emotion(
                base_score, 
                keyword_emotions,
                intensity_modifier
            )
            
            return {
                'dominant_emotion': final_emotion['emotion'],
                'emotion_scores': {
                    '긍정': final_emotion['positive_score'],
                    '중립': final_emotion['neutral_score'],
                    '부정': final_emotion['negative_score']
                },
                'keywords_detected': keyword_emotions['detected_keywords'],
                'intensity': intensity_modifier
            }
            
        except Exception as e:
            st.error(f"감정 분석 중 오류 발생: {str(e)}")
            return None

    def _analyze_keywords(self, text):
        """키워드 기반 감정 분석"""
        detected_keywords = {
            "긍정": [],
            "부정": [],
            "중립": []
        }
        
        # 키워드 검출
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    detected_keywords[emotion].append(keyword)
        
        # 감정 점수 계산
        scores = {
            "긍정": len(detected_keywords["긍정"]) * 0.2,
            "부정": len(detected_keywords["부정"]) * 0.2,
            "중립": len(detected_keywords["중립"]) * 0.2
        }
        
        return {
            "scores": scores,
            "detected_keywords": detected_keywords
        }

    def _check_intensifiers(self, text):
        """강조어 검출 및 강도 수정자 계산"""
        intensity = 1.0
        for intensifier in self.intensifiers:
            if intensifier in text:
                intensity += 0.2  # 각 강조어마다 강도 증가
        return min(intensity, 2.0)  # 최대 2배까지만 허용

    def _determine_final_emotion(self, base_score, keyword_emotions, intensity):
        """최종 감정 결정"""
        # BERT 점수를 긍정/부정 점수로 변환
        bert_positive = base_score
        bert_negative = 1 - base_score
        bert_neutral = 1 - abs(bert_positive - bert_negative)
        
        # 키워드 점수와 BERT 점수 결합
        keyword_scores = keyword_emotions['scores']
        final_scores = {
            'positive_score': (bert_positive + keyword_scores['긍정']) * intensity,
            'negative_score': (bert_negative + keyword_scores['부정']) * intensity,
            'neutral_score': (bert_neutral + keyword_scores['중립']) / 2  # 중립은 강도 영향 X
        }
        
        # 최종 감정 결정
        max_score = max(final_scores.values())
        if max_score == final_scores['neutral_score']:
            emotion = "중립"
        elif max_score == final_scores['positive_score']:
            emotion = "긍정"
        else:
            emotion = "부정"
            
        return {
            'emotion': emotion,
            **final_scores
        }

    def display_emotion_analysis(self, analysis_result):
        """감정 분석 결과 시각화"""
        if not analysis_result:
            return
            
        # 감정 이모지 매핑
        emotion_emoji = {
            "긍정": "😊",
            "중립": "😐",
            "부정": "😢"
        }
            
        st.write(f"### 현재 감정 상태: {emotion_emoji[analysis_result['dominant_emotion']]}")
        
        # 감정 점수 표시
        for emotion, score in analysis_result['emotion_scores'].items():
            st.progress(score, text=f"{emotion}: {score:.2f}")
        
        # 검출된 키워드 표시
        if 'keywords_detected' in analysis_result:
            st.write("### 감지된 감정 키워드")
            for emotion, keywords in analysis_result['keywords_detected'].items():
                if keywords:
                    st.write(f"{emotion_emoji[emotion]} {emotion}: {', '.join(keywords)}")