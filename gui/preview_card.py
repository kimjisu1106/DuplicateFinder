"""
preview_card.py — 개별 파일 카드 (썸네일 + 정보 + 체크박스)
"""
import os
import subprocess
import sys
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk
from . import theme
from .i18n import t

THUMB_SIZE = (200, 200)

VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v', '.3gp', '.ts', '.mts'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}


def open_with_default_viewer(filepath: Path):
    """OS 기본 뷰어/플레이어로 파일 열기."""
    try:
        if sys.platform == 'win32':
            os.startfile(str(filepath))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(filepath)], check=False)
        else:
            subprocess.run(['xdg-open', str(filepath)], check=False)
    except Exception:
        pass


def reveal_in_explorer(filepath: Path):
    """파일 탐색기에서 해당 파일을 선택한 채로 폴더 열기."""
    try:
        if sys.platform == 'win32':
            subprocess.Popen(f'explorer /select,"{filepath}"')
        elif sys.platform == 'darwin':
            subprocess.run(['open', '-R', str(filepath)], check=False)
        else:
            subprocess.run(['xdg-open', str(filepath.parent)], check=False)
    except Exception:
        pass


def format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / 1024:.1f} KB"


class PreviewCard(tk.Frame):
    """단일 파일 미리보기 카드 위젯."""

    def __init__(self, parent, filepath: Path, show_thumb: bool = True, **kwargs):
        super().__init__(parent, relief='ridge', borderwidth=1, **kwargs)
        self.filepath = filepath
        self._photo = None
        self.var = tk.BooleanVar(value=False)
        self._show_thumb = show_thumb
        self._ext = filepath.suffix.lower()

        self._build()

    def _is_video(self):
        return self._ext in VIDEO_EXTENSIONS

    def _is_audio(self):
        return self._ext in AUDIO_EXTENSIONS

    def _build(self):
        if self._is_video():
            self._build_video_placeholder()
        elif self._is_audio():
            self._build_audio_placeholder()
        else:
            self._build_image_thumb()

        # 파일명
        name = self.filepath.name
        display_name = name if len(name) <= 22 else name[:19] + '...'
        tk.Label(self, text=display_name, font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 1, 'bold'),
                 wraplength=200, justify='center').pack()

        # 메타 정보
        info = self._get_info()
        tk.Label(self, text=info, font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 2),
                 foreground='#666666', justify='center').pack()

        # 영상/오디오: 재생 버튼
        if self._is_video() or self._is_audio():
            tk.Button(self, text=t('btn_play'), command=lambda: reveal_in_explorer(self.filepath),
                      width=10).pack(pady=(4, 2))

        # 체크박스
        tk.Checkbutton(self, variable=self.var, text=t('cb_select')).pack(pady=(2, 6))

    def _build_image_thumb(self):
        if self._show_thumb:
            thumb_label = tk.Label(self, cursor='hand2', background='#2b2b2b')
            thumb_label.pack(padx=4, pady=(6, 2))
            self._load_thumbnail(thumb_label)
        else:
            lbl = tk.Label(self, text='🖼', font=(theme.APP_FONT_FAMILY, 24),
                           cursor='hand2', foreground='#aaaaaa')
            lbl.pack(padx=4, pady=(6, 2), ipadx=60, ipady=40)
            lbl.bind('<Button-1>', lambda e: reveal_in_explorer(self.filepath))

    def _build_video_placeholder(self):
        lbl = tk.Label(self, text='🎬', font=(theme.APP_FONT_FAMILY, 36),
                       foreground='#aaaaaa', background='#2b2b2b',
                       width=14, height=6)
        lbl.pack(padx=4, pady=(6, 2))

    def _build_audio_placeholder(self):
        lbl = tk.Label(self, text='🎵', font=(theme.APP_FONT_FAMILY, 36),
                       foreground='#aaaaaa', background='#2b2b2b',
                       width=14, height=6)
        lbl.pack(padx=4, pady=(6, 2))

    def _load_thumbnail(self, label: tk.Label):
        try:
            img = Image.open(self.filepath)
            img.thumbnail(THUMB_SIZE, Image.LANCZOS)
            bg = Image.new('RGB', THUMB_SIZE, (43, 43, 43))
            offset = ((THUMB_SIZE[0] - img.width) // 2, (THUMB_SIZE[1] - img.height) // 2)
            bg.paste(img, offset)
            self._photo = ImageTk.PhotoImage(bg)
            label.config(image=self._photo)
            label.bind('<Button-1>', lambda e: reveal_in_explorer(self.filepath))
        except Exception:
            label.config(text=t('label_no_preview'), width=28, height=12,
                         relief='sunken', foreground='#888888', cursor='hand2')
            label.bind('<Button-1>', lambda e: reveal_in_explorer(self.filepath))

    def _get_info(self) -> str:
        parts = []
        try:
            stat = self.filepath.stat()
            parts.append(format_size(stat.st_size))
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
            parts.append(mtime)
        except Exception:
            pass
        if not self._is_video() and not self._is_audio():
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
