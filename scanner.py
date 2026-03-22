"""
scanner.py — 폴더 스캔, 해시 계산, 중복 탐지 로직
"""
import hashlib
import threading
import queue
from pathlib import Path
from typing import Callable

import imagehash
from PIL import Image

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif', '.heic'}


def is_safe_path(base_dir: Path, target: Path) -> bool:
    """대상 경로가 기준 폴더 내부에 있는지 확인 (경로 탈출 방지)."""
    try:
        target.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False


def get_md5(filepath: Path) -> str:
    """파일의 MD5 해시를 반환."""
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def get_phash(filepath: Path):
    """파일의 Perceptual Hash를 반환. 실패 시 None."""
    try:
        return imagehash.phash(Image.open(filepath))
    except Exception:
        return None


def collect_image_files(folder: Path, recursive: bool) -> list[Path]:
    """폴더에서 지원 확장자 이미지 파일 목록을 수집."""
    pattern = '**/*' if recursive else '*'
    files = []
    for p in folder.glob(pattern):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            if is_safe_path(folder, p):
                files.append(p)
    return files


class Scanner:
    """백그라운드 스캔 실행 및 결과 전달 클래스."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 초기값: 실행 중 (set = 멈추지 않음)
        self._thread: threading.Thread | None = None
        self.progress_queue: queue.Queue = queue.Queue()

    def pause(self):
        """스캔 일시중지."""
        self._pause_event.clear()

    def resume(self):
        """스캔 재개."""
        self._pause_event.set()

    def start(self, folder: Path, recursive: bool, threshold: int, similar: bool = True):
        """스캔을 백그라운드 스레드에서 시작."""
        self._stop_event.clear()
        self._pause_event.set()
        self._thread = threading.Thread(
            target=self._run,
            args=(folder, recursive, threshold, similar),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        """스캔 취소 요청."""
        self._stop_event.set()

    def _put(self, msg_type: str, **kwargs):
        self.progress_queue.put({'type': msg_type, **kwargs})

    def _run(self, folder: Path, recursive: bool, threshold: int, similar: bool = True):
        try:
            # 파일 수집
            self._put('status', message='이미지 파일 목록 수집 중...')
            files = collect_image_files(folder, recursive)
            total = len(files)
            if total == 0:
                self._put('done', exact_groups=[], similar_groups=[], total=0)
                return

            self._put('total', count=total)

            # 1단계: MD5 계산
            # 유사 검색 있으면 2단계와 합쳐 100%가 되도록 total*2 사용, 없으면 total 그대로
            est_total = total * 2 if similar else total
            md5_map: dict[str, list[Path]] = {}
            for i, fp in enumerate(files):
                self._pause_event.wait()  # 일시중지 중이면 여기서 대기
                if self._stop_event.is_set():
                    self._put('cancelled')
                    return
                self._put('progress', current=i + 1, total=est_total, filename=fp.name)
                try:
                    h = get_md5(fp)
                    md5_map.setdefault(h, []).append(fp)
                except Exception:
                    pass

            exact_groups = [paths for paths in md5_map.values() if len(paths) > 1]
            exact_set = {fp for group in exact_groups for fp in group}

            if not similar:
                # 유사 이미지 검색 생략
                self._put('done', exact_groups=exact_groups, similar_groups=[], total=total)
                return

            # 2단계: pHash 계산 (MD5가 다른 파일들만)
            unique_files = [fp for fp in files if fp not in exact_set]
            phash_list: list[tuple[Path, any]] = []

            self._put('status', message='유사 이미지 분석 중...')
            grand_total = total + len(unique_files)
            for i, fp in enumerate(unique_files):
                self._pause_event.wait()  # 일시중지 중이면 여기서 대기
                if self._stop_event.is_set():
                    self._put('cancelled')
                    return
                self._put('progress', current=total + i + 1, total=grand_total, filename=fp.name)
                ph = get_phash(fp)
                if ph is not None:
                    phash_list.append((fp, ph))

            # 유사 그룹화 (Union-Find)
            n = len(phash_list)
            parent = list(range(n))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            def union(x, y):
                parent[find(x)] = find(y)

            self._put('status', message=f'유사도 비교 중... (0 / {n}장)')
            for i in range(n):
                self._pause_event.wait()  # 일시중지 중이면 여기서 대기
                if self._stop_event.is_set():
                    self._put('cancelled')
                    return
                if i % 50 == 0:
                    self._put('status', message=f'유사도 비교 중... ({i} / {n}장)')
                for j in range(i + 1, n):
                    dist = phash_list[i][1] - phash_list[j][1]
                    if dist <= threshold:
                        union(i, j)

            groups_map: dict[int, list[Path]] = {}
            for i, (fp, _) in enumerate(phash_list):
                root = find(i)
                groups_map.setdefault(root, []).append(fp)

            similar_groups = [paths for paths in groups_map.values() if len(paths) > 1]

            self._put('done', exact_groups=exact_groups, similar_groups=similar_groups, total=total)

        except Exception as e:
            self._put('error', message=str(e))
