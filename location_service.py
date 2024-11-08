import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

class LocationService:
    def __init__(self):
        try:
            # .streamlit/secrets.toml 파일에서 API 키 로드
            self.api_key = st.secrets["KAKAO_API_KEY"]
            
            # API 키 유효성 검증
            if not self.api_key or self.api_key == "your_api_key":
                raise KeyError("올바른 API 키가 설정되지 않았습니다.")
                
        except Exception as e:
            st.error(f"""
            Kakao API 키 설정이 필요합니다.
            1. .streamlit/secrets.toml 파일을 생성하세요
            2. KAKAO_API_KEY = "your_api_key" 를 추가하세요
            에러 메시지: {str(e)}
            """)
            self.api_key = None

    def get_location_input(self):
        """사용자 위치 입력 받기"""
        col1, col2 = st.columns([3, 1])
        with col1:
            address = st.text_input("📍 현재 위치를 입력해주세요 (예: 서울시 강남구)", key="location_input")
        with col2:
            search_button = st.button("검색", key="search_location")
        
        if address and search_button:
            return self.get_coordinates(address)
        return None

    def get_coordinates(self, address):
        """주소를 좌표로 변환"""
        if not self.api_key:
            st.error("API 키가 설정되지 않아 위치 서비스를 사용할 수 없습니다.")
            return None
            
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {"query": address}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            if result.get("documents"):
                location = result["documents"][0]
                return {
                    "address": address,
                    "lat": float(location["y"]),
                    "lon": float(location["x"])
                }
            else:
                st.warning("주소를 찾을 수 없습니다. 다시 확인해주세요.")
                return None
                
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 401:
                st.error("API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                st.error(f"HTTP 에러가 발생했습니다: {http_err}")
            return None
            
        except Exception as e:
            st.error(f"위치 검색 중 오류가 발생했습니다: {str(e)}")
            return None

    def show_map(self, location_data):
        """지도에 위치 표시"""
        if location_data:
            m = folium.Map(
                location=[location_data["lat"], location_data["lon"]], 
                zoom_start=15
            )
            
            # 현재 위치 마커 추가
            folium.Marker(
                [location_data["lat"], location_data["lon"]],
                popup="현재 위치",
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)
            
            # Streamlit에 지도 표시
            st_folium(m, width=300, height=300)
            
            return True
        return False

    def find_nearby_counseling_centers(self, location_data, radius=3000):
        """주변 상담 센터 검색"""
        if not location_data:
            return []
            
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {
            "query": "심리상담센터",
            "x": location_data["lon"],
            "y": location_data["lat"],
            "radius": radius
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            centers = []
            for place in result.get("documents", []):
                centers.append({
                    "name": place["place_name"],
                    "address": place["address_name"],
                    "phone": place.get("phone", "번호 없음"),
                    "distance": f"{float(place['distance']):.1f}m"
                })
            
            return centers
            
        except Exception as e:
            st.error(f"상담센터 검색 중 오류가 발생했습니다: {str(e)}")
            return []