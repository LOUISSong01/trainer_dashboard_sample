# ⚡ 빠른 시작

## 로컬 개발 (5분)

```bash
# 1. 클론
git clone https://github.com/YOUR_USERNAME/trainer-dashboard.git
cd trainer-dashboard

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
cp env.example .env
# .env 파일 열어서 DB 정보 입력

# 4. 실행
streamlit run app.py
```

## 배포 (5분)

1. **GitHub Push**
   ```bash
   git push origin main
   ```

2. **Streamlit Cloud**
   - https://streamlit.io/cloud 접속
   - "New app" → 저장소 선택 → `app.py`
   - Secrets 추가 (DB 정보)
   - "Deploy!"

3. **완료!**
   ```
   ✅ https://your-app.streamlit.app
   ```

---

## 트레이너 사용법

1. 링크 접속
2. Trainer ID 입력
3. "데이터 추가" 탭
4. 폼 작성 및 저장
5. 실시간 점수 확인!

---

**상세 가이드:**
- 📚 [README.md](./README.md)
- 🚀 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

