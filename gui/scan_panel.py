"""
scan_panel.py — 폴더 선택 + 스캔 설정 패널
"""
import time
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox
from pathlib import Path
from .theme import APP_FONT_FAMILY, APP_FONT_SIZE
from .i18n import t


def _ask_folder(parent, title: str, initialdir: Path = None) -> str | None:
    """더블클릭으로 하위폴더 없는 폴더를 바로 선택할 수 있는 커스텀 폴더 선택 다이얼로그."""
    root_path = [initialdir or Path.home()]
    selected  = [None]
    result    = [None]

    def subfolders(p: Path) -> list[Path]:
        try:
            return sorted([x for x in p.iterdir() if x.is_dir()],
                          key=lambda x: x.name.lower())
        except PermissionError:
            return []

    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.geometry('560x440')
    dlg.resizable(True, True)
    dlg.grab_set()

    top = tk.Frame(dlg)
    top.pack(fill='x', padx=8, pady=(8, 4))
    tk.Button(top, text=t('btn_navigate_up'), width=8,
              command=lambda: _navigate(root_path[0].parent)).pack(side='left', padx=(0, 6))
    path_var = tk.StringVar()
    path_entry = tk.Entry(top, textvariable=path_var, foreground='#333333')
    path_entry.pack(side='left', fill='x', expand=True)
    path_entry.bind('<Return>', lambda _e: _navigate(Path(path_var.get())))

    mid = tk.Frame(dlg)
    mid.pack(fill='both', expand=True, padx=8, pady=4)
    sb = tk.Scrollbar(mid, orient='vertical')
    sb.pack(side='right', fill='y')
    tree = ttk.Treeview(mid, yscrollcommand=sb.set, selectmode='browse', show='tree')
    tree.pack(side='left', fill='both', expand=True)
    sb.config(command=tree.yview)

    bot = tk.Frame(dlg)
    bot.pack(fill='x', padx=8, pady=(4, 8))
    ok_btn = tk.Button(bot, text=t('btn_confirm'), width=8, bg='#4CAF50', fg='white', state='disabled',
                       command=lambda: _confirm())
    ok_btn.pack(side='right', padx=(4, 0))
    tk.Button(bot, text=t('btn_cancel'), width=8, command=dlg.destroy).pack(side='right')

    def _populate(path: Path):
        tree.delete(*tree.get_children())
        path_var.set(str(path))
        for folder in subfolders(path):
            node = tree.insert('', 'end', text=f'📁  {folder.name}', values=[str(folder)])
            if subfolders(folder):
                tree.insert(node, 'end', text='', values=['__dummy__'])

    def _navigate(path: Path):
        if not path.exists():
            return
        root_path[0] = path
        selected[0] = None
        ok_btn.config(state='disabled')
        _populate(path)

    def _on_select(event):
        sel = tree.selection()
        if not sel:
            return
        val = tree.item(sel[0])['values']
        if val and val[0] != '__dummy__':
            selected[0] = Path(val[0])
            ok_btn.config(state='normal')

    def _on_double(event):
        sel = tree.selection()
        if not sel:
            return
        val = tree.item(sel[0])['values']
        if not val or val[0] == '__dummy__':
            return
        path = Path(val[0])
        if subfolders(path):
            _navigate(path)
        else:
            selected[0] = path
            _confirm()

    def _on_expand(event):
        node = tree.focus()
        children = tree.get_children(node)
        if children and tree.item(children[0])['values'] == ['__dummy__']:
            tree.delete(children[0])
            path = Path(tree.item(node)['values'][0])
            for folder in subfolders(path):
                child = tree.insert(node, 'end', text=f'📁  {folder.name}', values=[str(folder)])
                if subfolders(folder):
                    tree.insert(child, 'end', text='', values=['__dummy__'])

    def _confirm():
        if selected[0]:
            result[0] = str(selected[0])
        dlg.destroy()

    tree.bind('<<TreeviewSelect>>', _on_select)
    tree.bind('<Double-1>', _on_double)
    tree.bind('<<TreeviewOpen>>', _on_expand)

    _populate(root_path[0])
    dlg.update_idletasks()
    dw, dh = dlg.winfo_width(), dlg.winfo_height()
    px = parent.winfo_rootx() + parent.winfo_width()  // 2 - dw // 2
    py = parent.winfo_rooty() + parent.winfo_height() // 2 - dh // 2
    sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
    px = max(0, min(px, sw - dw))
    py = max(0, min(py, sh - dh))
    dlg.geometry(f'+{px}+{py}')
    dlg.wait_window()
    return result[0]


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
        self._lang_btn = tk.Button(row0, text=t('btn_lang_toggle'),
                                   command=self._on_lang_toggle, width=8)
        self._lang_btn.pack(side='right', padx=(4, 0))

        bmc = tk.Label(row0, text=t('label_sponsor'), cursor='hand2',
                       background='#FFDD00', foreground='#000000',
                       font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1, 'bold'),
                       padx=8, pady=3, relief='flat')
        bmc.pack(side='right', padx=(4, 0))
        bmc.bind('<Button-1>', lambda e: webbrowser.open('https://kimlog0415.github.io/contact/'))

        tk.Button(row0, text=t('btn_choose_folder'),
                  command=self._choose_folder, width=10).pack(side='right', padx=(4, 0))

        tk.Label(row0, text=t('label_folder')).pack(side='left')
        self._folder_var = tk.StringVar(value=t('status_no_folder_selected'))
        tk.Label(row0, textvariable=self._folder_var, anchor='w',
                 relief='sunken', foreground='#333333').pack(side='left', padx=6, fill='x', expand=True)

        # ── Row 1: 옵션 ──────────────────────────────────────────────
        self._row1 = tk.Frame(self)
        self._row1.pack(fill='x', pady=(0, 2))

        self._recursive_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self._row1, text=t('cb_include_subfolders'),
                       variable=self._recursive_var).pack(side='left')

        tk.Label(self._row1, text=t('label_search_target')).pack(side='left')

        self._images_var   = tk.BooleanVar(value=True)
        self._videos_var   = tk.BooleanVar(value=False)
        self._audio_var    = tk.BooleanVar(value=False)
        self._all_files_var = tk.BooleanVar(value=False)

        self._cb_images = tk.Checkbutton(self._row1, text=t('cb_images'),
                                         variable=self._images_var,
                                         command=self._on_filetype_toggle)
        self._cb_images.pack(side='left', padx=(4, 0))

        self._cb_videos = tk.Checkbutton(self._row1, text=t('cb_videos'),
                                         variable=self._videos_var,
                                         command=self._on_filetype_toggle)
        self._cb_videos.pack(side='left', padx=(2, 0))

        self._cb_audio = tk.Checkbutton(self._row1, text=t('cb_audio'),
                                        variable=self._audio_var,
                                        command=self._on_filetype_toggle)
        self._cb_audio.pack(side='left', padx=(2, 0))

        tk.Checkbutton(self._row1, text=t('cb_all_files'),
                       variable=self._all_files_var,
                       command=self._on_all_files_toggle).pack(side='left', padx=(8, 0))

        # 유사 이미지 검색 (이미지 체크 시에만 표시)
        self._similar_var = tk.BooleanVar(value=True)
        self._similar_cb = tk.Checkbutton(self._row1, text=t('cb_similar_images'),
                                          variable=self._similar_var,
                                          command=self._on_similar_toggle)
        self._similar_cb.pack(side='left', padx=(12, 0))  # 초기: 이미지 체크됨

        # ── Row 2: 민감도 슬라이더 (유사 이미지 검색 체크 시에만 표시) ──
        self._threshold_row = tk.Frame(self)
        self._threshold_row.pack(fill='x', pady=(0, 4))

        tk.Label(self._threshold_row, text=t('label_sensitivity')).pack(side='left', padx=(0, 4))

        slider_wrap = tk.Frame(self._threshold_row)
        slider_wrap.pack(side='left')

        self._threshold_var = tk.IntVar(value=10)
        self._slider = tk.Scale(slider_wrap, from_=0, to=20, orient='horizontal',
                                variable=self._threshold_var, length=140, showvalue=False)
        self._slider.pack()

        hint = tk.Frame(slider_wrap)
        hint.pack(fill='x')
        tk.Label(hint, text=t('label_strict'), foreground='#888888',
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE - 2)).pack(side='left')
        tk.Label(hint, text=t('label_loose'), foreground='#888888',
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE - 2)).pack(side='right')

        self._slider.bind('<Enter>', self._show_slider_tip)
        self._slider.bind('<Leave>', self._hide_slider_tip)
        self._slider.bind('<Motion>', self._update_slider_tip)

        # ── Row 3: 스캔 버튼 ─────────────────────────────────────────
        self._row_btns = tk.Frame(self)
        self._row_btns.pack(fill='x', pady=(4, 0))

        self._scan_btn = tk.Button(self._row_btns, text=t('btn_scan_start'),
                                   command=self._start_scan, width=12,
                                   bg='#4CAF50', fg='white',
                                   font=(APP_FONT_FAMILY, APP_FONT_SIZE, 'bold'))
        self._scan_btn.pack(side='left', padx=(0, 6))

        self._pause_btn = tk.Button(self._row_btns, text=t('btn_pause'),
                                    command=self._toggle_pause, width=10, state='disabled')
        self._pause_btn.pack(side='left', padx=(0, 6))

        self._cancel_btn = tk.Button(self._row_btns, text=t('btn_cancel_scan'),
                                     command=self._cancel_scan, width=8, state='disabled')
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
                 foreground='#333333', font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1)).pack(side='left')
        self._eta_var = tk.StringVar(value='')
        tk.Label(row5, textvariable=self._eta_var, anchor='e',
                 foreground='#555555', font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1)).pack(side='right')

        row6 = tk.Frame(self)
        row6.pack(fill='x')
        self._status_var = tk.StringVar(value='')
        tk.Label(row6, textvariable=self._status_var, anchor='w',
                 foreground='#888888', font=(APP_FONT_FAMILY, APP_FONT_SIZE - 2)).pack(side='left')

    # ── 슬라이더 툴팁 ────────────────────────────────────────────────

    def _show_slider_tip(self, event):
        self._tip_window = tw = tk.Toplevel(self._slider)
        tw.wm_overrideredirect(True)
        self._place_tip(event)
        tk.Label(tw, text=str(self._threshold_var.get()),
                 background='#ffffe0', relief='solid', borderwidth=1,
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1), padx=4).pack()

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
            self._similar_cb.pack(side='left', padx=(12, 0), after=self._cb_all_files)
        else:
            self._similar_cb.pack_forget()
            self._similar_var.set(False)
        self._update_threshold_visibility()

    def _update_threshold_visibility(self):
        """민감도 슬라이더 행 표시 여부 결정."""
        show = self._similar_var.get() and self._images_var.get() and not self._all_files_var.get()
        if show:
            self._threshold_row.pack(fill='x', pady=(0, 4), after=self._row1)
        else:
            self._threshold_row.pack_forget()
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
        path = _ask_folder(self, title=t('dlg_title_select_scan_folder'), initialdir=Path.home())
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
        else:
            self._scan_btn.config(state='normal')
            self._pause_btn.config(state='disabled', text=t('btn_pause'))
            self._cancel_btn.config(state='disabled')
            self._paused = False

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
