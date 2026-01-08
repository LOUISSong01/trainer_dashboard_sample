# 트레이너 대시보드 배포 가이드

> 트레이너에게 웹 링크로 대시보드를 공유하는 방법

---

## 🚀 Streamlit Cloud 배포 (무료, 추천)

### 준비물

- ✅ GitHub 계정
- ✅ Streamlit Cloud 계정 (GitHub로 가입)
- ✅ PostgreSQL 데이터베이스 (현재 DB 사용)

---

## 📋 배포 단계

### Step 1: GitHub에 코드 업로드

```bash
cd /Users/louissong/Documents/projects/fitness_chatbot

# Git 초기화 (아직 안했으면)
git init
git add llamaInd_cbot/

# 커밋
git commit -m "Add trainer dashboard"

# GitHub 저장소 연결 (본인의 저장소)
git remote add origin https://github.com/YOUR_USERNAME/fitness_chatbot.git
git push -u origin main
```

**⚠️ 중요:** `.env` 파일은 절대 GitHub에 올리지 마세요!

`.gitignore` 확인:

```
.env
.streamlit/secrets.toml
```

---

### Step 2: Streamlit Cloud 가입

1. https://streamlit.io/cloud 접속
2. "Sign up" 클릭
3. GitHub 계정으로 가입
4. 이메일 인증

---

### Step 3: 앱 배포

1. **"New app" 버튼 클릭**

2. **저장소 선택**

   ```
   Repository: YOUR_USERNAME/fitness_chatbot
   Branch: main
   Main file path: llamaInd_cbot/trainer_dashboard.py
   ```

3. **"Advanced settings" 클릭**

4. **Python 버전 선택**

   ```
   Python version: 3.11
   ```

5. **Secrets 추가**

   "Secrets" 섹션에 다음 내용 입력:

   ```toml
   [database]
   DB_HOST = "your-db-host.com"
   DB_PORT = "5432"
   DB_NAME = "your-database-name"
   DB_USER = "your-username"
   DB_PASSWORD = "your-password"
   ```

   **본인의 실제 DB 정보를 입력하세요!**

6. **"Deploy!" 버튼 클릭**

---

### Step 4: 배포 완료!

3-5분 후 배포 완료:

```
✅ 배포 완료!
🌐 URL: https://your-app-name.streamlit.app
```

이 URL을 트레이너에게 공유하세요!

---

## 🔐 보안 설정

### 1. 비밀번호 추가 (선택사항)

트레이너만 접근하도록 비밀번호 보호:

`trainer_dashboard.py` 상단에 추가:

```python
def check_password():
    """간단한 비밀번호 인증"""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("비밀번호", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("비밀번호", type="password", on_change=password_entered, key="password")
        st.error("😕 비밀번호가 틀렸습니다")
        return False
    else:
        return True

# main() 함수 시작 부분에 추가
if not check_password():
    st.stop()
```

그리고 Secrets에 추가:

```toml
password = "your-secure-password"
```

### 2. IP 제한 (유료 플랜)

Streamlit Cloud의 Team 플랜($250/월)에서 가능합니다.

---

## 🌐 커스텀 도메인 (선택사항)

### 무료 도메인

```
https://trainer-dashboard-fitness.streamlit.app
```

### 커스텀 도메인 ($20/월)

```
https://trainer.yourdomain.com
```

Streamlit Cloud의 설정에서 커스텀 도메인 추가 가능

---

## 📊 모니터링

### Streamlit Cloud 대시보드에서:

1. **앱 상태 확인**

   - 실행 중 / 중지
   - 마지막 배포 시간

2. **로그 확인**

   - 에러 메시지
   - 사용자 접속 로그

3. **리소스 사용량**
   - CPU 사용률
   - 메모리 사용량

---

## 🔄 자동 배포

GitHub에 push하면 자동으로 재배포됩니다!

```bash
# 코드 수정 후
git add .
git commit -m "Update dashboard"
git push

# 1-2분 후 자동으로 웹사이트 업데이트!
```

---

## 💰 비용

### Streamlit Cloud

