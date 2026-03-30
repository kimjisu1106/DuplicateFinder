"""
main_window.py — 메인 윈도우 레이아웃
"""
import sys
import tkinter as tk
from tkinter import messagebox, font as tkfont
from pathlib import Path

from . import theme
from .i18n import t, set_language, get_language
from .scan_panel import ScanPanel
from .result_panel import ResultPanel
from scanner import Scanner


class MainWindow(tk.Tk):
    """애플리케이션 메인 윈도우."""

    def __init__(self):
        super().__init__()
        self.title(t('window_title'))
        self.geometry('1100x740')
        self.minsize(900, 600)
        try:
            base = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent
            self.iconbitmap(base / 'icon.ico')
        except Exception:
            pass

        self._apply_global_font()
        self._scanner = Scanner()
        self._last_scan_results: tuple | None = None  # (exact_groups, similar_groups, total)
        self._build()

    def _apply_global_font(self):
        """모든 Tkinter 위젯의 기본 폰트를 통일."""
        theme.apply_language_font(get_language(), tkfont.families())
        default_font = tkfont.nametofont('TkDefaultFont')
        default_font.configure(family=theme.APP_FONT_FAMILY, size=theme.APP_FONT_SIZE)

        for name in ('TkTextFont', 'TkFixedFont', 'TkMenuFont',
                     'TkHeadingFont', 'TkCaptionFont', 'TkSmallCaptionFont'):
            try:
                tkfont.nametofont(name).configure(family=theme.APP_FONT_FAMILY, size=theme.APP_FONT_SIZE)
            except Exception:
                pass

    def _build(self):
        self._scan_panel = ScanPanel(
            self,
            on_scan=self._on_scan,
            on_cancel=self._on_cancel,
            on_pause=self._on_pause,
            on_lang_toggle=self._toggle_language,
        )
        self._scan_panel.pack(fill='x', padx=10, pady=(10, 4))

        self._result_panel = ResultPanel(self)
        self._result_panel.pack(fill='both', expand=True, padx=10, pady=(4, 10))

    def _toggle_language(self):
        new_lang = 'en' if get_language() == 'ko' else 'ko'
        set_language(new_lang)
        self._apply_global_font()
        self._scan_panel.destroy()
        self._result_panel.destroy()
        self._build()
        if self._last_scan_results:
            exact, similar, total = self._last_scan_results
            self._result_panel.show_results(exact, similar, total)

    def _on_scan(self, folder: Path, recursive: bool, threshold: int, similar: bool,
                 include_images: bool = True, include_videos: bool = False,
                 include_audio: bool = False, include_all: bool = False):
        self._last_scan_results = None
        self._result_panel.clear()
        self._scan_panel.set_scanning(True)
        self._scanner.start(folder, recursive, threshold, similar,
                            include_images, include_videos, include_audio, include_all)
        self._poll_queue()

    def _finish_scan(self, exact_groups, similar_groups, total):
        self._last_scan_results = (exact_groups, similar_groups, total)
        self._result_panel.show_results(exact_groups, similar_groups, total)
        self._scan_panel.set_processing(False)
        self._scan_panel.set_status(t('status_scan_complete'))

    def _on_pause(self, is_paused: bool):
        if is_paused:
            self._scanner.pause()
        else:
            self._scanner.resume()

    def _on_cancel(self):
        self._scanner.resume()
        self._scanner.stop()
        self._scan_panel.set_scanning(False)
        self._scan_panel.set_status(t('status_scan_cancelled'))

    def _poll_queue(self):
        """큐에서 진행 상황 메시지를 읽어 GUI 업데이트."""
        try:
            while True:
                msg = self._scanner.progress_queue.get_nowait()
                mtype = msg['type']

                if mtype == 'total':
                    pass

                elif mtype == 'progress':
                    self._scan_panel.update_progress(
                        msg['current'], msg['total'], msg.get('filename', '')
                    )

                elif mtype == 'status':
                    self._scan_panel.set_status(msg['message'])

                elif mtype == 'done':
                    self._scan_panel.set_scanning(False)
                    self._scan_panel.set_processing(True)
                    exact = msg['exact_groups']
                    similar = msg['similar_groups']
                    total = msg['total']
                    self.after(50, lambda: self._finish_scan(exact, similar, total))
                    return

                elif mtype == 'cancelled':
                    self._scan_panel.set_scanning(False)
                    self._scan_panel.set_status(t('status_cancelled'))
                    self.after(1500, self._scan_panel.reset_progress)
                    return

                elif mtype == 'error':
                    self._scan_panel.set_scanning(False)
                    messagebox.showerror(t('dlg_title_scan_error'), msg['message'])
                    return

        except Exception:
            pass

        self.after(100, self._poll_queue)
