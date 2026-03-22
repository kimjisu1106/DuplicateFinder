"""
main_window.py — 메인 윈도우 레이아웃
"""
import tkinter as tk
from tkinter import messagebox, font as tkfont
from pathlib import Path

from .theme import APP_FONT_FAMILY, APP_FONT_SIZE

from .scan_panel import ScanPanel
from .result_panel import ResultPanel
from scanner import Scanner


class MainWindow(tk.Tk):
    """애플리케이션 메인 윈도우."""

    def __init__(self):
        super().__init__()
        self.title('📸 Photo Duplicate Finder')
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
        # 상단: 스캔 패널
        self._scan_panel = ScanPanel(
            self,
            on_scan=self._on_scan,
            on_cancel=self._on_cancel,
        )
        self._scan_panel.pack(fill='x', padx=10, pady=(10, 4))

        # 하단: 결과 패널
        self._result_panel = ResultPanel(self)
        self._result_panel.pack(fill='both', expand=True, padx=10, pady=(4, 10))

    def _on_scan(self, folder: Path, recursive: bool, threshold: int):
        self._result_panel.clear()
        self._scan_panel.set_scanning(True)
        self._scanner.start(folder, recursive, threshold)
        self._poll_queue()

    def _on_cancel(self):
        self._scanner.stop()
        self._scan_panel.set_scanning(False)
        self._scan_panel.set_status('스캔이 취소되었습니다.')

    def _poll_queue(self):
        """큐에서 진행 상황 메시지를 읽어 GUI 업데이트."""
        try:
            while True:
                msg = self._scanner.progress_queue.get_nowait()
                mtype = msg['type']

                if mtype == 'total':
                    pass  # 총 파일 수 (진행률 계산에 활용)

                elif mtype == 'progress':
                    self._scan_panel.update_progress(
                        msg['current'], msg['total'], msg.get('filename', '')
                    )

                elif mtype == 'status':
                    self._scan_panel.set_status(msg['message'])

                elif mtype == 'done':
                    self._scan_panel.set_scanning(False)
                    self._scan_panel.update_progress(1, 1, '')
                    self._scan_panel.set_status('스캔 완료!')
                    self._result_panel.show_results(
                        msg['exact_groups'],
                        msg['similar_groups'],
                        msg['total'],
                    )
                    return

                elif mtype == 'cancelled':
                    self._scan_panel.set_scanning(False)
                    self._scan_panel.set_status('취소됨')
                    return

                elif mtype == 'error':
                    self._scan_panel.set_scanning(False)
                    messagebox.showerror('스캔 오류', msg['message'])
                    return

        except Exception:
            pass

        # 아직 완료 전이면 계속 폴링
        self.after(100, self._poll_queue)
