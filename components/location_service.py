# components/location_service.py

import streamlit as st
import streamlit.components.v1 as components
import requests
import folium
from streamlit_folium import st_folium
import json

class LocationService:
    def __init__(self):
        try:
            self.api_key = st.secrets["KAKAO_API_KEY"]
            if not self.api_key:
                raise KeyError("API 키가 설정되지 않았습니다")
            if 'location_data' not in st.session_state:
                st.session_state.location_data = None
        except Exception as e:
            st.error(f"위치 서비스 초기화 오류: {str(e)}")
            self.api_key = None

    def get_current_location_by_ip(self):
        """IP 기반 현재 위치 확인"""
        try:
            response = requests.get('https://ipapi.co/json/')
            if response.status_code == 200:
                data = response.json()
                return {
                    "lat": float(data['latitude']),
                    "lon": float(data['longitude']),
                    "address": f"{data['city']}, {data['region']}"
                }
        except Exception as e:
            st.error(f"위치 확인 중 오류 발생: {str(e)}")
        return None

    def get_coordinates(self, address, search_type=""):
        """주소를 좌표로 변환"""
        if not self.api_key:
            st.error("API 키가 설정되지 않아 위치 서비스를 사용할 수 없습니다.")
            return None

        try:
            # 검색 유형에 따른 API 선택
            if search_type == "키워드로 검색":
                url = "https://dapi.kakao.com/v2/local/search/keyword.json"
            else:
                url = "https://dapi.kakao.com/v2/local/search/address.json"

            headers = {"Authorization": f"KakaoAK {self.api_key}"}
            params = {"query": address}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("documents"):
                location = result["documents"][0]
                
                # 키워드 검색일 경우의 결과 처리
                if search_type == "키워드로 검색":
                    return {
                        "address": location.get("place_name", ""),
                        "address_detail": f"{location.get('address_name', '')} ({location.get('place_name', '')})",
                        "lat": float(location["y"]),
                        "lon": float(location["x"])
                    }
                
                # 주소 검색일 경우의 결과 처리
                road_address = location.get("road_address", {})
                jibun_address = location.get("address", {})
                
                address_detail = road_address.get("address_name", "") if road_address else jibun_address.get("address_name", "")
                building_name = road_address.get("building_name", "") if road_address else ""
                
                if building_name:
                    address_detail += f" ({building_name})"

                return {
                    "address": address_detail,
                    "lat": float(location["y"]),
                    "lon": float(location["x"])
                }
            else:
                st.warning("주소를 찾을 수 없습니다. 다시 확인해주세요.")
                return None

        except Exception as e:
            st.error(f"위치 검색 중 오류가 발생했습니다: {str(e)}")
            return None

    def get_location_input(self):
        """위치 정보 입력 받기"""
        st.write("📍 위치 정보")
        
        # 위치 정보 입력 방식 선택
        location_method = st.radio(
            "위치 정보 입력 방식을 선택해주세요:",
            ["🎯 현재 위치 사용", "✍️ 주소 검색"],
            horizontal=True,
            key="location_method"
        )
        
        if location_method == "🎯 현재 위치 사용":
            if st.button("📍 현재 위치 찾기", key="current_location"):
                with st.spinner("현재 위치를 찾는 중..."):
                    location_data = self.get_current_location_by_ip()
                    if location_data:
                        st.session_state.location_data = location_data
                        st.success(f"📍 현재 위치: {location_data['address']}")
                    else:
                        st.error("위치를 찾을 수 없습니다. 주소 검색을 이용해주세요.")
        else:
            # 검색 방식 선택
            search_type = st.selectbox(
                "검색 방식 선택",
                [
                    "도로명주소로 검색",
                    "지번주소로 검색",
                    "건물명으로 검색",
                    "동/읍/면으로 검색",
                    "키워드로 검색"
                ],
                key="search_type"
            )

            # 검색 도움말
            help_text = {
                "도로명주소로 검색": "예: 테헤란로 152, 강남대로 396",
                "지번주소로 검색": "예: 역삼동 823, 삼성동 159",
                "건물명으로 검색": "예: 강남파이낸스센터, 코엑스",
                "동/읍/면으로 검색": "예: 역삼1동, 삼성1동",
                "키워드로 검색": "예: 강남역, 서울대학교"
            }

            col1, col2 = st.columns([3, 1])
            with col1:
                address = st.text_input(
                    "주소 입력",
                    key="address_input",
                    help=help_text[search_type],
                    placeholder=help_text[search_type].split(": ")[1].split(", ")[0]
                )
            with col2:
                if st.button("검색", key="search_button"):
                    if address:
                        with st.spinner("주소를 검색중입니다..."):
                            location_data = self.get_coordinates(address, search_type)
                            if location_data:
                                st.session_state.location_data = location_data
                                st.success(f"📍 검색된 주소: {location_data['address']}")

        return st.session_state.location_data

    def show_map_and_centers(self):
        """지도 및 상담센터 정보 표시"""
        if st.session_state.location_data:
            # 지도 생성 및 표시
            m = folium.Map(
                location=[st.session_state.location_data["lat"], 
                        st.session_state.location_data["lon"]], 
                zoom_start=15
            )
            
            # 현재 위치 마커 추가
            folium.Marker(
                [st.session_state.location_data["lat"], 
                st.session_state.location_data["lon"]],
                popup="현재 위치",
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)
            
            # 주변 상담센터 검색 및 마커 추가
            centers = self.find_nearby_counseling_centers(st.session_state.location_data)
            
            for center in centers:
                folium.Marker(
                    [float(center["lat"]) if "lat" in center else st.session_state.location_data["lat"],
                    float(center["lon"]) if "lon" in center else st.session_state.location_data["lon"]],
                    popup=f"{center['name']}<br>{center['phone']}",
                    icon=folium.Icon(color="green", icon="info-sign"),
                ).add_to(m)
            
            # 지도 표시
            st_folium(m, width=300, height=300, key="map")
            
            # 상담센터 목록 표시
            st.write("### 🏥 주변 상담센터")
            if centers:
                for center in centers:
                    # expander 대신 markdown으로 표시
                    st.markdown(f"""
                    ---
                    ### 📍 {center['name']} ({center['distance']})
                    - 🏢 주소: {center['address']}
                    - 📞 전화: {center['phone']}
                    {f"- 📑 분류: {center['category']}" if center.get('category') else ""}
                    {f"- 🔗 [상세 정보 보기]({center['place_url']})" if center.get('place_url') else ""}
                    """)
            else:
                st.info("주변에 상담센터가 없습니다.")

    def find_nearby_counseling_centers(self, location_data, radius=3000):
        """주변 상담 센터 검색"""
        if not location_data or not self.api_key:
            return []

        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {
            "query": "심리상담센터",
            "x": location_data["lon"],
            "y": location_data["lat"],
            "radius": radius,
            "sort": "distance"
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            centers = []
            for place in result.get("documents", []):
                distance_meters = float(place['distance'])
                distance_display = f"{distance_meters/1000:.1f}km" if distance_meters >= 1000 else f"{distance_meters:.0f}m"

                centers.append({
                    "name": place["place_name"],
                    "address": place["address_name"],
                    "phone": place.get("phone", "번호 없음"),
                    "distance_value": distance_meters,
                    "distance": distance_display,
                    "lat": float(place["y"]),
                    "lon": float(place["x"]),
                    "place_url": place.get("place_url", ""),
                    "category": place.get("category_name", "")
                })

            centers.sort(key=lambda x: x["distance_value"])
            return centers

        except Exception as e:
            st.error(f"상담센터 검색 중 오류가 발생했습니다: {str(e)}")
            return []

    def display_centers_info(self, centers):
        """상담센터 정보 표시"""
        if not centers:
            st.info("주변에 상담센터가 없습니다.")
            return

        for center in centers:
            with st.expander(f"📍 {center['name']} ({center['distance']})"):
                st.write(f"🏢 주소: {center['address']}")
                st.write(f"📞 전화: {center['phone']}")
                if center.get('category'):
                    st.write(f"📑 분류: {center['category']}")
                if center.get('place_url'):
                    st.write(f"🔗 [상세 정보 보기]({center['place_url']})")