# youtube-manage-dashboard (공개 repo)

유튜브 채널 관리 웹 대시보드 + 일일 자동 수집기. **공개(Public)** repo로 두고
GitHub Pages로 무료 호스팅합니다. 여기에는 유튜브에 이미 공개된 자료
(구독자·조회수·업로드시각 등)만 들어갑니다.

민감한 회원 개인정보는 별도 비공개 repo `youtube-manage-core`에 보관합니다.

## 구성
- `index.html` — 대시보드 화면 (채널 현황 + 추이 그래프)
- `collect.py` — 일일 수집기 (GitHub Actions가 자동 실행)
- `channels.json` — 관리할 채널 목록 (터미널 `manage.py`로 편집)
- `manage.py` — 채널 추가/삭제 도구
- `data/` — 수집 결과 (자동 갱신, 직접 손대지 않음)
- `.github/workflows/daily.yml` — 매일 자동 수집 (별도 토큰 불필요)

## 처음 세팅
1. 이 폴더를 **공개(Public)** GitHub repo로 push
2. 유튜브 API 키 발급 (무료): https://console.cloud.google.com
   → YouTube Data API v3 사용 설정 → API 키 만들기
3. repo → Settings → Secrets and variables → Actions → New repository secret
   - 이름 `YOUTUBE_API_KEY`, 값 = 발급받은 키
4. repo → Settings → Pages → Branch `main` / `/ (root)` → Save
   → 주소 `https://본인이름.github.io/youtube-manage-dashboard/`
5. repo → Actions → `daily-collect` → **Run workflow** 로 즉시 1회 수집 테스트

이후 매일 한국시간 오전 9시 자동 수집됩니다.

## 채널 관리 (터미널)
```
python manage.py list
python manage.py add --handle @채널핸들 --name "표시이름"
python manage.py add --id UCxxxxxxxx --name "표시이름"
python manage.py remove --id UCxxxxxxxx
git add -A && git commit -m "채널 갱신" && git push
```

## 비밀번호 보호
`index.html` 의 `PW_PLAIN = "changeme"` 를 원하는 비밀번호로 변경.
정적 사이트라 강력하진 않습니다(단순 접근 차단용). 강한 보안이 필요하면
무료 Cloudflare Access를 앞단에 붙이는 방법이 있습니다.

## 로컬 테스트
```
# PowerShell
$env:YOUTUBE_API_KEY="발급받은키"
python collect.py
```
그 뒤 `index.html`을 브라우저로 열어 결과 확인.

## 무료 한도
- YouTube API: 하루 10,000 쿼터 (채널 수십 개 × 하루 1회면 여유)
- GitHub Actions: 공개 repo는 무료
- GitHub Pages: 공개 repo는 무료
