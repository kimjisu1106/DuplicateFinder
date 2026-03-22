# 📸 Photo Duplicate Finder — CLAUDE.md

## 프로젝트 개요

특정 폴더를 스캔해서 **완전히 동일한 사진**과 **유사한 사진**을 찾아내고,
나란히 비교한 뒤 삭제할 수 있는 데스크탑 GUI 앱.

**언어:** Python 3.10+
**GUI 프레임워크:** Tkinter (Python 내장, 설치 불필요)
**실행:** `python main.py`
**최초 구현 완료:** 2026-03-22
**마지막 업데이트:** 2026-03-22

---

## 핵심 기능 요구사항

### 1. 폴더 선택
- 앱 실행 시 폴더 선택 버튼 제공
- 선택한 폴더 경로를 화면에 표시
- 하위 폴더 포함 여부 옵션 (체크박스)

### 2. 스캔 단계 (2단계)

**1단계 — 완전 동일 파일 감지**
- MD5 해시로 파일 내용이 100% 동일한 파일 그룹 찾기
- 파일명이 달라도 내용이 같으면 중복으로 처리
- 지원 확장자: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.tiff`, `.heic`

**2단계 — 유사 이미지 감지**
- Perceptual Hash (pHash) 알고리즘 사용 (`imagehash` 라이브러리)
- 유사도 민감도를 슬라이더로 조절 가능 (해밍 거리 0~20)
  - 낮을수록 엄격 (거의 동일), 높을수록 관대 (조금 달라도 유사로 처리)
- 크기가 다르거나 약간 편집된 사진도 감지

**스캔 진행 표시**
- 진행률 프로그레스바 표시
- 현재 처리 중인 파일명 표시
- 스캔 중 취소 버튼 제공

### 3. 결과 화면

**그룹 목록 (왼쪽 패널)**
- 중복/유사 그룹을 리스트로 표시
- 각 그룹에 사진 수, 절약 가능한 용량 표시
- 완전 중복 / 유사 중복 탭으로 구분

**미리보기 (오른쪽 패널)**
- 그룹 선택 시 해당 사진들을 나란히 썸네일로 표시
- 각 사진 아래에 파일명, 크기(KB/MB), 해상도, 수정일 표시
- 썸네일 클릭 시 원본 크기로 열기 (OS 기본 뷰어 사용)

**선택 및 삭제**
- 각 사진에 체크박스 + 개별 삭제 버튼 제공
- "원본 유지 (나머지 선택)" 버튼 — 각 그룹에서 가장 큰/오래된 파일만 남기고 나머지 자동 선택
- "선택 항목 삭제" 버튼 — 클릭 시 확인 다이얼로그 후 일괄 삭제
- 개별 삭제 버튼 — 카드마다 빨간 삭제 버튼으로 즉시 삭제
- 삭제는 **휴지통으로 이동** (완전 삭제 아님, `send2trash` 라이브러리 사용)

### 4. 요약 정보
- 스캔한 전체 사진 수
- 발견된 중복 그룹 수
- 삭제 시 절약 가능한 총 용량

---

## 파일 구조

```
photo-duplicate-finder/
├── main.py              # 앱 진입점, Tkinter 메인 윈도우
├── scanner.py           # 폴더 스캔, 해시 계산, 중복 탐지 로직
├── gui/
│   ├── __init__.py
│   ├── theme.py         # 전역 폰트/색상 설정 (APP_FONT_FAMILY, APP_FONT_SIZE)
│   ├── main_window.py   # 메인 윈도우 레이아웃 + 전역 폰트 적용
│   ├── scan_panel.py    # 폴더 선택 + 스캔 설정 패널
│   ├── result_panel.py  # 결과 목록 + 미리보기 패널
│   └── preview_card.py  # 개별 사진 카드 (썸네일 + 정보 + 체크박스 + 삭제버튼)
├── requirements.txt
└── README.md
```

---

## 의존성 (requirements.txt)

```
Pillow==10.3.0        # 이미지 처리 및 썸네일 생성
ImageHash==4.3.1      # Perceptual hashing (유사 이미지 감지)
Send2Trash==1.8.3     # 파일을 휴지통으로 이동
```

설치 명령어:
```bash
pip install -r requirements.txt
```

---

## 핵심 로직 가이드

### 해시 계산 (scanner.py)

```python
# 완전 동일 감지
import hashlib
def get_md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

# 유사 이미지 감지
import imagehash
from PIL import Image
def get_phash(filepath):
    return imagehash.phash(Image.open(filepath))

