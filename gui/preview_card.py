"""
preview_card.py — 개별 사진 카드 (썸네일 + 정보 + 체크박스)
"""
import os
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

THUMB_SIZE = (200, 200)


def open_with_default_viewer(filepath: Path):
    """OS 기본 뷰어로 파일 열기."""
    try:
        if sys.platform == 'win32':
            os.startfile(str(filepath))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(filepath)], check=False)
        else:
            subprocess.run(['xdg-open', str(filepath)], check=False)
    except Exception:
        pass


def format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / 1024:.1f} KB"


class PreviewCard(tk.Frame):
    """단일 이미지 미리보기 카드 위젯."""

    def __init__(self, parent, filepath: Path, **kwargs):
        super().__init__(parent, relief='ridge', borderwidth=1, **kwargs)
        self.filepath = filepath
        self._photo = None
        self.var = tk.BooleanVar(value=False)

        self._build()

    def _build(self):
        # 썸네일
        thumb_label = tk.Label(self, cursor='hand2', background='#2b2b2b')
        thumb_label.pack(padx=4, pady=(6, 2))
        self._load_thumbnail(thumb_label)

        # 파일명
        name = self.filepath.name
        display_name = name if len(name) <= 22 else name[:19] + '...'
        tk.Label(self, text=display_name, font=('Segoe UI', 8, 'bold'),
                 wraplength=200, justify='center').pack()

        # 메타 정보
        info = self._get_info()
        tk.Label(self, text=info, font=('Segoe UI', 7),
                 foreground='#666666', justify='center').pack()

        # 체크박스
        cb = tk.Checkbutton(self, variable=self.var, text='선택')
        cb.pack(pady=(2, 6))

    def _load_thumbnail(self, label: tk.Label):
        try:
            img = Image.open(self.filepath)
            img.thumbnail(THUMB_SIZE, Image.LANCZOS)
            # 배경 채우기
            bg = Image.new('RGB', THUMB_SIZE, (43, 43, 43))
            offset = ((THUMB_SIZE[0] - img.width) // 2, (THUMB_SIZE[1] - img.height) // 2)
            bg.paste(img, offset)
            self._photo = ImageTk.PhotoImage(bg)
            label.config(image=self._photo)
            label.bind('<Button-1>', lambda e: open_with_default_viewer(self.filepath))
        except Exception:
            label.config(text='미리보기\n불가', width=28, height=12,
                         relief='sunken', foreground='#888888')

    def _get_info(self) -> str:
        parts = []
        try:
            stat = self.filepath.stat()
            parts.append(format_size(stat.st_size))
            import datetime
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
            parts.append(mtime)
        except Exception:
            pass
        try:
            with Image.open(self.filepath) as img:
                parts.append(f"{img.width}×{img.height}")
        except Exception:
            pass
        return '  |  '.join(parts)

    def is_selected(self) -> bool:
        return self.var.get()

    def set_selected(self, value: bool):
        self.var.set(value)

    def highlight(self, on: bool):
        color = '#fff3cd' if on else self.master.cget('background')
        try:
            self.config(background=color)
        except Exception:
            pass
