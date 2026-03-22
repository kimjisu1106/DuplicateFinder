"""
scan_panel.py — 폴더 선택 + 스캔 설정 패널
"""
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path


class ScanPanel(tk.LabelFrame):
    """폴더 선택, 옵션 설정, 스캔 시작/취소 버튼을 포함하는 패널."""

    def __init__(self, parent, on_scan: callable, on_cancel: callable, **kwargs):
        super().__init__(parent, text=' 스캔 설정 ', padx=10, pady=8, **kwargs)
        self._on_scan = on_scan
        self._on_cancel = on_cancel
        self._folder: Path | None = None

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

        tk.Label(row1, text='   유사도 민감도 (해밍 거리):').pack(side='left')
        self._threshold_var = tk.IntVar(value=10)
        self._threshold_label = tk.Label(row1, text='10', width=3)
        slider = tk.Scale(row1, from_=0, to=20, orient='horizontal',
                          variable=self._threshold_var, length=160,
                          command=self._on_slider, showvalue=False)
        slider.pack(side='left', padx=4)
        self._threshold_label.pack(side='left')
        tk.Label(row1, text='← 엄격  관대 →', foreground='#888888', font=('Segoe UI', 8)).pack(side='left', padx=4)

        # 버튼 행
        row2 = tk.Frame(self)
        row2.pack(fill='x', pady=(4, 0))

        self._scan_btn = tk.Button(row2, text='스캔 시작', command=self._start_scan,
                                   width=12, bg='#4CAF50', fg='white',
                                   font=('Segoe UI', 9, 'bold'))
        self._scan_btn.pack(side='left', padx=(0, 6))

        self._cancel_btn = tk.Button(row2, text='취소', command=self._cancel_scan,
                                     width=8, state='disabled')
        self._cancel_btn.pack(side='left')

        # 진행 상황
        row3 = tk.Frame(self)
        row3.pack(fill='x', pady=(8, 0))

        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(row3, variable=self._progress_var,
                                         maximum=100, length=400)
        self._progress.pack(side='left', fill='x', expand=True, padx=(0, 8))

        self._status_var = tk.StringVar(value='')
        tk.Label(row3, textvariable=self._status_var, anchor='w',
                 width=36, foreground='#555555', font=('Segoe UI', 8)).pack(side='left')

    def _choose_folder(self):
        path = filedialog.askdirectory(title='스캔할 폴더를 선택하세요')
        if path:
            self._folder = Path(path)
            display = str(self._folder)
            if len(display) > 58:
                display = '...' + display[-55:]
            self._folder_var.set(display)

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
        self._on_scan(
            folder=self._folder,
            recursive=self._recursive_var.get(),
            threshold=self._threshold_var.get(),
        )

    def _cancel_scan(self):
        self._on_cancel()

    # --- 외부에서 호출하는 상태 업데이트 메서드 ---

    def set_scanning(self, is_scanning: bool):
        if is_scanning:
            self._scan_btn.config(state='disabled')
            self._cancel_btn.config(state='normal')
        else:
            self._scan_btn.config(state='normal')
            self._cancel_btn.config(state='disabled')

    def update_progress(self, current: int, total: int, filename: str = ''):
        pct = (current / total * 100) if total > 0 else 0
        self._progress_var.set(pct)
        short = filename if len(filename) <= 34 else filename[:31] + '...'
        self._status_var.set(short)

    def set_status(self, message: str):
        self._status_var.set(message)

    def reset_progress(self):
        self._progress_var.set(0)
        self._status_var.set('')