# 두 이미지의 유사도 (해밍 거리, 낮을수록 비슷)
distance = hash1 - hash2  # imagehash끼리 뺄셈으로 거리 계산
```

### 스캔 흐름

1. 폴더 내 지원 확장자 파일 전체 목록 수집
2. 각 파일 MD5 계산 → 동일 해시 그룹화
3. MD5가 다른 파일들에 대해 pHash 계산
4. 슬라이더 임계값 이하인 파일 쌍 → 유사 그룹화
5. 결과를 GUI에 전달

### 멀티스레딩

- 스캔은 `threading.Thread`로 백그라운드 실행 (GUI 프리징 방지)
- 진행상황은 `queue.Queue`로 메인 스레드에 전달
- `after()` 메서드로 GUI 업데이트

---

## UX 원칙

- 실수로 중요한 사진 삭제하는 것을 방지하는 것이 최우선
- 삭제 전 항상 확인 다이얼로그 표시
- 삭제는 반드시 휴지통으로 (복구 가능하게)
- 원본 추천 로직은 **해상도 높은 것 > 파일 크기 큰 것 > 날짜 오래된 것** 순서로 우선

---

## 개발 순서 (추천)

1. `scanner.py` — 스캔 & 해시 로직 먼저 완성 후 테스트
2. `main.py` + `gui/main_window.py` — 기본 윈도우 틀 구성
3. `gui/scan_panel.py` — 폴더 선택 & 스캔 시작 UI
4. `gui/result_panel.py` — 결과 목록 표시
5. `gui/preview_card.py` — 썸네일 카드 & 체크박스
6. 삭제 기능 연결 & 전체 통합 테스트

---

## 보안 검토 체크리스트

코드 작성 후, 그리고 기능 추가할 때마다 아래 항목을 반드시 확인할 것.

### ✅ 라이브러리 & API 공식 여부 확인

| 라이브러리 | 공식 PyPI 이름 | 공식 문서 |
|---|---|---|
| Pillow | `Pillow` (대문자 P) | https://pillow.readthedocs.io |
| imagehash | `ImageHash` | https://github.com/JohannesBuchner/imagehash |
| send2trash | `Send2Trash` | https://github.com/arsenetar/send2trash |

- `pip install` 시 **오타 주의** — `Pillow` vs `pillow`, `imagehash` vs `image-hash` 등 이름이 비슷한 악성 패키지 존재
- `requirements.txt`에 **버전 고정** 필수 (`>=` 대신 `==` 권장, 예: `Pillow==10.3.0`)
- 추가 라이브러리 도입 시 반드시 PyPI 공식 페이지 확인: https://pypi.org

### ✅ 파일 접근 보안

- 이 앱은 **읽기(Read)** 와 **삭제(Trash 이동)** 만 허용 — 파일 내용 수정, 업로드, 외부 전송 코드가 있으면 안 됨
- 파일 경로는 반드시 `pathlib.Path`로 처리 — 문자열 직접 조합 금지 (경로 탈출 공격 방지)
- 스캔 범위는 사용자가 선택한 폴더 내부로만 제한 — `..` 상위 경로 접근 차단

```python
# 안전한 경로 처리 예시
from pathlib import Path

def is_safe_path(base_dir: Path, target: Path) -> bool:
    return base_dir.resolve() in target.resolve().parents
```

### ✅ 네트워크 통신 금지

- 이 앱은 **완전 로컬 동작** — 어떤 네트워크 요청도 없어야 함
- `requests`, `urllib`, `http`, `socket` 등 네트워크 관련 import가 있으면 즉시 제거
- 외부 API 호출, 텔레메트리, 자동 업데이트 기능 포함 금지

### ✅ 위험 코드 패턴 금지

아래 코드가 있으면 무조건 제거:

```python
# ❌ 절대 사용 금지
eval(...)          # 임의 코드 실행
exec(...)          # 임의 코드 실행
os.system(...)     # 셸 명령 실행
subprocess.run(...)  # 외부 프로세스 실행 (필요한 경우 사유 명시)
__import__(...)    # 동적 import
```

### ✅ 삭제 기능 안전장치

- 파일 삭제는 반드시 `send2trash` 사용 — `os.remove()`, `Path.unlink()` 직접 삭제 금지
- 삭제 전 확인 다이얼로그 필수 (건너뛰는 옵션 없음)
- 삭제 실행 전 대상 파일 목록을 로그로 출력

```python
# 안전한 삭제 예시
from send2trash import send2trash

def safe_delete(filepath: Path):
    print(f"[삭제→휴지통] {filepath}")  # 로그
    send2trash(str(filepath))           # 휴지통으로 이동
```

### ✅ 코드 완성 후 


1. 🔍 보안 검토 결과 요약 출력
    전체 코드에서 네트워크 요청, eval/exec, os.system 사용 여부 확인해줘.
    외부로 데이터 전송하는 코드가 있는지 검토해줘.
    requirements.txt의 라이브러리가 공식 PyPI 패키지인지 확인해줘.
2. 📝 CLAUDE.md를 현재 코드 상태에 맞게 업데이트 (파일 구조, 라이브러리 버전, 완료 날짜 등)
3. 📦 git add . 하고 적절한 커밋 메시지로 commit
4. 🚀 git push origin main
5. ✅ 각 단계 완료될 때마다 해당 이모지와 함께 결과 출력해줘


### ✅ 최종 점검 후 마무리 절차

보안 검토가 끝나면 아래 순서대로 진행. **각 단계 완료 시 해당 이모지를 출력할 것.**

```
🔍 보안 검토 중...
   → 네트워크 요청 없음 확인
   → 위험 코드 패턴 없음 확인
   → 라이브러리 공식 여부 확인

📝 CLAUDE.md 업데이트 중...
   → 변경된 파일 구조 반영
   → 추가된 라이브러리 있으면 목록 갱신
   → 최종 완료 날짜 기록

📦 Git commit 준비 중...
   → git add .
   → git commit -m "feat: [변경 내용 요약]"

🚀 Git push 중...
   → git push origin main

✅ 완료! 모든 단계가 성공적으로 끝났습니다.
```

## 참고사항

- HEIC 파일은 `pillow-heif` 라이브러리 추가 설치 필요할 수 있음 (선택)
- 썸네일 크기 권장: 200x200px
- 대용량 폴더(1000장+) 테스트 필수
- Windows / macOS 둘 다 동작해야 함 (경로 처리 주의 — `pathlib.Path` 사용 권장)