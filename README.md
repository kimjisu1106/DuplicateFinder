# 📸 DuplicateFinder

**중복 파일 탐지 및 정리 데스크탑 앱**

수만 장의 사진, 영상, 오디오 파일이 쌓인 드라이브를 빠르게 정리하세요.
완전히 동일한 파일과 유사한 이미지를 자동으로 찾아내고, 나란히 비교한 뒤 안전하게 삭제할 수 있습니다.

---

## ✨ 주요 기능

- **완전 중복 탐지** — MD5 해시로 내용이 100% 동일한 파일 그룹화 (파일명 무관)
- **유사 이미지 탐지** — pHash 알고리즘으로 크기나 편집이 다소 다른 사진도 감지
- **이미지 / 영상 / 오디오 / 전체 파일** 지원 — 확장자 무관 전체 파일 MD5 스캔 가능
- **안전한 삭제** — 휴지통으로 이동 (복구 가능), 확인 다이얼로그 필수
- **대용량 폴더 대응** — 백그라운드 스캔, 일시중지/재개, GUI 프리징 없음
- **원본 자동 추천** — 해상도 → 파일 크기 → 날짜 기준으로 원본 선정
- **다중 그룹 선택** — Ctrl+클릭 / Shift+클릭으로 여러 그룹 일괄 처리
- **한/영 언어 전환** — 앱 우측 상단 버튼으로 즉시 전환

---

## 🖥️ 스크린샷

> 추후 추가 예정

---

## 📦 설치 및 실행

### 일반 사용자 (Windows)

1. [Releases](../../releases) 에서 `DuplicateFinder.exe` 다운로드
2. 실행 (설치 불필요)

### 개발자

```bash
git clone https://github.com/kimlog0415/DuplicateFinder.git
cd DuplicateFinder
pip install -r requirements.txt
python main.py
```

**요구사항:** Python 3.10+

---

## 🔍 사용 방법

1. **폴더 선택** — 스캔할 폴더를 선택하세요
2. **옵션 설정** — 검색 대상(이미지/영상/오디오/전체 파일), 하위 폴더 포함 여부, 유사 이미지 검색 여부 및 민감도 조절
3. **스캔 시작** — 진행률과 남은 시간이 실시간으로 표시됩니다. 일시중지/재개/취소 가능
4. **결과 확인** — 완전 중복 / 유사 중복 탭에서 그룹별로 파일 비교
5. **삭제** — 원본 유지 버튼으로 자동 선택 후 일괄 삭제, 또는 직접 체크. Ctrl/Shift+클릭으로 여러 그룹 한 번에 처리 가능

---

## ⚙️ 의존성

| 라이브러리 | 용도 |
|---|---|
| [Pillow](https://pillow.readthedocs.io) | 이미지 처리 및 썸네일 생성 |
| [ImageHash](https://github.com/JohannesBuchner/imagehash) | 유사 이미지 감지 (pHash) |
| [Send2Trash](https://github.com/arsenetar/send2trash) | 파일을 휴지통으로 이동 |

---

## 🔒 보안

- **완전 로컬 동작** — 네트워크 요청 없음, 인터넷 연결 불필요
- **읽기 + 휴지통 이동만 허용** — 파일 직접 삭제(`os.remove`) 미사용
- **경로 탈출 방지** — 스캔 범위를 선택한 폴더 내부로만 제한

---

## ☕ 후원

앱이 유용하셨다면 커피 한 잔 후원해 주세요!

👉 [후원하기](https://kimlog0415.github.io/contact/)

---

## 📬 문의

버그 리포트, 기능 제안 → [Issues](../../issues)

기타 문의 → [kimlog0415.github.io/contact](https://kimlog0415.github.io/contact/)

---

## 📄 라이선스

MIT License

---

<details>
<summary>🇺🇸 English</summary>

## DuplicateFinder

A desktop app for detecting and cleaning up duplicate files.

Quickly find and remove exact duplicates and visually similar images from your drives.

### Features

- **Exact duplicate detection** — MD5 hash comparison (filename-independent)
- **Similar image detection** — pHash algorithm for slightly edited or resized photos
- **Image / Video / Audio / All files** support — scan all file types by MD5 regardless of extension
- **Safe deletion** — moves to Trash only, confirmation dialog required
- **Large folder support** — background scan with pause/resume, no GUI freezing
- **Auto original detection** — ranked by resolution → file size → date
- **Multi-group selection** — Ctrl+click / Shift+click for bulk processing
- **Korean / English UI** — toggle language instantly from the top bar

### Installation

**Windows users:** Download `DuplicateFinder.exe` from [Releases](../../releases)

**Developers:**
```bash
git clone https://github.com/kimlog0415/DuplicateFinder.git
cd DuplicateFinder
pip install -r requirements.txt
python main.py
```

Requires Python 3.10+

### Usage

1. **Select folder** — choose the folder to scan
2. **Set options** — target file types, include subfolders, similar image search and sensitivity
3. **Start scan** — real-time progress and ETA displayed. Pause/resume/cancel available
4. **Review results** — compare files in Exact Duplicates / Similar tabs
5. **Delete** — use "Keep original" for auto-selection, or check manually. Ctrl/Shift+click to bulk process multiple groups

### Security

- Fully local — no network requests
- Only reads files and moves to Trash (no direct deletion)
- Scan scope is strictly limited to the selected folder

</details>
