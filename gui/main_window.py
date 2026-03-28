"""
main_window.py — 메인 윈도우 레이아웃
"""
import tkinter as tk
from tkinter import messagebox, font as tkfont
from pathlib import Path

from .theme import APP_FONT_FAMILY, APP_FONT_SIZE
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

        self._apply_global_font()
        self._scanner = Scanner()
        self._build()

    def _apply_global_font(self):
        """모든 Tkinter 위젯의 기본 폰트를 통일."""
        default_font = tkfont.nametofont('TkDefaultFont')
        default_font.configure(family=APP_FONT_FAMILY, size=APP_FONT_SIZE)

        for name in ('TkTextFont', 'TkFixedFont', 'TkMenuFont',
                     'TkHeadingFont', 'TkCaptionFont', 'TkSmallCaptionFont'):
            try:
                tkfont.nametofont(name).configure(family=APP_FONT_FAMILY, size=APP_FONT_SIZE)
            except Exception:
                pass

    def _build(self):
        # 언어 전환 버튼 (우상단)
        self._top_bar = tk.Frame(self)
        self._top_bar.pack(fill='x', padx=10, pady=(6, 0))
        self._lang_btn = tk.Button(self._top_bar, text=t('btn_lang_toggle'),
                                   command=self._toggle_language, width=8)
        self._lang_btn.pack(side='right')

        # 스캔 패널
        self._scan_panel = ScanPanel(
            self,
            on_scan=self._on_scan,
            on_cancel=self._on_cancel,
            on_pause=self._on_pause,
        )
        self._scan_panel.pack(fill='x', padx=10, pady=(4, 4))

        # 결과 패널
        self._result_panel = ResultPanel(self)
        self._result_panel.pack(fill='both', expand=True, padx=10, pady=(4, 10))

    def _toggle_language(self):
        new_lang = 'en' if get_language() == 'ko' else 'ko'
        set_language(new_lang)
        # 재시작 없이 즉시 반영하려면 위젯을 다시 그려야 하므로 윈도우 재빌드
        self._top_bar.destroy()
        self._scan_panel.destroy()
        self._result_panel.destroy()
        self._build()

    def _on_scan(self, folder: Path, recursive: bool, threshold: int, similar: bool,
                 include_images: bool = True, include_videos: bool = False,
                 include_audio: bool = False, include_all: bool = False):
        self._result_panel.clear()
        self._scan_panel.set_scanning(True)
        self._scanner.start(folder, recursive, threshold, similar,
                            include_images, include_videos, include_audio, include_all)
        self._poll_queue()

    def _finish_scan(self, exact_groups, similar_groups, total):
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
