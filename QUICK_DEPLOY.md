# ⚡ 5분 안에 배포하기

> 트레이너에게 웹 링크로 대시보드 공유

---

## 🚀 빠른 배포 (5분)

### 1️⃣ GitHub 업로드 (2분)

```bash
cd /Users/louissong/Documents/projects/fitness_chatbot

# 커밋
git add llamaInd_cbot/
git commit -m "Add trainer dashboard"

# Push (본인 저장소)
git push origin main
```

---

### 2️⃣ Streamlit Cloud 배포 (2분)

1. **https://streamlit.io/cloud** 접속
2. **"New app"** 클릭
3. **저장소 선택:**

   - Repository: `YOUR_USERNAME/fitness_chatbot`
   - Branch: `main`
   - Main file: `llamaInd_cbot/trainer_dashboard.py`

4. **Advanced settings → Secrets:**

   ```toml
   [database]
   DB_HOST = "your-db-host"
   DB_PORT = "5432"
   DB_NAME = "your-db-name"
   DB_USER = "your-username"
   DB_PASSWORD = "your-password"
   ```

5. **"Deploy!"** 클릭

---

### 3️⃣ 완료! (1분)

**URL 받기:**

```
✅ https://your-app.streamlit.app
```

**트레이너에게 전달:**

```
안녕하세요!

대시보드가 준비되었습니다:
🌐 https://your-app.streamlit.app

사용 방법:
1. 위 링크 접속
2. Trainer ID 입력
3. 데이터 추가하고 실시간으로 점수 확인!

문의: support@yourdomain.com
```

---

## 📱 결과

- ✅ **PC에서** 접속 가능
- ✅ **모바일에서** 접속 가능
- ✅ **언제든지** 데이터 추가 가능
- ✅ **실시간으로** 점수 확인 가능

---

## 🔄 업데이트

코드 수정 후:

```bash
git add .
git commit -m "Update"
git push

# 1분 후 자동으로 웹사이트 업데이트!
```

---

**끝!** 🎉
