# components/theme_manager.py
import streamlit as st

class ThemeManager:
    def __init__(self):
        self.themes = {
            "긍정": {
                "primary_color": "#4CAF50",    # 생기있는 그린
                "background_color": "#E8F5E9", # 연한 민트빛 배경
                "text_color": "#1B5E20",      # 진한 그린
                "accent_color": "#81C784",     # 밝은 그린
                "border_color": "#A5D6A7"      # 중간 톤의 그린
            },
            "중립": {
                "primary_color": "#3F51B5",    # 인디고
                "background_color": "#F5F5F5", # 밝은 그레이
                "text_color": "#1A237E",      # 진한 인디고
                "accent_color": "#7986CB",     # 연한 인디고
                "border_color": "#9FA8DA"      # 중간 톤의 인디고
            },
            "부정": {
                "primary_color": "#E53935",    # 진한 레드
                "background_color": "#FFEBEE", # 매우 연한 레드
                "text_color": "#B71C1C",      # 매우 진한 레드
                "accent_color": "#EF5350",     # 밝은 레드
                "border_color": "#EF9A9A"      # 연한 레드
            }
        }
        
        if 'current_theme' not in st.session_state:
            st.session_state.current_theme = "중립"

    def apply_theme(self, emotion):
        """감정에 따른 테마 적용"""
        if not emotion:
            return
            
        theme = self.themes.get(emotion, self.themes["중립"])
        
        if st.session_state.current_theme != emotion:
            st.session_state.current_theme = emotion
            
            # 부정적 감정일 때의 애니메이션 효과
            animation_css = ""
            if emotion == "부정":
                animation_css = """
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.8; }
                        100% { opacity: 1; }
                    }
                    
                    @keyframes border-pulse {
                        0% { border-color: """ + theme["border_color"] + """; }
                        50% { border-color: """ + theme["accent_color"] + """; }
                        100% { border-color: """ + theme["border_color"] + """; }
                    }
                    
                    @keyframes background-pulse {
                        0% { background-color: """ + theme["background_color"] + """; }
                        50% { background-color: """ + theme["accent_color"] + "22" + """; }
                        100% { background-color: """ + theme["background_color"] + """; }
                    }
                """

            animation_style = ""
            if emotion == "부정":
                animation_style = "animation: pulse 2s ease-in-out infinite;"
                
            background_animation = ""
            if emotion == "부정":
                background_animation = "animation: background-pulse 3s ease-in-out infinite;"
                
            border_animation = ""
            if emotion == "부정":
                border_animation = "animation: border-pulse 3s ease-in-out infinite;"

            # CSS 스타일 적용
            st.markdown(
                f"""
                <style>
                    {animation_css}
                    
                    .stApp {{
                        background-color: {theme["background_color"]};
                        color: {theme["text_color"]};
                        transition: all 0.3s ease;
                        {background_animation}
                    }}
                    
                    .stButton>button {{
                        background-color: {theme["primary_color"]};
                        color: white;
                        border: none;
                        transition: all 0.3s ease;
                        {animation_style}
                    }}
                    
                    .stButton>button:hover {{
                        background-color: {theme["accent_color"]};
                        transform: scale(1.05);
                    }}
                    
                    .stProgress > div > div {{
                        background-color: {theme["accent_color"]};
                        transition: all 0.3s ease;
                        {animation_style}
                    }}
                    
                    .stTextInput > div > div {{
                        border-color: {theme["border_color"]};
                        {border_animation}
                    }}
                    
                    .streamlit-expanderHeader {{
                        background-color: {theme["background_color"]};
                        color: {theme["text_color"]};
                        {background_animation}
                    }}
                    
                    .bot-message {{
                        background-color: {theme["background_color"]};
                        border: 1px solid {theme["border_color"]};
                        padding: 15px;
                        border-radius: 15px;
                        margin: 5px 0;
                        transition: all 0.3s ease;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        {border_animation}
                    }}
                    
                    .user-message {{
                        background-color: {theme["accent_color"]}22;
                        border: 1px solid {theme["border_color"]};
                        padding: 15px;
                        border-radius: 15px;
                        margin: 5px 0;
                        text-align: right;
                        transition: all 0.3s ease;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        {border_animation}
                    }}
                </style>
                """,
                unsafe_allow_html=True
            )

    def get_theme_colors(self, emotion):
        """테마 색상 가져오기"""
        return self.themes.get(emotion, self.themes["중립"])

    def apply_custom_theme(self, colors):
        """커스텀 테마 적용"""
        if not colors:
            return
            
        st.markdown(
            f"""
            <style>
                .stApp {{
                    background-color: {colors["background_color"]};
                    color: {colors["text_color"]};
                    transition: all 0.3s ease;
                }}
                .stButton>button {{
                    background-color: {colors["primary_color"]};
                    color: white;
                    transition: all 0.3s ease;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

    def get_current_theme(self):
        """현재 테마 정보 반환"""
        return self.themes.get(st.session_state.current_theme, self.themes["중립"])