| 플랜       | 가격     | 특징                                                 |
| ---------- | -------- | ---------------------------------------------------- |
| Community  | **무료** | - Public 저장소<br>- 1GB RAM<br>- 1 CPU<br>- 충분함! |
| Team       | $250/월  | - Private 저장소<br>- IP 제한<br>- 4GB RAM           |
| Enterprise | 협의     | - On-premise 가능                                    |

**대부분의 경우 무료 플랜으로 충분합니다!**

---

## 🛠️ 대안: Railway.app 배포

Railway는 Private 저장소도 무료로 지원합니다!

### 장점

- ✅ Private 저장소 무료
- ✅ PostgreSQL 무료 제공
- ✅ 매달 $5 크레딧 무료
- ✅ 커스텀 도메인 무료

### 배포 방법

1. https://railway.app 접속
2. "Start a New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. 저장소 선택
5. 환경 변수 추가:
   ```
   DB_HOST=xxx
   DB_PORT=5432
   DB_NAME=xxx
   DB_USER=xxx
   DB_PASSWORD=xxx
   ```
6. Deploy!

**URL:** `https://your-app.railway.app`

---

## 📱 트레이너 사용 가이드

배포 후 트레이너에게 전달할 내용:

```
안녕하세요!

트레이너님의 챗봇 데이터를 관리할 수 있는 대시보드가 준비되었습니다.

🌐 접속 링크: https://your-app.streamlit.app

📋 사용 방법:
1. 위 링크 접속
2. Trainer ID 입력: trainer_XXX
3. "현황" 탭에서 현재 점수 확인
4. "데이터 추가" 탭에서 새로운 데이터 입력
5. 실시간으로 점수 변화 확인!

🎯 목표:
- 60점 이상: 챗봇 활성화 가능
- 75점 이상: 권장 수준
- 85점 이상: 우수 수준

❓ 문제 발생 시:
- 이메일: support@yourdomain.com
- 전화: 010-XXXX-XXXX

행운을 빕니다! 💪
```

---

## 🐛 트러블슈팅

### 1. "Failed to load secrets"

**원인:** Secrets가 제대로 설정되지 않음

**해결:**

1. Streamlit Cloud 대시보드 접속
2. 앱 선택 → Settings → Secrets
3. 올바른 형식으로 다시 입력

---

### 2. "Connection refused" (DB 연결 실패)

**원인:** DB가 외부 접속을 허용하지 않음

**해결:**

1. PostgreSQL 설정에서 외부 접속 허용
2. 방화벽 설정 확인
3. Streamlit Cloud IP를 화이트리스트에 추가

---

### 3. "Module not found"

**원인:** requirements.txt가 없거나 잘못됨

**해결:**

1. `requirements_dashboard.txt`를 `requirements.txt`로 복사
2. GitHub에 push

---

### 4. 앱이 너무 느림

**원인:** 무료 플랜의 리소스 제한

**해결:**

1. `@st.cache_data`, `@st.cache_resource` 적극 사용
2. DB 쿼리 최적화
3. 유료 플랜 고려 (Team: $250/월)

---

## ✅ 체크리스트

배포 전 확인사항:

- [ ] `.env` 파일이 `.gitignore`에 있음
- [ ] `requirements_dashboard.txt` 존재
- [ ] DB가 외부 접속 허용
- [ ] GitHub 저장소 생성
- [ ] 코드 push 완료
- [ ] Streamlit Cloud 가입
- [ ] Secrets 설정 완료
- [ ] 배포 완료
- [ ] URL 테스트
- [ ] 트레이너에게 공유

---

## 🎉 완료!

이제 트레이너가 언제 어디서든 웹 브라우저로 데이터를 관리할 수 있습니다!

**배포 후 URL 예시:**

```
https://fitness-trainer-dashboard.streamlit.app
```

**모바일에서도 작동합니다!** 📱

---

## 📞 지원

배포 중 문제가 발생하면:

- 📧 Streamlit 지원: support@streamlit.io
- 💬 Streamlit 포럼: https://discuss.streamlit.io
- 📚 문서: https://docs.streamlit.io

---

**Happy Deploying! 🚀**
