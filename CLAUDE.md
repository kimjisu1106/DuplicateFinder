# 📸 DuplicateFinder — CLAUDE.md

## 프로젝트 개요

특정 폴더를 스캔해서 **완전히 동일한 파일**과 **유사한 이미지**를 찾아내고,
나란히 비교한 뒤 삭제할 수 있는 데스크탑 GUI 앱.

| 항목 | 내용 |
|---|---|
| 언어 | Python 3.10+ |
| GUI | Tkinter (내장, 설치 불필요) |
| 실행 | `python main.py` |
| 배포 | `dist/DuplicateFinder.exe` (PyInstaller, ~53MB) |
| 최초 구현 | 2026-03-22 |
| 마지막 업데이트 | 2026-03-28 |

---

## 요약

- Python Tkinter 기반 로컬 파일 중복 탐지 데스크탑 앱
- MD5 해시(완전 동일)와 pHash(유사 이미지) 2단계 스캔 방식
- 이미지 / 영상 / 오디오 / 전체 파일(확장자 무관) 지원
- 한/영 다국어 지원 (언어별 폰트 자동 적용)
- 삭제는 휴지통 이동 방식으로 안전하게 처리

---

## 파일 구조

```
DuplicateFinder/
├── main.py                  # 앱 진입점
├── scanner.py               # 폴더 스캔, 해시 계산, 중복 탐지 로직
├── gui/
│   ├── __init__.py
│   ├── theme.py             # 언어별 폰트/색상 설정 + apply_language_font()
│   ├── i18n.py              # 한/영 텍스트 딕셔너리 + t() / set_language() / get_language()
│   ├── main_window.py       # 메인 윈도우 레이아웃 + 언어 전환
│   ├── scan_panel.py        # 폴더 선택 + 스캔 설정 패널
│   ├── result_panel.py      # 결과 목록 + 미리보기 패널 + _score_file()
│   └── preview_card.py      # 개별 파일 카드 (썸네일/아이콘 + 정보 + 재생/체크박스)
├── DuplicateFinder.spec     # PyInstaller 빌드 설정
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 의존성

```
Pillow==10.3.0        # 이미지 처리 및 썸네일 생성
ImageHash==4.3.1      # Perceptual hashing (유사 이미지 감지)
Send2Trash==1.8.3     # 파일을 휴지통으로 이동
```

---

## 핵심 로직

### 스캔 흐름

1. 선택된 확장자 파일 목록 수집
2. MD5 계산 → 동일 해시 그룹화 (진행률 0→50%, 유사 검색 끄면 0→100%)
3. `similar=True`인 경우만: pHash 계산 (50→100%)
4. Union-Find로 유사 그룹화
5. 결과를 GUI에 전달 → indeterminate 프로그레스바로 정리 중 표시

### 해시 계산

```python
# 완전 동일
import hashlib
def get_md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

# 유사 이미지
import imagehash
from PIL import Image
def get_phash(filepath):
    return imagehash.phash(Image.open(filepath))

distance = hash1 - hash2  # 해밍 거리, 낮을수록 유사
```

### 멀티스레딩

- `threading.Thread`로 백그라운드 스캔 (GUI 프리징 방지)
- `queue.Queue`로 진행상황 전달, `after()`로 GUI 업데이트
- `_pause_event` (threading.Event)로 일시중지/재개
- 취소 시 `_pause_event.set()` 후 `_stop_event.set()`

### 주요 상수

- 미리보기 카드 상한: `_MAX_RENDER_CARDS = 50` (초과 시 일괄 처리 패널)
- 확인 다이얼로그 파일 목록 상한: `_MAX_LIST = 10` (초과 시 "... 외 N개")
- 썸네일 크기: 200×200px
- 원본 추천 기준: **해상도 > 파일 크기 > 날짜**

---

## UX 원칙

- 실수로 중요한 파일 삭제 방지가 최우선
- 삭제 전 항상 확인 다이얼로그 표시
- 삭제는 반드시 휴지통으로 (복구 가능하게)

---

## 보안 체크리스트

| 항목 | 규칙 |
|---|---|
| 파일 삭제 | `send2trash`만 사용. `os.remove()` / `Path.unlink()` 금지 |
| 네트워크 | `requests` / `urllib` / `socket` import 금지 |
| 위험 코드 | `eval` / `exec` / `os.system` / `__import__` 금지 |
| subprocess | OS 기본 뷰어/플레이어 열기 용도만 허용 (preview_card.py) |
| webbrowser | PayPal 후원 링크 전용 (scan_panel.py) |
| 경로 | `pathlib.Path` 처리, `is_safe_path`로 스캔 범위 제한 |
| 라이브러리 | `requirements.txt`에 버전 고정 (`==`), PyPI 공식 패키지만 사용 |

---

## 🚨 코드 수정 후 마무리 절차 — 절대 생략 금지

**코드를 한 줄이라도 수정했다면 반드시 아래 순서 실행.**

```
🔍 보안 검토
   → 네트워크 요청 코드 없음 확인 (requests/urllib/socket)
   → 위험 패턴 없음 확인 (eval/exec/os.system/__import__)
   → 직접 삭제 없음 확인 (os.remove/Path.unlink)
   → subprocess.run 있으면 허용된 용도인지 확인

📝 CLAUDE.md 업데이트
   → 변경된 기능/파일 구조 반영, 날짜 갱신

📦 Git commit & push
   → git add [변경 파일]
   → git commit -m "feat/fix/refactor/docs: [변경 내용]"
   → git push origin main
```

---

## 참고

- HEIC: `pillow-heif` 추가 설치 필요할 수 있음
- Windows / macOS 모두 동작 (`pathlib.Path`로 경로 통일)
- 대용량 폴더(590GB+) 실사용 환경 기준으로 개발