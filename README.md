# Duplicate Finder

> 한국어 | [English](#english)

---

## 한국어

중복 파일을 찾아 정리하는 Windows 데스크탑 앱입니다.
완전히 동일한 파일(MD5 해시)과 유사한 이미지(pHash)를 탐지하고, 나란히 비교한 뒤 안전하게 삭제할 수 있습니다.

### 주요 기능

- **완전 중복 탐지** — MD5 해시 비교로 내용이 완전히 같은 파일 탐지 (이름·위치 무관)
- **유사 이미지 탐지** — Perceptual Hash로 리사이즈·압축된 유사 이미지 탐지
- **파일 종류 선택** — 이미지 / 영상 / 오디오 / 전체 파일 선택 가능
- **하위 폴더 포함** 옵션
- **민감도 조절** — 유사 이미지 탐지 임계값 슬라이더
- **파일 위치 열기** — 미리보기 클릭 시 파일 탐색기에서 해당 파일 선택하여 열기
- **안전한 삭제** — 휴지통으로 이동 (복구 가능)
- **원본 자동 추천** — 해상도 > 파일 크기 > 날짜 기준
- **한/영 UI 전환** — 스캔 결과가 있을 경우 전환 전 경고 다이얼로그 표시
- **스캔 일시중지 / 재개 / 취소**

### 다운로드 및 실행

Python 설치 없이 바로 실행 가능합니다.

1. [Releases](../../releases) 페이지에서 최신 `DuplicateFinder.exe` 다운로드
2. 더블클릭으로 실행

### 백신 오진 안내

일부 백신(알약 등)에서 랜섬웨어로 오진할 수 있습니다.
파일을 대량으로 읽고 삭제하는 동작 패턴이 랜섬웨어와 유사하게 보이기 때문이며, 실제 악성코드가 아닙니다.
소스 코드는 이 저장소에서 직접 확인하실 수 있습니다.
오진 발생 시 백신의 예외 목록에 추가하시거나, 소스에서 직접 빌드해 사용하세요.

### 소스에서 실행

```bash
pip install Pillow ImageHash Send2Trash
python main.py
```

### 빌드

```bash
pip install pyinstaller
pyinstaller DuplicateFinder.spec
```

`dist/DuplicateFinder.exe` 생성됩니다.

### 후원

이 앱이 도움이 됐다면 커피 한 잔으로 응원해주세요 ☕

[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://kimlog.pages.dev/contact/)

---

## English

A Windows desktop app for finding and cleaning up duplicate files.
Detects exact duplicates (MD5 hash) and visually similar images (pHash), lets you compare them side by side, and safely removes them.

### Features

- **Exact duplicate detection** — MD5 hash comparison regardless of file name or location
- **Similar image detection** — Perceptual Hash to catch resized or recompressed images
- **File type filter** — Images / Videos / Audio / All files
- **Recursive scan** — Include subfolders option
- **Sensitivity slider** — Adjust similarity threshold
- **Reveal in Explorer** — Click any preview to open the file's location in Explorer with it selected
- **Safe deletion** — Files moved to Trash (recoverable)
- **Auto original recommendation** — Resolution > File size > Date
- **Korean / English UI toggle** — warns before clearing scan results when switching language
- **Pause / Resume / Cancel scan**

### Download & Run

No Python installation required.

1. Download the latest `DuplicateFinder.exe` from the [Releases](../../releases) page
2. Double-click to run

### Antivirus False Positive

Some antivirus software (e.g. ALYac) may flag this app as ransomware.
This is a false positive — the app reads many files for hash comparison and moves files to Trash, which can resemble ransomware behavior.
The full source code is available in this repository for inspection.
If flagged, add the exe to your antivirus exception list or build from source.

### Run from Source

```bash
pip install Pillow ImageHash Send2Trash
python main.py
```

### Build

```bash
pip install pyinstaller
pyinstaller DuplicateFinder.spec
```

Output: `dist/DuplicateFinder.exe`

### Support

If this app was helpful, consider buying me a coffee ☕

[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://kimlog.pages.dev/contact/)

---

## License

MIT
