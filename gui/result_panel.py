"""
result_panel.py — 결과 목록 + 미리보기 패널
"""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from send2trash import send2trash
from PIL import Image

from . import theme
from .i18n import t
from .preview_card import PreviewCard, format_size

_MAX_LIST = 10  # 팝업에 표시할 최대 파일 수

def _format_file_list(paths: list) -> str:
    lines = [f'  • {p.name}' for p in paths[:_MAX_LIST]]
    if len(paths) > _MAX_LIST:
        lines.append(t('msg_file_list_more', n=len(paths) - _MAX_LIST))
    return '\n'.join(lines)


class ResultPanel(tk.Frame):
    """스캔 결과 표시 패널 (그룹 목록 + 미리보기)."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._exact_groups: list[list[Path]] = []
        self._similar_groups: list[list[Path]] = []
        self._current_cards: list[PreviewCard] = []
        self._card_to_group: dict = {}
        self._group_card_frames: list = []
        self._show_thumb_var = tk.BooleanVar(value=True)
        self._current_preview: tuple | None = None

        self._build()

    def _build(self):
        summary_frame = tk.Frame(self)
        summary_frame.pack(fill='x', padx=8, pady=(6, 4))

        self._summary_var = tk.StringVar(value=t('status_no_results'))
        tk.Label(summary_frame, textvariable=self._summary_var,
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE), foreground='#333333').pack(side='left')
        tk.Checkbutton(summary_frame, text=t('cb_show_thumbnail'),
                       variable=self._show_thumb_var,
                       command=self._on_thumb_toggle).pack(side='right')

        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill='both', expand=True, padx=6, pady=4)
        self._notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        self._exact_tab = self._make_tab('exact')
        self._similar_tab = self._make_tab('similar')

        self._notebook.add(self._exact_tab['frame'], text=t('tab_exact_label'))
        self._notebook.add(self._similar_tab['frame'], text=t('tab_similar_label'))

    def _make_tab(self, tab_key: str) -> dict:
        frame = tk.Frame(self._notebook)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        left = tk.Frame(frame, width=220)
        left.pack(side='left', fill='y', padx=(4, 0), pady=4)
        left.pack_propagate(False)

        tk.Label(left, text=t('label_group_list'),
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE, 'bold')).pack(anchor='w')

        listbox_frame = tk.Frame(left)
        listbox_frame.pack(fill='both', expand=True)

        scrollbar = tk.Scrollbar(listbox_frame, orient='vertical')
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set,
                             selectmode='extended', activestyle='none',
                             font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 1), width=28)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side='right', fill='y')
        listbox.pack(side='left', fill='both', expand=True)

        right = tk.Frame(frame)
        right.pack(side='left', fill='both', expand=True, padx=4, pady=4)

        btn_row = tk.Frame(right)
        btn_row.pack(fill='x', pady=(0, 4))

        tk.Button(btn_row, text=t('btn_keep_original'),
                  command=lambda: self._auto_select(tab_key)).pack(side='left', padx=(0, 6))

        canvas = tk.Canvas(right, highlightthickness=0)
        v_scroll = tk.Scrollbar(right, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        preview_inner = tk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=preview_inner, anchor='nw')

        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        preview_inner.bind('<Configure>', on_configure)

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')
        canvas.bind('<MouseWheel>', _on_mousewheel)
        preview_inner.bind('<MouseWheel>', _on_mousewheel)

        tab_data = {
            'frame': frame,
            'listbox': listbox,
            'preview_inner': preview_inner,
            'canvas': canvas,
            'groups': [],
        }

        def _on_canvas_resize(e, td=tab_data):
            canvas.itemconfig(canvas_window, width=e.width)
            self._relayout_cards(td)
        canvas.bind('<Configure>', _on_canvas_resize)

        listbox.bind('<<ListboxSelect>>', lambda e, td=tab_data: self._on_group_select(td))

        tk.Button(btn_row, text=t('btn_select_all'),
                  command=lambda: self._select_all()).pack(side='left', padx=(0, 6))

        tk.Button(btn_row, text=t('btn_delete_selected'),
                  bg='#f44336', fg='white',
                  font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE, 'bold'),
                  command=lambda: self._delete_selected(tab_key)).pack(side='left', padx=(0, 6))

        tk.Button(btn_row, text=t('btn_dismiss_group'),
                  command=lambda td=tab_data: self._dismiss_group(td)).pack(side='left')

        return tab_data

    def _on_tab_changed(self, event):
        pass

    def _get_current_tab(self) -> dict:
        idx = self._notebook.index(self._notebook.select())
        return self._exact_tab if idx == 0 else self._similar_tab

    def _on_group_select(self, tab_data: dict):
        sel = tab_data['listbox'].curselection()
        if not sel:
            return
        valid = [i for i in sel if i < len(tab_data['groups'])]
        if valid:
            self._show_preview(tab_data, valid)

    _MAX_RENDER_CARDS = 50

    def _delete_with_progress(self, targets: list, on_done: callable):
        total = len(targets)
        q = queue.Queue()

        dlg = tk.Toplevel(self)
        dlg.title(t('dlg_title_deleting'))
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol('WM_DELETE_WINDOW', lambda: None)

        tk.Label(dlg, text=t('dlg_msg_moving_files', total=total),
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE)).pack(padx=24, pady=(16, 8))

        count_var = tk.StringVar(value=f'0 / {total}')
        tk.Label(dlg, textvariable=count_var,
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 1),
                 foreground='#555555').pack()

        prog_var = tk.DoubleVar(value=0)
        ttk.Progressbar(dlg, variable=prog_var, maximum=100, length=320).pack(padx=24, pady=6)

        file_var = tk.StringVar(value='')
        tk.Label(dlg, textvariable=file_var,
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 2),
                 foreground='#888888', width=44).pack(padx=24, pady=(0, 16))

        dlg.update_idletasks()
        px = self.winfo_rootx() + self.winfo_width() // 2 - dlg.winfo_width() // 2
        py = self.winfo_rooty() + self.winfo_height() // 2 - dlg.winfo_height() // 2
        dlg.geometry(f'+{px}+{py}')

        def _worker():
            deleted, errors = set(), []
            for i, fp in enumerate(targets):
                print(f"[삭제→휴지통] {fp}")
                try:
                    send2trash(str(fp))
                    deleted.add(fp)
                except Exception as e:
                    errors.append(f"{fp.name}: {e}")
                q.put(('progress', i + 1, fp.name))
            q.put(('done', deleted, errors))

        threading.Thread(target=_worker, daemon=True).start()

        def _poll():
            try:
                while True:
                    msg = q.get_nowait()
                    if msg[0] == 'progress':
                        _, i, name = msg
                        prog_var.set(i / total * 100)
                        count_var.set(f'{i} / {total}')
                        short = name if len(name) <= 40 else name[:37] + '...'
                        file_var.set(short)
                    elif msg[0] == 'done':
                        _, deleted, errors = msg
                        dlg.destroy()
                        on_done(deleted, errors)
                        return
            except queue.Empty:
                pass
            dlg.after(50, _poll)

        _poll()

    def _show_bulk_panel(self, inner, tab_data: dict, group_indices: list[int], total_files: int):
        n_groups = len(group_indices)
        tk.Label(inner,
                 text=t('status_too_many_cards', n_groups=n_groups, total_files=total_files),
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE),
                 foreground='#555555', justify='center').pack(pady=(40, 16))

        tk.Button(inner, text=t('btn_bulk_keep_delete', n=total_files - n_groups),
                  bg='#f44336', fg='white',
                  font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE, 'bold'),
                  command=lambda: self._bulk_keep_and_delete(tab_data, group_indices)).pack(pady=6)

        tk.Button(inner, text=t('btn_bulk_dismiss', n=n_groups),
                  command=lambda: self._dismiss_group(tab_data)).pack(pady=6)

    def _bulk_keep_and_delete(self, tab_data: dict, group_indices: list[int]):
        confirmed = messagebox.askyesno(
            t('dlg_title_bulk_delete_confirm'),
            t('dlg_msg_bulk_delete_confirm', n=len(group_indices)),
            icon='warning',
        )
        if not confirmed:
            return

        groups = tab_data['groups']
        q = queue.Queue()

        dlg = tk.Toplevel(self)
        dlg.title(t('dlg_title_processing'))
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol('WM_DELETE_WINDOW', lambda: None)

        tk.Label(dlg, text=t('dlg_msg_processing_groups', n=len(group_indices)),
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE)).pack(padx=24, pady=(16, 8))

        count_var = tk.StringVar(value='')
        tk.Label(dlg, textvariable=count_var,
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 1),
                 foreground='#555555').pack()

        prog = ttk.Progressbar(dlg, mode='indeterminate', length=320)
        prog.pack(padx=24, pady=6)
        prog.start(12)

        file_var = tk.StringVar(value=t('status_analyzing_originals'))
        tk.Label(dlg, textvariable=file_var,
                 font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 2),
                 foreground='#888888', width=44).pack(padx=24, pady=(0, 16))

        dlg.update_idletasks()
        px = self.winfo_rootx() + self.winfo_width() // 2 - dlg.winfo_width() // 2
        py = self.winfo_rooty() + self.winfo_height() // 2 - dlg.winfo_height() // 2
        dlg.geometry(f'+{px}+{py}')

        def _worker():
            def score(fp):
                try:
                    stat = fp.stat()
                    size, mtime = stat.st_size, stat.st_mtime
                except Exception:
                    size, mtime = 0, 0
                try:
                    with Image.open(fp) as img:
                        res = img.width * img.height
                except Exception:
                    res = 0
                return (res, size, -mtime)

            targets = []
            for group_idx in group_indices:
                if group_idx >= len(groups):
                    continue
                group = groups[group_idx]
                best = max(range(len(group)), key=lambda i: score(group[i]))
                targets.extend(fp for i, fp in enumerate(group) if i != best)

            if not targets:
                q.put(('done', set(), []))
                return

            q.put(('ready', len(targets)))

            deleted, errors = set(), []
            for i, fp in enumerate(targets):
                print(f"[삭제→휴지통] {fp}")
                try:
                    send2trash(str(fp))
                    deleted.add(fp)
                except Exception as e:
                    errors.append(f"{fp.name}: {e}")
                q.put(('progress', i + 1, len(targets), fp.name))
            q.put(('done', deleted, errors))

        threading.Thread(target=_worker, daemon=True).start()

        def _poll():
            try:
                while True:
                    msg = q.get_nowait()
                    if msg[0] == 'ready':
                        total = msg[1]
                        prog.stop()
                        prog.config(mode='determinate', maximum=100)
                        count_var.set(f'0 / {total}')
                        file_var.set(t('status_deletion_started'))
                    elif msg[0] == 'progress':
                        _, i, total, name = msg
                        prog['value'] = i / total * 100
                        count_var.set(f'{i} / {total}')
                        short = name if len(name) <= 40 else name[:37] + '...'
                        file_var.set(short)
                    elif msg[0] == 'done':
                        _, deleted, errors = msg
                        dlg.destroy()
                        if errors:
                            messagebox.showerror(t('dlg_title_deletion_error'), '\n'.join(errors))
                        for group_idx in sorted(group_indices, reverse=True):
                            if group_idx >= len(groups):
                                continue
                            tab_data['groups'][group_idx] = [
                                fp for fp in groups[group_idx] if fp not in deleted
                            ]
                            if len(tab_data['groups'][group_idx]) < 2:
                                tab_data['groups'].pop(group_idx)
                                tab_data['listbox'].delete(group_idx)
                        for w in tab_data['preview_inner'].winfo_children():
                            w.destroy()
                        self._current_cards = []
                        self._card_to_group = {}
                        self._group_card_frames = []
                        self._current_preview = None
                        self._update_summary()
                        return
            except queue.Empty:
                pass
            dlg.after(50, _poll)

        _poll()

    def _on_thumb_toggle(self):
        if self._current_preview:
            self._show_preview(*self._current_preview)

    def _show_preview(self, tab_data: dict, group_indices: list[int]):
        self._current_preview = (tab_data, group_indices)
        inner = tab_data['preview_inner']
        for w in inner.winfo_children():
            w.destroy()
        self._current_cards = []
        self._card_to_group = {}
        self._group_card_frames = []

        groups = tab_data['groups']
        total_files = sum(len(groups[i]) for i in group_indices if i < len(groups))

        if total_files > self._MAX_RENDER_CARDS:
            self._show_bulk_panel(inner, tab_data, group_indices, total_files)
            tab_data['canvas'].yview_moveto(0)
            return

        show_thumb = self._show_thumb_var.get()
        multi = len(group_indices) > 1

        for group_idx in group_indices:
            if group_idx >= len(groups):
                continue
            group = groups[group_idx]

            def _scroll(e, c=tab_data['canvas']):
                c.yview_scroll(int(-1 * (e.delta / 120)), 'units')

            outer = tk.Frame(inner)
            outer.pack(fill='x', pady=(4, 0))
            outer.bind('<MouseWheel>', _scroll)

            if multi:
                lbl = tk.Label(outer,
                               text=t('label_group_separator', idx=group_idx + 1, n=len(group)),
                               font=(theme.APP_FONT_FAMILY, theme.APP_FONT_SIZE - 1),
                               foreground='#888888', anchor='w')
                lbl.pack(fill='x', padx=6, pady=(4, 2))
                lbl.bind('<MouseWheel>', _scroll)

            cards_frame = tk.Frame(outer)
            cards_frame.pack(fill='x')
            cards_frame.bind('<MouseWheel>', _scroll)

            cards = []
            for fp in group:
                card = PreviewCard(cards_frame, fp, show_thumb=show_thumb)
                self._current_cards.append(card)
                self._card_to_group[card] = group_idx
                cards.append(card)
                card.bind('<MouseWheel>', _scroll)

            self._group_card_frames.append((group_idx, cards_frame, cards))

        self._relayout_cards(tab_data)
        tab_data['canvas'].yview_moveto(0)

    def _relayout_cards(self, tab_data: dict):
        if not self._group_card_frames:
            return
        canvas = tab_data['canvas']
        canvas.update_idletasks()
        width = canvas.winfo_width()
        if width < 50:
            width = 600
        card_width = 230
        cols = max(1, width // card_width)
        for _, cards_frame, cards in self._group_card_frames:
            for i, card in enumerate(cards):
                card.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky='n')

    def _select_all(self):
        for card in self._current_cards:
            card.set_selected(True)
            card.highlight(True)

    def _dismiss_group(self, tab_data: dict):
        sel = tab_data['listbox'].curselection()
        if not sel:
            messagebox.showinfo(t('dlg_title_no_selection'), t('dlg_msg_select_group_first'))
            return
        for group_idx in sorted(sel, reverse=True):
            tab_data['groups'].pop(group_idx)
            tab_data['listbox'].delete(group_idx)
        for w in tab_data['preview_inner'].winfo_children():
            w.destroy()
        self._current_cards = []
        self._card_to_group = {}
        self._group_card_frames = []
        self._update_summary()

    def _auto_select(self, tab_key: str):
        if not self._current_cards:
            return

        def score(fp: Path):
            try:
                stat = fp.stat()
                size = stat.st_size
                mtime = stat.st_mtime
            except Exception:
                size, mtime = 0, 0
            try:
                with Image.open(fp) as img:
                    res = img.width * img.height
            except Exception:
                res = 0
            return (res, size, -mtime)

        from collections import defaultdict
        groups: dict[int, list[PreviewCard]] = defaultdict(list)
        for card in self._current_cards:
            groups[self._card_to_group.get(card, 0)].append(card)

        for cards in groups.values():
            best = max(range(len(cards)), key=lambda i: score(cards[i].filepath))
            for i, card in enumerate(cards):
                card.set_selected(i != best)
                card.highlight(i != best)

    def _delete_selected(self, tab_key: str):
        selected_cards = [c for c in self._current_cards if c.is_selected()]
        if not selected_cards:
            messagebox.showinfo(t('dlg_title_no_selection'), t('dlg_msg_select_files_first'))
            return

        targets = [c.filepath for c in selected_cards]
        names = _format_file_list(targets)
        confirmed = messagebox.askyesno(
            t('dlg_title_delete_confirm'),
            t('dlg_msg_delete_confirm', n=len(targets), names=names),
            icon='warning',
        )
        if not confirmed:
            return

        tab_data = self._get_current_tab()

        def on_done(deleted_set, errors):
            if errors:
                messagebox.showerror(t('dlg_title_deletion_error'), '\n'.join(errors))
            affected = sorted(
                {self._card_to_group[c] for c in selected_cards if c.filepath in deleted_set},
                reverse=True,
            )
            for group_idx in affected:
                tab_data['groups'][group_idx] = [
                    fp for fp in tab_data['groups'][group_idx] if fp not in deleted_set
                ]
                if len(tab_data['groups'][group_idx]) < 2:
                    tab_data['groups'].pop(group_idx)
                    tab_data['listbox'].delete(group_idx)
            self._update_summary()
            remaining_sel = [i for i in tab_data['listbox'].curselection()
                             if i < len(tab_data['groups'])]
            if remaining_sel:
                self._show_preview(tab_data, remaining_sel)
            else:
                for w in tab_data['preview_inner'].winfo_children():
                    w.destroy()
                self._current_cards = []
                self._card_to_group = {}
                self._group_card_frames = []

        self._delete_with_progress(targets, on_done)

    # --- 외부 호출 메서드 ---

    def show_results(self, exact_groups: list[list[Path]],
                     similar_groups: list[list[Path]], total: int):
        self._exact_groups = exact_groups
        self._similar_groups = similar_groups
        self._populate_tab(self._exact_tab, exact_groups)
        self._populate_tab(self._similar_tab, similar_groups)
        self._update_summary(total)

    def _populate_tab(self, tab_data: dict, groups: list[list[Path]]):
        tab_data['groups'] = [list(g) for g in groups]
        lb = tab_data['listbox']
        lb.delete(0, 'end')

        for i, group in enumerate(groups):
            try:
                savings = sum(p.stat().st_size for p in group[1:])
                lb.insert('end', t('label_group_info_savings',
                                   idx=i + 1, n=len(group), savings=format_size(savings)))
            except Exception:
                lb.insert('end', t('label_group_info', idx=i + 1, n=len(group)))

        for w in tab_data['preview_inner'].winfo_children():
            w.destroy()
        self._current_cards = []

    def _update_summary(self, total: int = None):
        e = len(self._exact_tab['groups'])
        s = len(self._similar_tab['groups'])

        def calc_savings(groups):
            result = 0
            for g in groups:
                for fp in g[1:]:
                    try:
                        result += fp.stat().st_size
                    except Exception:
                        pass
            return result

        savings = calc_savings(self._exact_tab['groups']) + calc_savings(self._similar_tab['groups'])
        msg = t('status_summary', e=e, s=s, savings=format_size(savings))
        if total is not None:
            msg = t('status_summary_total', total=total, msg=msg)
        self._summary_var.set(msg)

    def clear(self):
        self._exact_tab['groups'] = []
        self._similar_tab['groups'] = []
        self._exact_tab['listbox'].delete(0, 'end')
        self._similar_tab['listbox'].delete(0, 'end')
        for w in self._exact_tab['preview_inner'].winfo_children():
            w.destroy()
        for w in self._similar_tab['preview_inner'].winfo_children():
            w.destroy()
        self._current_cards = []
        self._card_to_group = {}
        self._group_card_frames = []
        self._summary_var.set(t('status_no_results'))
