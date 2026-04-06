"""
scan_panel.py — 폴더 선택 + 스캔 설정 패널
"""
import time
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from . import theme
from .i18n import t, get_language



class ScanPanel(tk.LabelFrame):
    """폴더 선택, 옵션 설정, 스캔 시작/취소 버튼을 포함하는 패널."""

    def __init__(self, parent, on_scan: callable, on_cancel: callable,
                 on_pause: callable, on_lang_toggle: callable, **kwargs):
        super().__init__(parent, text=t('label_frame_scan_settings'), padx=10, pady=8, **kwargs)
        self._on_scan = on_scan
        self._on_cancel = on_cancel
        self._on_pause = on_pause
        self._on_lang_toggle = on_lang_toggle
        self._folder: Path | None = None
        self._paused = False
        self._scan_start_time: float | None = None
        self._pause_start_time: float | None = None
        self._total_paused_secs: float = 0.0
        self._tip_window: tk.Toplevel | None = None

        self._build()

    def _build(self):
        # ── Row 0: 폴더 선택 + 우측 버튼 ────────────────────────────
        row0 = tk.Frame(self)
        row0.pack(fill='x', pady=(0, 6))

        # 우측 버튼 먼저 팩 (공간 부족 시 path label이 줄어들도록)
        _opposite_font = 'Malgun Gothic' if get_language() == 'en' else 'Segoe UI'
        self._lang_btn = tk.Button(row0, text=t('btn_lang_toggle'),
                                   command=self._on_lang_toggle, width=8,
                                   font=(_opposite_font, theme.APP_FONT_SIZE))
        self._lang_btn.pack(side='right', padx=(4, 0))

        bmc = tk.Label(row0, text=t('label_sponsor'), cursor='hand2',
                       background='#FFDD00', foreground='#000000',
                       font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 1, 'bold'),
                       padx=8, pady=3, relief='flat')
        bmc.pack(side='right', padx=(4, 0))
        bmc.bind('<Button-1>', lambda e: webbrowser.open('https://kimlog1203.netlify.app/contact/'))

        self._folder_btn = tk.Button(row0, text=t('btn_choose_folder'),
                                     command=self._choose_folder, width=10)
        self._folder_btn.pack(side='right', padx=(4, 0))

        tk.Label(row0, text=t('label_folder')).pack(side='left')
        self._folder_var = tk.StringVar(value=t('status_no_folder_selected'))
        tk.Label(row0, textvariable=self._folder_var, anchor='w',
                 relief='sunken', foreground='#333333').pack(side='left', padx=6, fill='x', expand=True)

        # ── Row 1: 옵션 ──────────────────────────────────────────────
        self._row1 = tk.Frame(self)
        self._row1.pack(fill='x', pady=(0, 2))

        self._recursive_var = tk.BooleanVar(value=True)
        self._recursive_cb = tk.Checkbutton(self._row1, text=t('cb_include_subfolders'),
                                            variable=self._recursive_var)
        self._recursive_cb.pack(side='left', anchor='n')

        tk.Label(self._row1, text=t('label_search_target')).pack(side='left', anchor='n')

        self._images_var   = tk.BooleanVar(value=True)
        self._videos_var   = tk.BooleanVar(value=False)
        self._audio_var    = tk.BooleanVar(value=False)
        self._all_files_var = tk.BooleanVar(value=False)

        self._cb_images = tk.Checkbutton(self._row1, text=t('cb_images'),
                                         variable=self._images_var,
                                         command=self._on_filetype_toggle)
        self._cb_images.pack(side='left', padx=(4, 0), anchor='n')

        self._cb_videos = tk.Checkbutton(self._row1, text=t('cb_videos'),
                                         variable=self._videos_var,
                                         command=self._on_filetype_toggle)
        self._cb_videos.pack(side='left', padx=(2, 0), anchor='n')

        self._cb_audio = tk.Checkbutton(self._row1, text=t('cb_audio'),
                                        variable=self._audio_var,
                                        command=self._on_filetype_toggle)
        self._cb_audio.pack(side='left', padx=(2, 0), anchor='n')

        self._cb_all_files = tk.Checkbutton(self._row1, text=t('cb_all_files'),
                                            variable=self._all_files_var,
                                            command=self._on_all_files_toggle)
        self._cb_all_files.pack(side='left', padx=(8, 0), anchor='n')

        # 유사 이미지 검색 (이미지 체크 시에만 표시)
        self._similar_var = tk.BooleanVar(value=True)
        self._similar_cb = tk.Checkbutton(self._row1, text=t('cb_similar_images'),
                                          variable=self._similar_var,
                                          command=self._on_similar_toggle)
        self._similar_cb.pack(side='left', padx=(12, 0), anchor='n')  # 초기: 이미지 체크됨

        # 민감도 슬라이더 (유사 이미지 검색 우측, 체크 시에만 표시)
        self._threshold_frame = tk.Frame(self._row1)

        tk.Label(self._threshold_frame, text=t('label_sensitivity')).pack(side='left', padx=(0, 4), anchor='n', pady=(2, 0))

        slider_wrap = tk.Frame(self._threshold_frame)
        slider_wrap.pack(side='left', pady=(3, 0))

        self._threshold_var = tk.IntVar(value=10)
        self._slider = tk.Scale(slider_wrap, from_=0, to=20, orient='horizontal',
                                variable=self._threshold_var, length=120, showvalue=False)
        self._slider.pack()

        hint = tk.Frame(slider_wrap)
        hint.pack(fill='x')
        tk.Label(hint, text=t('label_strict'), foreground='#888888',
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 2)).pack(side='left')
        tk.Label(hint, text=t('label_loose'), foreground='#888888',
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 2)).pack(side='right')

        self._slider.bind('<Enter>', self._show_slider_tip)
        self._slider.bind('<Leave>', self._hide_slider_tip)
        self._slider.bind('<Motion>', self._update_slider_tip)

        # 초기 표시: 유사 이미지 검색 기본 체크 상태이므로 슬라이더 표시
        self._threshold_frame.pack(side='left', padx=(8, 0), anchor='n')

        # ── Row 2: 스캔 버튼 ─────────────────────────────────────────
        self._row_btns = tk.Frame(self)
        self._row_btns.pack(fill='x', pady=(4, 0))

        self._scan_btn = tk.Button(self._row_btns, text=t('btn_scan_start'),
                                   command=self._start_scan, width=12,
                                   bg='#4CAF50', fg='white', disabledforeground='white',
                                   font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE, 'bold'))
        self._scan_btn.pack(side='left', padx=(0, 6))

        self._pause_btn = tk.Button(self._row_btns, text=t('btn_pause'),
                                    command=self._toggle_pause, width=10, state='disabled',
                                    bg='#F59E0B')
        self._pause_btn.pack(side='left', padx=(0, 6))

        self._cancel_btn = tk.Button(self._row_btns, text=t('btn_cancel_scan'),
                                     command=self._cancel_scan, width=8, state='disabled',
                                     bg='#6B7280', fg='white', disabledforeground='white')
        self._cancel_btn.pack(side='left')

        # ── Row 4-6: 진행 상황 ───────────────────────────────────────
        row4 = tk.Frame(self)
        row4.pack(fill='x', pady=(8, 0))
        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(row4, variable=self._progress_var, maximum=100)
        self._progress.pack(fill='x', expand=True)

        row5 = tk.Frame(self)
        row5.pack(fill='x', pady=(2, 0))
        self._count_var = tk.StringVar(value='')
        tk.Label(row5, textvariable=self._count_var, anchor='w',
                 foreground='#333333', font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 1)).pack(side='left')
        self._eta_var = tk.StringVar(value='')
        tk.Label(row5, textvariable=self._eta_var, anchor='e',
                 foreground='#555555', font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 1)).pack(side='right')

        row6 = tk.Frame(self)
        row6.pack(fill='x')
        self._status_var = tk.StringVar(value='')
        tk.Label(row6, textvariable=self._status_var, anchor='w',
                 foreground='#888888', font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 2)).pack(side='left')

    # ── 슬라이더 툴팁 ────────────────────────────────────────────────

    def _show_slider_tip(self, event):
        self._tip_window = tw = tk.Toplevel(self._slider)
        tw.wm_overrideredirect(True)
        self._place_tip(event)
        tk.Label(tw, text=str(self._threshold_var.get()),
                 background='#ffffe0', relief='solid', borderwidth=1,
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 1), padx=4).pack()

    def _hide_slider_tip(self, event):
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None

    def _update_slider_tip(self, event):
        if self._tip_window:
            self._place_tip(event)
            for w in self._tip_window.winfo_children():
                w.config(text=str(self._threshold_var.get()))

    def _place_tip(self, event):
        x = self._slider.winfo_rootx() + event.x
        y = self._slider.winfo_rooty() - 28
        self._tip_window.wm_geometry(f'+{x}+{y}')

    # ── 가시성 제어 ──────────────────────────────────────────────────

    def _update_similar_visibility(self):
        """유사 이미지 검색 체크박스 표시 여부 결정."""
        show = self._images_var.get() and not self._all_files_var.get()
        if show:
            self._similar_cb.pack(side='left', padx=(12, 0), anchor='n', after=self._cb_all_files)  # 재표시
        else:
            self._similar_cb.pack_forget()
            self._similar_var.set(False)
        self._update_threshold_visibility()

    def _update_threshold_visibility(self):
        """민감도 슬라이더 표시 여부 결정 (similar_cb 우측 인라인)."""
        show = self._similar_var.get() and self._images_var.get() and not self._all_files_var.get()
        if show:
            self._threshold_frame.pack(side='left', padx=(8, 0), anchor='n', after=self._similar_cb)
        else:
            self._threshold_frame.pack_forget()
            self._hide_slider_tip(None)

    # ── 이벤트 핸들러 ────────────────────────────────────────────────

    def _on_all_files_toggle(self):
        if self._all_files_var.get():
            self._cb_images.config(state='disabled')
            self._cb_videos.config(state='disabled')
            self._cb_audio.config(state='disabled')
        else:
            self._cb_images.config(state='normal')
            self._cb_videos.config(state='normal')
            self._cb_audio.config(state='normal')
        self._update_similar_visibility()

    def _on_filetype_toggle(self):
        if self._videos_var.get() or self._audio_var.get():
            self._similar_var.set(False)
        self._update_similar_visibility()

    def _on_similar_toggle(self):
        self._update_threshold_visibility()

    def _choose_folder(self):
        path = filedialog.askdirectory(
            title=t('dlg_title_select_scan_folder'),
            initialdir=str(self._folder) if self._folder else str(Path.home()),
            parent=self,
        )
        if path:
            self._folder = Path(path)
            display = str(self._folder)
            if len(display) > 58:
                display = '...' + display[-55:]
            self._folder_var.set(display)

    def _start_scan(self):
        if self._folder is None:
            messagebox.showwarning(t('dlg_title_no_folder'), t('dlg_msg_select_folder_first'))
            return
        self._scan_btn.config(state='disabled')
        self._cancel_btn.config(state='normal')
        self._progress_var.set(0)
        self._status_var.set(t('status_scan_preparing'))
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
            include_images=self._images_var.get(),
            include_videos=self._videos_var.get(),
            include_audio=self._audio_var.get(),
            include_all=self._all_files_var.get(),
        )

    def _toggle_pause(self):
        self._paused = not self._paused
        if self._paused:
            self._pause_start_time = time.time()
            self._pause_btn.config(text=t('btn_resume'))
            self._status_var.set(t('status_paused'))
        else:
            if self._pause_start_time:
                self._total_paused_secs += time.time() - self._pause_start_time
                self._pause_start_time = None
            self._pause_btn.config(text=t('btn_pause'))
        self._on_pause(self._paused)

    def _cancel_scan(self):
        self._paused = False
        self._on_cancel()

    # ── 외부에서 호출하는 상태 업데이트 메서드 ──────────────────────

    def set_scanning(self, is_scanning: bool):
        if is_scanning:
            self._scan_btn.config(state='disabled')
            self._pause_btn.config(state='normal', text=t('btn_pause'))
            self._cancel_btn.config(state='normal')
            self._paused = False
            for w in (self._folder_btn, self._recursive_cb, self._cb_images,
                      self._cb_videos, self._cb_audio, self._cb_all_files,
                      self._similar_cb, self._slider, self._lang_btn):
                w.config(state='disabled')
        else:
            self._scan_btn.config(state='normal')
            self._pause_btn.config(state='disabled', text=t('btn_pause'))
            self._cancel_btn.config(state='disabled')
            self._paused = False
            for w in (self._folder_btn, self._recursive_cb, self._cb_all_files,
                      self._similar_cb, self._slider, self._lang_btn):
                w.config(state='normal')
            self._on_all_files_toggle()  # images/videos/audio 상태 복원

    def update_progress(self, current: int, total: int, filename: str = ''):
        pct = (current / total * 100) if total > 0 else 0
        self._progress_var.set(pct)
        self._count_var.set(t('status_progress_count',
                               current=f'{current:,}', total=f'{total:,}', pct=pct))

        eta_text = ''
        if self._scan_start_time and current > 0:
            elapsed = time.time() - self._scan_start_time - self._total_paused_secs
            rate = current / elapsed if elapsed > 0 else 0
            if rate > 0:
                remaining = (total - current) / rate
                if remaining >= 3600:
                    eta_text = t('status_eta_hours_mins',
                                 h=int(remaining // 3600), m=int((remaining % 3600) // 60))
                elif remaining >= 60:
                    eta_text = t('status_eta_mins_secs',
                                 m=int(remaining // 60), s=int(remaining % 60))
                else:
                    eta_text = t('status_eta_secs', s=int(remaining))
        self._eta_var.set(eta_text)

        short = filename if len(filename) <= 50 else filename[:47] + '...'
        self._status_var.set(short)

    def set_processing(self, is_processing: bool):
        if is_processing:
            self._progress.config(mode='indeterminate')
            self._progress.start(12)
            self._count_var.set('')
            self._eta_var.set('')
            self._status_var.set(t('status_processing_results'))
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
