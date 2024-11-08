# data_processor.py
import os
import json
import pandas as pd
from typing import List, Dict, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import threading
from functools import lru_cache

class DataProcessor:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "jhgan/ko-sbert-nli"):
        if not hasattr(self, 'initialized'):
            self.model = SentenceTransformer(model_name, device='cpu')
            self.index = None
            self.counseling_data = []
            self.wellness_data = []
            self.batch_size = 32
            self.initialized = True
    
    def load_counseling_data(self, single_turn_path: str, multi_turn_path: str, wellness_path: str) -> bool:
        """모든 상담 데이터 로드"""
        try:
            # 기존 데이터 초기화
            self.counseling_data = []
            
            # 싱글턴 데이터 로드
            if os.path.exists(single_turn_path):
                with open(single_turn_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            self.counseling_data.append({
                                'input': data['input'],
                                'output': data['output'],
                                'type': 'single'
                            })
                        except json.JSONDecodeError:
                            continue
            
            # 멀티턴 데이터 로드
            if os.path.exists(multi_turn_path):
                with open(multi_turn_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            processed_dialog = self._process_multiturn_dialog(data)
                            if processed_dialog:
                                self.counseling_data.append(processed_dialog)
                        except json.JSONDecodeError:
                            continue

            # Wellness 데이터셋 로드
            if os.path.exists(wellness_path):
                try:
                    wellness_df = pd.read_csv(wellness_path)
                    for _, row in wellness_df.iterrows():
                        self.counseling_data.append({
                            'input': row['Q'],
                            'output': row['A'],
                            'type': 'wellness'
                        })
                except Exception as e:
                    print(f"Wellness 데이터 로드 중 오류: {str(e)}")
            
            return len(self.counseling_data) > 0
            
        except Exception as e:
            print(f"데이터 로드 중 오류 발생: {str(e)}")
            return False
    
    def _process_multiturn_dialog(self, dialog_data: Dict) -> Optional[Dict]:
        """멀티턴 대화 데이터 처리"""
        try:
            processed_input = ""
            processed_output = ""
            
            for utterance in dialog_data.get('dialogue', []):
                if utterance.get('speaker') == 'user':
                    processed_input += f"내담자: {utterance.get('utterance', '')}\n"
                else:
                    processed_output += f"상담사: {utterance.get('utterance', '')}\n"
            
            return {
                'input': processed_input.strip(),
                'output': processed_output.strip(),
                'type': 'multi'
            } if processed_input and processed_output else None
            
        except Exception:
            return None

    @lru_cache(maxsize=1024)
    def encode_text(self, text: str) -> np.ndarray:
        """텍스트 인코딩 (캐시 사용)"""
        return self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
    
    def create_embeddings(self) -> bool:
        """문서 임베딩 생성"""
        try:
            if not self.counseling_data:
                return False
                
            texts = [data['input'] for data in self.counseling_data]
            embeddings_list = []
            
            # 배치 처리로 임베딩 생성
            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i + self.batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts, 
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    batch_size=self.batch_size
                )
                embeddings_list.append(batch_embeddings)
            
            embeddings = np.vstack(embeddings_list)
            
            # FAISS 인덱스 생성
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)
            
            return True
            
        except Exception as e:
            print(f"임베딩 생성 중 오류: {str(e)}")
            return False

    def find_similar_cases(self, query: str, k: int = 3) -> List[Dict]:
        """유사 케이스 검색"""
        if not self.counseling_data or not self.index:
            return []
            
        try:
            query_vector = self.encode_text(query).reshape(1, -1)
            distances, indices = self.index.search(query_vector, k)
            
            similar_cases = []
            for idx in indices[0]:
                if 0 <= idx < len(self.counseling_data):
                    similar_cases.append(self.counseling_data[idx])
                
            return similar_cases
            
        except Exception as e:
            print(f"유사 케이스 검색 중 오류: {str(e)}")
            return []

    def save_index(self, file_path: str) -> bool:
        """FAISS 인덱스 저장"""
        try:
            faiss.write_index(self.index, file_path)
            return True
        except Exception as e:
            print(f"인덱스 저장 중 오류: {str(e)}")
            return False
    
    def load_index(self, file_path: str) -> bool:
        """FAISS 인덱스 로드"""
        try:
            self.index = faiss.read_index(file_path)
            return True
        except Exception as e:
            print(f"인덱스 로드 중 오류: {str(e)}")
            return False