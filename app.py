"""
트레이너 데이터 관리 대시보드
- 현재 데이터 현황 확인
- 새로운 데이터 추가
- 실시간 점수/티어 업데이트
"""

import streamlit as st
import psycopg2
import os
import requests
from dotenv import load_dotenv
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# .env 로드 (로컬용)
load_dotenv()

# Streamlit secrets 지원 (배포용)
def get_db_config():
    """로컬 환경변수 또는 Streamlit secrets에서 DB 설정 가져오기"""
    try:
        # Streamlit Cloud 배포 환경 (secrets.toml이 있으면)
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            return {
                'host': st.secrets['database']['DB_HOST'],
                'port': st.secrets['database']['DB_PORT'],
                'database': st.secrets['database']['DB_NAME'],
                'user': st.secrets['database']['DB_USER'],
                'password': st.secrets['database']['DB_PASSWORD']
            }
    except:
        pass
    
    # 로컬 개발 환경 (.env 파일 사용)
    return {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

# 백엔드 API 베이스 URL
def get_backend_base_url():
    return os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

# 페이지 설정
st.set_page_config(
    page_title="트레이너 관리자 페이지",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일
st.markdown("""
<style>
    .big-font {
        font-size: 30px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# DB 연결
@st.cache_resource
def get_db_connection():
    config = get_db_config()
    conn = psycopg2.connect(**config)
    return conn

def get_safe_connection():
    """안전한 DB 연결 가져오기 (닫혀있으면 재연결)"""
    conn = get_db_connection()
    try:
        # 연결 상태 확인
        conn.cursor().execute("SELECT 1")
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # 연결이 닫혔으면 캐시 초기화 후 재연결
        st.cache_resource.clear()
        conn = get_db_connection()
    return conn


# 현재 데이터 가져오기
def get_current_data(trainer_id):
    conn = None
    cur = None
    try:
        conn = get_safe_connection()
        cur = conn.cursor()
        
        tables = {
            'QnA': 'data_trainer_qna',
            '운동 가이드라인': 'data_trainer_workout_guideline',
            '식단 가이드라인': 'data_trainer_diet_guideline',
            '철학/마인드셋': 'data_trainer_philosophy',
            '부상 관리': 'data_trainer_injury',
            '피드백': 'data_trainer_feedback',
            '식단 예시': 'data_trainer_meal_examples',
            '운동 예시': 'data_trainer_workout_examples',
            '톤/말투': 'data_trainer_tones_raw'
        }
        
        data = {}
        for name, table in tables.items():
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table} WHERE trainer_id = %s", (trainer_id,))
                count = cur.fetchone()[0]
                data[name] = count
            except Exception as e:
                # SELECT 쿼리는 롤백 불필요, 에러만 기록하고 계속 진행
                data[name] = 0
        
        return data
    finally:
        # 커서만 정리 (연결은 캐시되므로 닫지 않음)
        if cur:
            cur.close()


# 카테고리별 데이터 상세 조회
@st.cache_data(ttl=60)  # 1분 캐시
def get_category_data(trainer_id, category):
    """특정 카테고리의 모든 데이터 가져오기"""
    conn = None
    cur = None
    try:
        conn = get_safe_connection()
        cur = conn.cursor()
        
        tables = {
            'QnA': ('data_trainer_qna', ['id', 'question', 'answer', 'category', 'risk_level', 'created_at']),
            '운동 가이드라인': ('data_trainer_workout_guideline', ['id', 'title', 'content', 'category', 'created_at']),
            '식단 가이드라인': ('data_trainer_diet_guideline', ['id', 'title', 'content', 'category', 'created_at']),
            '철학/마인드셋': ('data_trainer_philosophy', ['id', 'content', 'category', 'created_at']),
            '부상 관리': ('data_trainer_injury', ['id', 'title', 'content', 'body_part', 'risk_level', 'keywords', 'created_at']),
            '피드백': ('data_trainer_feedback', ['id', 'user_goal', 'title', 'content', 'category', 'keywords', 'created_at']),
            '식단 예시': ('data_trainer_meal_examples', ['id', 'title', 'content', 'category', 'created_at']),
            '운동 예시': ('data_trainer_workout_examples', ['id', 'title', 'content', 'category', 'user_level', 'created_at']),
            '톤/말투': ('data_trainer_tones_raw', ['id', 'trainer_name', 'raw_data', 'created_at'])
        }

        if category not in tables:
            return pd.DataFrame()
        
        table_name, columns = tables[category]
        
        query = f"""
            SELECT {', '.join(columns)}
            FROM {table_name}
            WHERE trainer_id = %s
            ORDER BY created_at DESC
        """
        cur.execute(query, (trainer_id,))
        rows = cur.fetchall()
        
        df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        st.error(f"데이터 조회 실패: {str(e)}")
        return pd.DataFrame()
    finally:
        # 커서만 정리 (연결은 캐시되므로 닫지 않음)
        if cur:
            cur.close()


# 데이터 삭제
def delete_data(category, data_id):
    """특정 데이터 삭제"""
    conn = get_safe_connection()
    cur = conn.cursor()
    
    tables = {
        'QnA': 'data_trainer_qna',
        '운동 가이드라인': 'data_trainer_workout_guideline',
        '식단 가이드라인': 'data_trainer_diet_guideline',
        '철학/마인드셋': 'data_trainer_philosophy',
        '부상 관리': 'data_trainer_injury',
        '피드백': 'data_trainer_feedback',
        '식단 예시': 'data_trainer_meal_examples',
        '운동 예시': 'data_trainer_workout_examples',
        '톤/말투': 'data_trainer_tones_raw'
    }
    
    if category not in tables:
        return False, "잘못된 카테고리입니다."
    
    try:
        cur.execute(f"DELETE FROM {tables[category]} WHERE id = %s", (data_id,))
        conn.commit()
        cur.close()
        st.cache_data.clear()  # 캐시 초기화
        return True, "✅ 삭제되었습니다!"
    except Exception as e:
        conn.rollback()
        cur.close()
        return False, f"❌ 삭제 실패: {str(e)}"


# 톤 분석/적용 트리거 (백엔드 /admin/analyze_tone 호출)
def trigger_tone_analyze(trainer_id: str):
    base_url = get_backend_base_url()
    url = f"{base_url}/admin/analyze_tone"
    try:
        resp = requests.post(url, params={"trainer_id": trainer_id}, timeout=15)
        if resp.status_code == 200:
            return True, "✅ 톤 분석/적용이 완료되었습니다."
        else:
            return False, f"❌ 톤 분석 실패: {resp.text}"
    except Exception as e:
        return False, f"❌ 톤 분석 요청 오류: {e}"


# 데이터 수정
def update_data(category, data_id, updated_fields):
    """특정 데이터 수정"""
    conn = get_safe_connection()
    cur = conn.cursor()
    
    tables = {
        'QnA': 'data_trainer_qna',
        '운동 가이드라인': 'data_trainer_workout_guideline',
        '식단 가이드라인': 'data_trainer_diet_guideline',
        '철학/마인드셋': 'data_trainer_philosophy',
        '부상 관리': 'data_trainer_injury',
        '피드백': 'data_trainer_feedback',
        '식단 예시': 'data_trainer_meal_examples',
        '운동 예시': 'data_trainer_workout_examples',
        '톤/말투': 'data_trainer_tones_raw'
    }
    
    if category not in tables:
        return False, "잘못된 카테고리입니다."
    
    try:
        # SET 절 생성
        set_clause = ", ".join([f"{key} = %s" for key in updated_fields.keys()])
        values = list(updated_fields.values()) + [data_id]
        
        query = f"UPDATE {tables[category]} SET {set_clause} WHERE id = %s"
        cur.execute(query, values)
        conn.commit()
        cur.close()
        st.cache_data.clear()  # 캐시 초기화
        return True, "✅ 수정되었습니다!"
    except Exception as e:
        conn.rollback()
        cur.close()
        return False, f"❌ 수정 실패: {str(e)}"


# 점수 계산
def calculate_score(current_data):
    # 목표 (Gold 기준)
    target = {
        'QnA': 60,
        '운동 가이드라인': 30,
        '식단 가이드라인': 20,
        '철학/마인드셋': 15,
        '부상 관리': 12,
        '피드백': 10,
        '식단 예시': 15,
        '운동 예시': 20,
        '톤/말투': 8
    }
    
    # 가중치
    weights = {
        'QnA': 0.23,
        '운동 가이드라인': 0.18,
        '식단 가이드라인': 0.13,
        '철학/마인드셋': 0.09,
        '부상 관리': 0.09,
        '피드백': 0.04,
        '식단 예시': 0.04,
        '운동 예시': 0.10,
        '톤/말투': 0.10
    }
    
    total_score = 0
    details = []
    
    for category, current_count in current_data.items():
        target_count = target[category]
        weight = weights[category]
        achievement = min((current_count / target_count) * 100, 100)
        score = achievement * weight
        total_score += score
        
        details.append({
            '카테고리': category,
            '현재': current_count,
            '목표': target_count,
            '달성률': f"{achievement:.0f}%",
            '점수': f"{score:.1f}/{weight*100:.0f}"
        })
    
    # 티어 결정
    if total_score >= 85:
        tier = "🥇 Gold"
        tier_color = "#FFD700"
    elif total_score >= 75:
        tier = "🥈 Silver"
        tier_color = "#C0C0C0"
    elif total_score >= 60:
        tier = "🥉 Bronze"
        tier_color = "#CD7F32"
    else:
        tier = "⚪ 미달"
        tier_color = "#808080"
    
    return total_score, tier, tier_color, details, target


# 데이터 추가
def add_data(trainer_id, category, data_dict):
    conn = get_safe_connection()
    cur = conn.cursor()
    
    try:
        if category == 'QnA':
            cur.execute("""
                INSERT INTO data_trainer_qna (trainer_id, question, answer, category, risk_level, language)
                VALUES (%s, %s, %s, %s, %s, 'ko')
            """, (trainer_id, data_dict['question'], data_dict['answer'], 
                  ['general'], data_dict.get('risk_level', 'low')))
        
        elif category == '운동 가이드라인':
            cur.execute("""
                INSERT INTO data_trainer_workout_guideline (trainer_id, title, content, category, language)
                VALUES (%s, %s, %s, %s, 'ko')
            """, (trainer_id, data_dict['title'], data_dict['content'], ['exercise']))
        
        elif category == '식단 가이드라인':
            cur.execute("""
                INSERT INTO data_trainer_diet_guideline (trainer_id, title, content, category, language)
                VALUES (%s, %s, %s, %s, 'ko')
            """, (trainer_id, data_dict['title'], data_dict['content'], ['diet']))
        
        elif category == '철학/마인드셋':
            cur.execute("""
                INSERT INTO data_trainer_philosophy (trainer_id, content, category, language)
                VALUES (%s, %s, %s, 'ko')
            """, (trainer_id, data_dict['content'], ['mindset']))
        
        elif category == '부상 관리':
            cur.execute("""
                INSERT INTO data_trainer_injury (trainer_id, title, content, body_part, risk_level, keywords, language)
                VALUES (%s, %s, %s, %s, %s, %s, 'ko')
            """, (trainer_id, data_dict['title'], data_dict['content'], 
                  [data_dict['body_part']], data_dict.get('risk_level', 'medium'),
                  data_dict.get('keywords', '').split(',') if data_dict.get('keywords') else []))
        
        elif category == '피드백':
            keywords_list = [k.strip() for k in data_dict.get('keywords', '').split(',') if k.strip()]
            cur.execute("""
                INSERT INTO data_trainer_feedback (trainer_id, user_goal, title, content, category, keywords, language)
                VALUES (%s, %s, %s, %s, %s, %s, 'ko')
            """, (trainer_id, data_dict.get('user_goal', ''), data_dict['title'], 
                  data_dict['content'], [data_dict['feedback_type']], keywords_list))
        
        elif category == '식단 예시':
            cur.execute("""
                INSERT INTO data_trainer_meal_examples (trainer_id, title, content, category, language)
                VALUES (%s, %s, %s, %s, %s, 'ko')
            """, (trainer_id, data_dict['title'], data_dict['content'], 
                  [data_dict['meal_type']], data_dict.get('user_level', 'beginner')))
        
        elif category == '운동 예시':
            cur.execute("""
                INSERT INTO data_trainer_workout_examples (trainer_id, title, content, category, user_level, language)
                VALUES (%s, %s, %s, %s, %s, 'ko')
            """, (trainer_id, data_dict['title'], data_dict['content'], 
                  [data_dict['workout_type']], data_dict.get('user_level', 'beginner')))
        
        elif category == '톤/말투':
            cur.execute("""
                INSERT INTO data_trainer_tones_raw (trainer_id, trainer_name, raw_data)
                VALUES (%s, %s, %s)
            """, (trainer_id, data_dict.get('trainer_name', ''), data_dict['raw_data']))
            
            # 커밋 후 톤 분석 API 호출
            conn.commit()
            cur.close()
            
            # 톤 데이터 자동 분석
            try:
                backend_url = get_backend_base_url()
                response = requests.post(
                    f"{backend_url}/admin/analyze_tone",
                    params={"trainer_id": trainer_id},
                    timeout=30
                )
                if response.status_code == 200:
                    return True, "✅ 톤 데이터가 성공적으로 추가되고 분석되었습니다!"
                else:
                    return True, f"⚠️ 톤 데이터는 저장되었으나 분석 실패: {response.text}"
            except Exception as analyze_error:
                return True, f"⚠️ 톤 데이터는 저장되었으나 분석 API 호출 실패: {str(analyze_error)}"
        
        conn.commit()
        cur.close()
        return True, "✅ 데이터가 성공적으로 추가되었습니다!"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        return False, f"❌ 에러 발생: {str(e)}"


# 메인 앱
def main():
    st.title("💪 트레이너 데이터 관리 대시보드")
    
    # 사이드바 - 트레이너 선택
    with st.sidebar:
        st.header("👤 트레이너 선택")
        trainer_id = st.text_input("Trainer ID", "tr_001")
        
        if st.button("🔄 데이터 새로고침"):
            st.cache_data.clear()
            st.rerun()
    
    # 현재 데이터 가져오기
    current_data = get_current_data(trainer_id)
    total_score, tier, tier_color, details, target = calculate_score(current_data)
    
    # 대시보드 헤더
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("현재 티어", tier)
    
    with col2:
        st.metric("총점", f"{total_score:.1f}/100점")
    
    with col3:
        total_current = sum(current_data.values())
        total_target = sum(target.values())
        st.metric("총 필요 데이터", f"{total_current}/{total_target}개")
    
    with col4:
        next_tier = "Bronze (60점)" if total_score < 60 else "Silver (75점)" if total_score < 75 else "Gold (85점)"
        st.metric("다음 목표", next_tier)
    
    st.divider()
    
    # 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📊 현황", "➕ 데이터 추가", "📝 데이터 관리", "📋 가이드"])
    
    # 탭 1: 현황
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("카테고리별 현황")
            
            # 데이터프레임
            df = pd.DataFrame(details)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 필요한 데이터
            st.subheader("필요한 데이터 (우선순위)")
            
            needed_data = []
            weights_dict = {
                'QnA': 0.23,
                '운동 가이드라인': 0.18,
                '식단 가이드라인': 0.13,
                '철학/마인드셋': 0.09,
                '부상 관리': 0.09,
                '피드백': 0.04,
                '식단 예시': 0.04,
                '운동 예시': 0.10,
                '톤/말투': 0.10
            }
            
            for category in current_data.keys():
                if category in target and category in weights_dict:
                    needed = target[category] - current_data[category]
                    if needed > 0:
                        shortage_ratio = needed / target[category]
                        priority_score = shortage_ratio * weights_dict[category]
                        needed_data.append({
                            '카테고리': category,
                            '필요 개수': f"+{needed}개",
                            '우선순위': priority_score
                        })
            
            needed_data.sort(key=lambda x: x['우선순위'], reverse=True)
            
            for i, item in enumerate(needed_data[:5], 1):
                if i <= 3:
                    priority = "🔴 긴급"
                else:
                    priority = "🟡 중요"
                st.write(f"{priority} **{item['카테고리']}**: {item['필요 개수']}")
        
        with col2:
            st.subheader("점수 시각화")
            
            # 게이지 차트
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=total_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "총점"},
                delta={'reference': 60 if total_score < 60 else 75 if total_score < 75 else 85},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': tier_color},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 75], 'color': "#CD7F32"},
                        {'range': [75, 85], 'color': "#C0C0C0"},
                        {'range': [85, 100], 'color': "#FFD700"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 60 if total_score < 60 else 75 if total_score < 75 else 85
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, width='stretch')
            
            # 카테고리별 막대 차트
            st.subheader("카테고리별 달성률")
            
            categories = []
            achievements = []
            
            for detail in details:
                categories.append(detail['카테고리'])
                achievement = float(detail['달성률'].strip('%'))
                achievements.append(achievement)
            
            fig2 = px.bar(
                x=categories,
                y=achievements,
                labels={'x': '카테고리', 'y': '달성률 (%)'},
                color=achievements,
                color_continuous_scale=['red', 'yellow', 'green']
            )
            fig2.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="목표")
            fig2.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig2, width='stretch')
    
    # 탭 2: 데이터 추가
    with tab2:
        st.subheader("➕ 새로운 데이터 추가")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            category = st.selectbox(
                "카테고리 선택",
                ['QnA', '운동 가이드라인', '식단 가이드라인', '철학/마인드셋', '부상 관리', '피드백', '식단 예시', '운동 예시', '톤/말투']
            )
        
        with col2:
            st.info(f"현재 {category}: {current_data.get(category, 0)}개 / 목표: {target.get(category, 0)}개")
        
        data_dict = {}
        
        if category == 'QnA':
            data_dict['question'] = st.text_input("질문", placeholder="예: 주 몇 회 운동이 적당한가요?")
            data_dict['answer'] = st.text_area("답변", height=200, 
                placeholder="예: 주 3회~5회가 가장 현실적이고 유지하기 좋습니다...")
            data_dict['risk_level'] = st.selectbox("위험 수준", ['low', 'medium', 'high'])
        
        elif category in ['운동 가이드라인', '식단 가이드라인']:
            data_dict['title'] = st.text_input("제목", placeholder="예: 집에서 할 수 있는 스쿼트 가이드")
            data_dict['content'] = st.text_area("내용", height=300,
                placeholder="1. 자세: 발을 어깨 너비로...\n2. 동작: 엉덩이를 뒤로...\n3. 주의사항: 무릎이...")
        
        elif category == '철학/마인드셋':
            data_dict['content'] = st.text_area("내용", height=200,
                placeholder="예: 운동은 단순한 숙제가 아니라 '나'라는 캐릭터를 성장시키는 과정입니다...")
        
        elif category == '부상 관리':
            data_dict['title'] = st.text_input("제목", placeholder="예: 무릎 통증 시 대처법")
            data_dict['content'] = st.text_area("내용", height=200)
            data_dict['body_part'] = st.selectbox("부위", ['무릎', '어깨', '허리', '손목', '발목', '팔꿈치', '기타'])
            data_dict['risk_level'] = st.selectbox("위험 수준", ['low', 'medium', 'high'])
            data_dict['keywords'] = st.text_input("키워드 (쉼표로 구분)", placeholder="예: 무릎,통증,부상")
        
        elif category == '피드백':
            data_dict['user_goal'] = st.selectbox("사용자 목표", 
                ['체중 감량', '근육 증가', '체력 향상', '건강 유지', '재활/회복', '체형 교정'])
            data_dict['title'] = st.text_input("제목", placeholder="예: 고단백 식단에 대한 피드백")
            data_dict['content'] = st.text_area("피드백 내용", height=200,
                placeholder="예:\n긍정적인 부분:\n- 단백질 섭취가 충분합니다\n- 식사 간격이 적절합니다\n\n개선이 필요한 부분:\n- 탄수화물을 현미로 바꾸세요\n- 채소 섭취를 늘리세요")
            data_dict['feedback_type'] = st.selectbox("피드백 유형", ['diet', 'workout', 'lifestyle'])
            data_dict['keywords'] = st.text_input("키워드 (쉼표로 구분)", placeholder="예: 고단백,저칼로리")
        
        elif category == '식단 예시':
            data_dict['meal_type'] = st.selectbox("식사 유형", ['아침', '점심', '저녁', '간식'])
            data_dict['title'] = st.text_input("제목", placeholder="예: 고단백 저칼로리 아침 식사")
            data_dict['content'] = st.text_area("식단 내용 (음식, 칼로리, 영양소 포함)", height=200,
                placeholder="예:\n음식:\n- 계란 2개 (140kcal, 단백질 12g)\n- 통밀빵 1조각 (80kcal, 단백질 4g)\n- 아보카도 1/2개 (120kcal)\n- 방울토마토 5개 (20kcal)\n\n총 칼로리: 360kcal\n총 단백질: 16g")
            data_dict['user_level'] = st.selectbox("난이도", ['beginner', 'intermediate', 'advanced'])
        
        elif category == '운동 예시':
            data_dict['workout_type'] = st.selectbox("운동 유형", ['상체', '하체', '전신', '유산소', '스트레칭'])
            data_dict['title'] = st.text_input("제목", placeholder="예: 집에서 하는 전신 운동")
            data_dict['content'] = st.text_area("운동 내용 (운동 목록, 시간 포함)", height=200,
                placeholder="예:\n운동 목록:\n1. 푸쉬업 15회 x 3세트\n2. 스쿼트 20회 x 3세트\n3. 플랭크 30초 x 3세트\n4. 버피 10회 x 3세트\n\n총 예상 시간: 30분\n휴식 시간: 세트 간 60초")
            data_dict['user_level'] = st.selectbox("난이도", ['beginner', 'intermediate', 'advanced'])
        
        elif category == '톤/말투':
            data_dict['trainer_name'] = st.text_input("트레이너 이름 (선택)", placeholder="예: 김철수 트레이너")
            data_dict['raw_data'] = st.text_area("톤/말투 원본 데이터", height=300,
                placeholder="트레이너의 말투, 어투, 특징적인 표현 방식을 자유롭게 작성하세요.\n\n예시:\n- 반말 사용, 친근한 말투\n- '~해보자', '~는 게 좋아' 같은 권유형 표현\n- 이모지 적극 활용 💪\n- 긍정적이고 동기부여하는 톤\n- 전문 용어보다 쉬운 표현 선호\n\n또는 실제 대화 예시를 여러 개 작성해도 좋습니다.")
            st.info("💡 팁: 트레이너의 실제 대화 스타일, 자주 쓰는 표현, 특징적인 말투를 구체적으로 작성하면 챗봇이 더 자연스럽게 응답합니다.")
        
        st.divider()
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("💾 저장하기", type="primary", use_container_width=True):
                # 필수 필드 검증
                required_fields = {
                    'QnA': ['question', 'answer'],
                    '운동 가이드라인': ['title', 'content'],
                    '식단 가이드라인': ['title', 'content'],
                    '철학/마인드셋': ['content'],
                    '부상 관리': ['title', 'content', 'body_part'],
                    '피드백': ['title', 'content', 'feedback_type'],
                    '식단 예시': ['meal_type', 'title', 'content'],
                    '운동 예시': ['workout_type', 'title', 'content'],
                    '톤/말투': ['raw_data']
                }
                
                missing = [field for field in required_fields[category] if not data_dict.get(field)]
                
                if missing:
                    st.error(f"❌ 필수 필드가 비어있습니다: {', '.join(missing)}")
                else:
                    success, message = add_data(trainer_id, category, data_dict)
                    if success:
                        st.success(message)
                        st.balloons()
                        
                        # 점수 업데이트
                        new_data = get_current_data(trainer_id)
                        new_score, new_tier, _, _, _ = calculate_score(new_data)
                        
                        if new_tier != tier:
                            st.success(f"🎉 축하합니다! 티어가 **{tier}** → **{new_tier}**로 상승했습니다!")
                        
                        score_diff = new_score - total_score
                        st.info(f"📊 점수가 **{score_diff:.1f}점** 상승했습니다! ({total_score:.1f}점 → {new_score:.1f}점)")
                        
                        st.button("🔄 새로고침하기", on_click=lambda: st.rerun())
                    else:
                        st.error(message)
        
        with col2:
            st.caption("💡 팁: 구체적이고 실행 가능한 내용을 작성하세요 (100-500자 권장)")
    
    # 탭 3: 데이터 관리
    with tab3:
        st.subheader("📝 기존 데이터 관리")
        
        # 카테고리 선택
        col1, col2 = st.columns([1, 3])
        
        with col1:
            manage_category = st.selectbox(
                "카테고리 선택",
                ['QnA', '운동 가이드라인', '식단 가이드라인', '철학/마인드셋', '부상 관리', '피드백', '식단 예시', '운동 예시', '톤/말투'],
                key='manage_category'
            )
        
        with col2:
            st.info(f"현재 {manage_category}: {current_data.get(manage_category, 0)}개")
        
        # 데이터 조회
        df = get_category_data(trainer_id, manage_category)
        
        if df.empty:
            st.warning(f"⚠️ {manage_category} 데이터가 없습니다. '➕ 데이터 추가' 탭에서 추가해주세요.")
        else:
            st.success(f"✅ 총 {len(df)}개의 데이터를 찾았습니다.")
            
            # 톤/말투 카테고리일 때 톤 분석/적용 버튼 제공
            if manage_category == '톤/말투':
                col_analyze, col_refresh = st.columns([1, 1])
                with col_analyze:
                    if st.button("🔄 톤 분석/적용 (raw → analyzed)", use_container_width=True):
                        ok, msg = trigger_tone_analyze(trainer_id)
                        if ok:
                            st.success(msg)
                            st.cache_data.clear()  # 캐시 초기화
                        else:
                            st.error(msg)
                with col_refresh:
                    st.button("🔄 새로고침", on_click=lambda: st.rerun(), use_container_width=True)
            
            # 데이터 표시
            for idx, row in df.iterrows():
                # with st.expander(f"🔍 ID: {row['id']} | {row.get('title', row.get('question', '내용'))[:50]}...", expanded=False):
                display_text = row.get('title', row.get('question', row.get('raw_data', row.get('content', '내용'))))
                with st.expander(f"🔍 {display_text[:50]}", expanded=False):

                    # 수정 폼
                    with st.form(key=f"edit_form_{row['id']}"):
                        updated_fields = {}
                        
                        if manage_category == 'QnA':
                            updated_fields['question'] = st.text_input("질문", value=row['question'], key=f"q_{row['id']}")
                            updated_fields['answer'] = st.text_area("답변", value=row['answer'], height=150, key=f"a_{row['id']}")
                            updated_fields['risk_level'] = st.selectbox("위험 수준", ['low', 'medium', 'high'], 
                                                                        index=['low', 'medium', 'high'].index(row['risk_level']), 
                                                                        key=f"r_{row['id']}")
                        
                        elif manage_category in ['운동 가이드라인', '식단 가이드라인']:
                            updated_fields['title'] = st.text_input("제목", value=row['title'], key=f"t_{row['id']}")
                            updated_fields['content'] = st.text_area("내용", value=row['content'], height=200, key=f"c_{row['id']}")
                        
                        elif manage_category == '철학/마인드셋':
                            updated_fields['content'] = st.text_area("내용", value=row['content'], height=150, key=f"c_{row['id']}")
                        
                        elif manage_category == '부상 관리':
                            updated_fields['title'] = st.text_input("제목", value=row['title'], key=f"t_{row['id']}")
                            updated_fields['content'] = st.text_area("내용", value=row['content'], height=150, key=f"c_{row['id']}")
                            
                            # body_part가 리스트인 경우 첫 번째 요소만 사용
                            body_part_value = row['body_part']
                            if isinstance(body_part_value, list):
                                body_part_value = body_part_value[0] if body_part_value else '기타'
                            
                            body_parts = ['무릎', '어깨', '허리', '손목', '발목', '팔꿈치', '기타']
                            body_part_index = body_parts.index(body_part_value) if body_part_value in body_parts else 6
                            
                            updated_fields['body_part'] = [st.selectbox("부위", body_parts, 
                                                                        index=body_part_index, 
                                                                        key=f"bp_{row['id']}")]
                            updated_fields['risk_level'] = st.selectbox("위험 수준", ['low', 'medium', 'high'], 
                                                                        index=['low', 'medium', 'high'].index(row['risk_level']), 
                                                                        key=f"r_{row['id']}")
                        
                        elif manage_category == '피드백':
                            user_goals = ['체중 감량', '근육 증가', '체력 향상', '건강 유지', '재활/회복', '체형 교정']
                            current_goal = row.get('user_goal', '체중 감량')
                            goal_index = user_goals.index(current_goal) if current_goal in user_goals else 0
                            updated_fields['user_goal'] = st.selectbox("사용자 목표", user_goals, index=goal_index, key=f"ug_{row['id']}")
                            updated_fields['title'] = st.text_input("제목", value=row.get('title', ''), key=f"t_{row['id']}")
                            updated_fields['content'] = st.text_area("피드백 내용", value=row.get('content', ''), height=200, key=f"c_{row['id']}")
                            
                            # category가 리스트인 경우 첫 번째 항목 사용
                            current_type = row.get('category', ['diet'])[0] if isinstance(row.get('category'), list) else 'diet'
                            updated_fields['feedback_type'] = st.selectbox("피드백 유형", ['diet', 'workout', 'lifestyle'], 
                                                                          index=['diet', 'workout', 'lifestyle'].index(current_type) if current_type in ['diet', 'workout', 'lifestyle'] else 0,
                                                                          key=f"ft_{row['id']}")
                            
                            # keywords가 리스트인 경우 쉼표로 연결
                            keywords_value = row.get('keywords', [])
                            if isinstance(keywords_value, list):
                                keywords_value = ','.join(keywords_value)
                            updated_fields['keywords'] = st.text_input("키워드 (쉼표로 구분)", value=keywords_value, key=f"kw_{row['id']}")
                        
                        elif manage_category == '식단 예시':
                            meal_types = ['아침', '점심', '저녁', '간식']
                            # category가 리스트인 경우 첫 번째 항목 사용
                            current_meal_type = row.get('category', ['아침'])[0] if isinstance(row.get('category'), list) else '아침'
                            updated_fields['meal_type'] = st.selectbox("식사 유형", meal_types, 
                                                                       index=meal_types.index(current_meal_type) if current_meal_type in meal_types else 0,
                                                                       key=f"mt_{row['id']}")
                            updated_fields['title'] = st.text_input("제목", value=row.get('title', ''), key=f"t_{row['id']}")
                            updated_fields['content'] = st.text_area("식단 내용", value=row.get('content', ''), height=200, key=f"c_{row['id']}")
                            
                            user_levels = ['beginner', 'intermediate', 'advanced']
                            current_level = row.get('user_level', 'beginner')
                            updated_fields['user_level'] = st.selectbox("난이도", user_levels,
                                                                        index=user_levels.index(current_level) if current_level in user_levels else 0,
                                                                        key=f"ul_{row['id']}")
                        
                        elif manage_category == '운동 예시':
                            workout_types = ['상체', '하체', '전신', '유산소', '스트레칭']
                            # category가 리스트인 경우 첫 번째 항목 사용
                            current_workout_type = row.get('category', ['전신'])[0] if isinstance(row.get('category'), list) else '전신'
                            updated_fields['workout_type'] = st.selectbox("운동 유형", workout_types,
                                                                          index=workout_types.index(current_workout_type) if current_workout_type in workout_types else 0,
                                                                          key=f"wt_{row['id']}")
                            updated_fields['title'] = st.text_input("제목", value=row.get('title', ''), key=f"t_{row['id']}")
                            updated_fields['content'] = st.text_area("운동 내용", value=row.get('content', ''), height=200, key=f"c_{row['id']}")
                            
                            user_levels = ['beginner', 'intermediate', 'advanced']
                            current_level = row.get('user_level', 'beginner')
                            updated_fields['user_level'] = st.selectbox("난이도", user_levels,
                                                                        index=user_levels.index(current_level) if current_level in user_levels else 0,
                                                                        key=f"ul_{row['id']}")
                        
                        elif manage_category == '톤/말투':
                            updated_fields['trainer_name'] = st.text_input("트레이너 이름", value=row.get('trainer_name', ''), key=f"tn_{row['id']}")
                            updated_fields['raw_data'] = st.text_area("톤/말투 원본 데이터", value=row.get('raw_data', ''), height=300, key=f"rd_{row['id']}")
                        
                        st.markdown("---")
                        col1, col2, col3 = st.columns([1, 1, 3])
                        
                        with col1:
                            submit_update = st.form_submit_button("💾 수정", type="primary", use_container_width=True)
                        
                        with col2:
                            submit_delete = st.form_submit_button("🗑️ 삭제", type="secondary", use_container_width=True)
                        
                        if submit_update:
                            # 특수 필드 처리
                            if manage_category == '피드백':
                                # keywords를 리스트로 변환
                                if 'keywords' in updated_fields and isinstance(updated_fields['keywords'], str):
                                    updated_fields['keywords'] = [k.strip() for k in updated_fields['keywords'].split(',') if k.strip()]
                                # feedback_type를 category로 변환
                                if 'feedback_type' in updated_fields:
                                    updated_fields['category'] = [updated_fields.pop('feedback_type')]
                            
                            elif manage_category == '식단 예시':
                                # meal_type를 category로 변환
                                if 'meal_type' in updated_fields:
                                    updated_fields['category'] = [updated_fields.pop('meal_type')]
                            
                            elif manage_category == '운동 예시':
                                # workout_type를 category로 변환
                                if 'workout_type' in updated_fields:
                                    updated_fields['category'] = [updated_fields.pop('workout_type')]
                            
                            success, message = update_data(manage_category, row['id'], updated_fields)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        
                        if submit_delete:
                            # 삭제 확인
                            if st.session_state.get(f'confirm_delete_{row["id"]}', False):
                                success, message = delete_data(manage_category, row['id'])
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.session_state[f'confirm_delete_{row["id"]}'] = True
                                st.warning("⚠️ 다시 한 번 '삭제' 버튼을 클릭하면 영구 삭제됩니다!")
    
    # 탭 4: 가이드
    with tab4:
        st.subheader("📋 데이터 작성 가이드")
        
        st.markdown("""
        ### ✅ 좋은 데이터 5가지 요소
        
        1. **구체적**: "열심히 운동하세요" ❌ → "스쿼트 15회 x 3세트, 주 3회" ✅
        2. **실행 가능**: 누구나 따라할 수 있게
        3. **안전**: 주의사항 포함
        4. **대상 명확**: "초보자는", "중급자는"
        5. **적절한 길이**: 100-500자
        
        ### 📊 티어 시스템
        
        - 🥉 **Bronze (60점)**: 챗봇 활성화 가능
        - 🥈 **Silver (75점)**: 권장 수준
        - 🥇 **Gold (85점)**: 우수 수준
        
        ### 🎯 우선순위
        
        1. **QnA**: 가장 중요! (23% 가중치)
        2. **운동 가이드라인**: 핵심 콘텐츠 (18% 가중치)
        3. **식단 가이드라인**: 중요 (13% 가중치)
        4. **톤/말투**: 챗봇 개성화 (10% 가중치) - 트레이너의 말투와 대화 스타일을 정의
        
        ### 💬 톤/말투 작성 가이드
        
        트레이너의 고유한 대화 스타일을 작성하세요:
        - 반말/존댓말 사용 여부
        - 자주 쓰는 표현이나 말버릇
        - 이모지 사용 스타일
        - 긍정적/동기부여적 톤
        - 실제 대화 예시 (추천)
        
        상세 가이드는 [TRAINER_GUIDELINE.md](./TRAINER_GUIDELINE.md)를 참고하세요.
        """)


if __name__ == "__main__":
    main()

