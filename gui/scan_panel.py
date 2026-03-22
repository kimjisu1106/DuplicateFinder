"""
scan_panel.py — 폴더 선택 + 스캔 설정 패널
"""
import time
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from .theme import APP_FONT_FAMILY, APP_FONT_SIZE


class ScanPanel(tk.LabelFrame):
    """폴더 선택, 옵션 설정, 스캔 시작/취소 버튼을 포함하는 패널."""

    def __init__(self, parent, on_scan: callable, on_cancel: callable, on_pause: callable, **kwargs):
        super().__init__(parent, text=' 스캔 설정 ', padx=10, pady=8, **kwargs)
        self._on_scan = on_scan
        self._on_cancel = on_cancel
        self._on_pause = on_pause
        self._folder: Path | None = None
        self._paused = False
        self._scan_start_time: float | None = None
        self._pause_start_time: float | None = None
        self._total_paused_secs: float = 0.0

        self._build()

    def _build(self):
        # 폴더 선택 행
        row0 = tk.Frame(self)
        row0.pack(fill='x', pady=(0, 6))

        tk.Label(row0, text='폴더:').pack(side='left')
        self._folder_var = tk.StringVar(value='선택된 폴더 없음')
        tk.Label(row0, textvariable=self._folder_var, anchor='w',
                 relief='sunken', width=46, foreground='#333333').pack(side='left', padx=6, fill='x', expand=True)
        tk.Button(row0, text='폴더 선택', command=self._choose_folder, width=10).pack(side='left')

        # 옵션 행
        row1 = tk.Frame(self)
        row1.pack(fill='x', pady=(0, 6))

        self._recursive_var = tk.BooleanVar(value=True)
        tk.Checkbutton(row1, text='하위 폴더 포함', variable=self._recursive_var).pack(side='left')

        self._similar_var = tk.BooleanVar(value=True)
        tk.Checkbutton(row1, text='유사 이미지 검색',
                       variable=self._similar_var,
                       command=self._on_similar_toggle).pack(side='left', padx=(12, 0))

        self._threshold_frame = tk.Frame(row1)
        self._threshold_frame.pack(side='left')

        tk.Label(self._threshold_frame, text='   민감도:').pack(side='left')
        self._threshold_var = tk.IntVar(value=10)
        self._threshold_label = tk.Label(self._threshold_frame, text='10', width=3)
        self._slider = tk.Scale(self._threshold_frame, from_=0, to=20, orient='horizontal',
                                variable=self._threshold_var, length=140,
                                command=self._on_slider, showvalue=False)
        self._slider.pack(side='left', padx=4)
        self._threshold_label.pack(side='left')
        tk.Label(self._threshold_frame, text='← 엄격  관대 →', foreground='#888888',
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1)).pack(side='left', padx=4)

        # 버튼 행
        row2 = tk.Frame(self)
        row2.pack(fill='x', pady=(4, 0))

        self._scan_btn = tk.Button(row2, text='스캔 시작', command=self._start_scan,
                                   width=12, bg='#4CAF50', fg='white',
                                   font=(APP_FONT_FAMILY, APP_FONT_SIZE, 'bold'))
        self._scan_btn.pack(side='left', padx=(0, 6))

        self._pause_btn = tk.Button(row2, text='일시중지', command=self._toggle_pause,
                                    width=10, state='disabled')
        self._pause_btn.pack(side='left', padx=(0, 6))

        self._cancel_btn = tk.Button(row2, text='취소', command=self._cancel_scan,
                                     width=8, state='disabled')
        self._cancel_btn.pack(side='left')

        # 진행 상황 — 프로그레스바
        row3 = tk.Frame(self)
        row3.pack(fill='x', pady=(8, 0))

        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(row3, variable=self._progress_var, maximum=100)
        self._progress.pack(fill='x', expand=True)

        # 진행 상황 — 상세 정보
        row4 = tk.Frame(self)
        row4.pack(fill='x', pady=(2, 0))

        self._count_var = tk.StringVar(value='')
        tk.Label(row4, textvariable=self._count_var, anchor='w',
                 foreground='#333333', font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1)).pack(side='left')

        self._eta_var = tk.StringVar(value='')
        tk.Label(row4, textvariable=self._eta_var, anchor='e',
                 foreground='#555555', font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1)).pack(side='right')

        self._status_var = tk.StringVar(value='')
        row5 = tk.Frame(self)
        row5.pack(fill='x')
        tk.Label(row5, textvariable=self._status_var, anchor='w',
                 foreground='#888888', font=(APP_FONT_FAMILY, APP_FONT_SIZE - 2)).pack(side='left')

    def _choose_folder(self):
        path = filedialog.askdirectory(title='스캔할 폴더를 선택하세요')
        if path:
            self._folder = Path(path)
            display = str(self._folder)
            if len(display) > 58:
                display = '...' + display[-55:]
            self._folder_var.set(display)

    def _on_similar_toggle(self):
        state = 'normal' if self._similar_var.get() else 'disabled'
        self._slider.config(state=state)
        for w in self._threshold_frame.winfo_children():
            if isinstance(w, tk.Label):
                w.config(foreground='#333333' if state == 'normal' else '#aaaaaa')

    def _on_slider(self, val):
        self._threshold_label.config(text=str(int(float(val))))

    def _start_scan(self):
        if self._folder is None:
            tk.messagebox.showwarning('폴더 미선택', '스캔할 폴더를 먼저 선택해주세요.')
            return
        self._scan_btn.config(state='disabled')
        self._cancel_btn.config(state='normal')
        self._progress_var.set(0)
        self._status_var.set('스캔 준비 중...')
        self._count_var.set('')
        self._eta_var.set('')
        self._scan_start_time = time.time()
        self._total_paused_secs = 0.0
        self._pause_start_time = None
        self._on_scan(
            folder=self._folder,
            recursive=self._recursive_var.get(),
            threshold=self._threshold_var.get(),
            similar=self._similar_var.get(),
        )

    def _toggle_pause(self):
        self._paused = not self._paused
        if self._paused:
            self._pause_start_time = time.time()
            self._pause_btn.config(text='재개')
            self._status_var.set('일시중지됨')
        else:
            if self._pause_start_time:
                self._total_paused_secs += time.time() - self._pause_start_time
                self._pause_start_time = None
            self._pause_btn.config(text='일시중지')
        self._on_pause(self._paused)

    def _cancel_scan(self):
        self._paused = False
        self._on_cancel()

    # --- 외부에서 호출하는 상태 업데이트 메서드 ---

    def set_scanning(self, is_scanning: bool):
        if is_scanning:
            self._scan_btn.config(state='disabled')
            self._pause_btn.config(state='normal', text='일시중지')
            self._cancel_btn.config(state='normal')
            self._paused = False
        else:
            self._scan_btn.config(state='normal')
            self._pause_btn.config(state='disabled', text='일시중지')
            self._cancel_btn.config(state='disabled')
            self._paused = False

    def update_progress(self, current: int, total: int, filename: str = ''):
        pct = (current / total * 100) if total > 0 else 0
        self._progress_var.set(pct)

        self._count_var.set(f'{current:,} / {total:,}개  ({pct:.1f}%)')

        # 남은 시간 추정 (일시중지 시간 제외)
        eta_text = ''
        if self._scan_start_time and current > 0:
            elapsed = time.time() - self._scan_start_time - self._total_paused_secs
            rate = current / elapsed if elapsed > 0 else 0
            if rate > 0:
                remaining = (total - current) / rate
                if remaining >= 3600:
                    eta_text = f'남은 시간: 약 {int(remaining // 3600)}시간 {int((remaining % 3600) // 60)}분'
                elif remaining >= 60:
                    eta_text = f'남은 시간: 약 {int(remaining // 60)}분 {int(remaining % 60)}초'
                else:
                    eta_text = f'남은 시간: 약 {int(remaining)}초'
        self._eta_var.set(eta_text)

        short = filename if len(filename) <= 50 else filename[:47] + '...'
        self._status_var.set(short)

    def set_processing(self, is_processing: bool):
        """결과 정리 중 indeterminate 프로그레스바 표시."""
        if is_processing:
            self._progress.config(mode='indeterminate')
            self._progress.start(12)
            self._count_var.set('')
            self._eta_var.set('')
            self._status_var.set('결과 정리 중...')
        else:
            self._progress.stop()
            self._progress.config(mode='determinate')

    def set_status(self, message: str):
        self._status_var.set(message)

    def reset_progress(self):
        self._progress_var.set(0)
        self._status_var.set('')
        self._count_var.set('')
        self._eta_var.set('')
