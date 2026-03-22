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

from .theme import APP_FONT_FAMILY, APP_FONT_SIZE

from .preview_card import PreviewCard, format_size

_MAX_LIST = 10  # 팝업에 표시할 최대 파일 수

def _format_file_list(paths: list) -> str:
    lines = [f'  • {p.name}' for p in paths[:_MAX_LIST]]
    if len(paths) > _MAX_LIST:
        lines.append(f'  ... 외 {len(paths) - _MAX_LIST}개')
    return '\n'.join(lines)


class ResultPanel(tk.Frame):
    """스캔 결과 표시 패널 (그룹 목록 + 미리보기)."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._exact_groups: list[list[Path]] = []
        self._similar_groups: list[list[Path]] = []
        self._current_cards: list[PreviewCard] = []
        self._card_to_group: dict = {}          # card → group_idx
        self._group_card_frames: list = []      # [(group_idx, cards_frame, cards)]
        self._show_thumb_var = tk.BooleanVar(value=True)
        self._current_preview: tuple | None = None  # (tab_data, group_indices)

        self._build()

    def _build(self):
        # 요약 행
        summary_frame = tk.Frame(self)
        summary_frame.pack(fill='x', padx=8, pady=(6, 4))

        self._summary_var = tk.StringVar(value='스캔 결과가 여기에 표시됩니다.')
        tk.Label(summary_frame, textvariable=self._summary_var,
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE), foreground='#333333').pack(side='left')
        tk.Checkbutton(summary_frame, text='썸네일 표시',
                       variable=self._show_thumb_var,
                       command=self._on_thumb_toggle).pack(side='right')

        # 탭 + 본문 영역
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill='both', expand=True, padx=6, pady=4)
        self._notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        self._exact_tab = self._make_tab('완전 중복')
        self._similar_tab = self._make_tab('유사 중복')

        self._notebook.add(self._exact_tab['frame'], text='완전 중복  ')
        self._notebook.add(self._similar_tab['frame'], text='유사 중복  ')

    def _make_tab(self, label: str) -> dict:
        frame = tk.Frame(self._notebook)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        # 왼쪽: 그룹 목록
        left = tk.Frame(frame, width=220)
        left.pack(side='left', fill='y', padx=(4, 0), pady=4)
        left.pack_propagate(False)

        tk.Label(left, text='그룹 목록', font=(APP_FONT_FAMILY, APP_FONT_SIZE, 'bold')).pack(anchor='w')

        listbox_frame = tk.Frame(left)
        listbox_frame.pack(fill='both', expand=True)

        scrollbar = tk.Scrollbar(listbox_frame, orient='vertical')
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set,
                             selectmode='extended', activestyle='none',
                             font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1), width=28)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side='right', fill='y')
        listbox.pack(side='left', fill='both', expand=True)

        # 오른쪽: 미리보기 + 버튼
        right = tk.Frame(frame)
        right.pack(side='left', fill='both', expand=True, padx=4, pady=4)

        btn_row = tk.Frame(right)
        btn_row.pack(fill='x', pady=(0, 4))

        tk.Button(btn_row, text='원본 유지 (나머지 선택)',
                  command=lambda: self._auto_select(label)).pack(side='left', padx=(0, 6))

        # 스크롤 가능한 미리보기 영역
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

        # 마우스 휠
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

        # 캔버스 너비 변경 시 카드 재배치
        def _on_canvas_resize(e, td=tab_data):
            canvas.itemconfig(canvas_window, width=e.width)
            self._relayout_cards(td)
        canvas.bind('<Configure>', _on_canvas_resize)

        listbox.bind('<<ListboxSelect>>', lambda e, td=tab_data: self._on_group_select(td))

        tk.Button(btn_row, text='전부 선택',
                  command=lambda: self._select_all()).pack(side='left', padx=(0, 6))

        tk.Button(btn_row, text='선택 항목 삭제',
                  bg='#f44336', fg='white',
                  font=(APP_FONT_FAMILY, APP_FONT_SIZE, 'bold'),
                  command=lambda: self._delete_selected(label)).pack(side='left', padx=(0, 6))

        tk.Button(btn_row, text='중복 아님',
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

    _MAX_RENDER_CARDS = 50  # 카드 렌더링 상한 (썸네일 유무 무관)

    def _delete_with_progress(self, targets: list, on_done: callable):
        """진행 다이얼로그를 띄우고 백그라운드에서 삭제 실행. 완료 시 on_done(deleted, errors) 호출."""
        total = len(targets)
        q = queue.Queue()

        # 진행 다이얼로그
        dlg = tk.Toplevel(self)
        dlg.title('삭제 중...')
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol('WM_DELETE_WINDOW', lambda: None)  # 닫기 버튼 비활성화

        tk.Label(dlg, text=f'총 {total}개 파일을 휴지통으로 이동 중...',
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE)).pack(padx=24, pady=(16, 8))

        count_var = tk.StringVar(value='0 / ' + str(total))
        tk.Label(dlg, textvariable=count_var,
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1),
                 foreground='#555555').pack()

        prog_var = tk.DoubleVar(value=0)
        ttk.Progressbar(dlg, variable=prog_var, maximum=100, length=320).pack(padx=24, pady=6)

        file_var = tk.StringVar(value='')
        tk.Label(dlg, textvariable=file_var,
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE - 2),
                 foreground='#888888', width=44).pack(padx=24, pady=(0, 16))

        # 다이얼로그 중앙 배치
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
        """카드 렌더링 없이 일괄 처리 패널 표시."""
        n_groups = len(group_indices)
        tk.Label(inner,
                 text=f'{n_groups}개 그룹  /  {total_files}개 파일 선택됨\n'
                      f'(파일이 너무 많아 미리보기를 표시하지 않습니다)',
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE),
                 foreground='#555555', justify='center').pack(pady=(40, 16))

        tk.Button(inner, text=f'원본 유지 후 나머지 삭제  ({total_files - n_groups}개 삭제 예정)',
                  bg='#f44336', fg='white',
                  font=(APP_FONT_FAMILY, APP_FONT_SIZE, 'bold'),
                  command=lambda: self._bulk_keep_and_delete(tab_data, group_indices)).pack(pady=6)

        tk.Button(inner, text=f'중복 아님  ({n_groups}개 그룹 목록에서 제거)',
                  command=lambda: self._dismiss_group(tab_data)).pack(pady=6)

    def _bulk_keep_and_delete(self, tab_data: dict, group_indices: list[int]):
        """각 그룹에서 원본 유지, 나머지 일괄 삭제 — 분석/삭제 전 과정을 백그라운드에서 처리."""
        confirmed = messagebox.askyesno(
            '일괄 삭제 확인',
            f'{len(group_indices)}개 그룹에서 원본을 제외한 나머지 파일을\n'
            '휴지통으로 이동하시겠습니까?\n\n(휴지통에서 복구할 수 있습니다)',
            icon='warning',
        )
        if not confirmed:
            return

        groups = tab_data['groups']
        q = queue.Queue()

        # 확인 직후 다이얼로그 즉시 표시
        dlg = tk.Toplevel(self)
        dlg.title('처리 중...')
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol('WM_DELETE_WINDOW', lambda: None)

        tk.Label(dlg, text=f'{len(group_indices)}개 그룹 처리 중...',
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE)).pack(padx=24, pady=(16, 8))

        count_var = tk.StringVar(value='')
        tk.Label(dlg, textvariable=count_var,
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1),
                 foreground='#555555').pack()

        prog = ttk.Progressbar(dlg, mode='indeterminate', length=320)
        prog.pack(padx=24, pady=6)
        prog.start(12)

        file_var = tk.StringVar(value='원본 파일 분석 중...')
        tk.Label(dlg, textvariable=file_var,
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE - 2),
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

            # 분석 단계
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

            # 삭제 단계
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
                        file_var.set('삭제 시작...')
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
                            messagebox.showerror('삭제 오류', '\n'.join(errors))
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

        # 너무 많으면 일괄 처리 패널 표시
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
                lbl = tk.Label(outer, text=f'── 그룹 {group_idx + 1}  ({len(group)}장) ──',
                               font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1),
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
        """캔버스 너비에 맞게 카드를 여러 행으로 재배치."""
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

    def _delete_all(self, tab_data: dict):
        """선택된 그룹(들)의 모든 파일을 휴지통으로 이동."""
        if not self._current_cards:
            messagebox.showinfo('선택 없음', '먼저 그룹을 선택해주세요.')
            return

        targets = [c.filepath for c in self._current_cards]
        names = _format_file_list(targets)
        confirmed = messagebox.askyesno(
            '전부 삭제 확인',
            f'선택된 그룹의 모든 {len(targets)}개 파일을 휴지통으로 이동하시겠습니까?\n\n{names}\n\n'
            '(휴지통에서 복구할 수 있습니다)',
            icon='warning',
        )
        if not confirmed:
            return

        def on_done(deleted, errors):
            if errors:
                messagebox.showerror('삭제 오류', '\n'.join(errors))
            sel = tab_data['listbox'].curselection()
            for group_idx in sorted(sel, reverse=True):
                tab_data['groups'].pop(group_idx)
                tab_data['listbox'].delete(group_idx)
            for w in tab_data['preview_inner'].winfo_children():
                w.destroy()
            self._current_cards = []
            self._card_to_group = {}
            self._group_card_frames = []
            self._update_summary()

        self._delete_with_progress(targets, on_done)

    def _select_all(self):
        """현재 표시된 카드 전체 선택."""
        for card in self._current_cards:
            card.set_selected(True)
            card.highlight(True)

    def _dismiss_group(self, tab_data: dict):
        """파일은 그대로 두고 선택된 그룹(들)을 목록에서 제거."""
        sel = tab_data['listbox'].curselection()
        if not sel:
            messagebox.showinfo('선택 없음', '먼저 그룹을 선택해주세요.')
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

    def _auto_select(self, label: str):
        """각 그룹에서 '원본'(해상도 높은 것 > 크기 큰 것 > 날짜 오래된 것)을 제외하고 나머지 선택."""
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

        # 그룹별로 원본 선정
        from collections import defaultdict
        groups: dict[int, list[PreviewCard]] = defaultdict(list)
        for card in self._current_cards:
            groups[self._card_to_group.get(card, 0)].append(card)

        for cards in groups.values():
            best = max(range(len(cards)), key=lambda i: score(cards[i].filepath))
            for i, card in enumerate(cards):
                card.set_selected(i != best)
                card.highlight(i != best)

    def _delete_selected(self, label: str):
        selected_cards = [c for c in self._current_cards if c.is_selected()]
        if not selected_cards:
            messagebox.showinfo('선택 없음', '삭제할 파일을 먼저 선택해주세요.')
            return

        targets = [c.filepath for c in selected_cards]
        names = _format_file_list(targets)
        confirmed = messagebox.askyesno(
            '삭제 확인',
            f'아래 {len(targets)}개 파일을 휴지통으로 이동하시겠습니까?\n\n{names}\n\n'
            '(휴지통에서 복구할 수 있습니다)',
            icon='warning',
        )
        if not confirmed:
            return

        tab_data = self._get_current_tab()

        def on_done(deleted_set, errors):
            if errors:
                messagebox.showerror('삭제 오류', '\n'.join(errors))
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
                total_size = sum(p.stat().st_size for p in group)
                savings = sum(p.stat().st_size for p in group[1:])
                lb.insert('end', f"그룹 {i+1}  ({len(group)}장, -{format_size(savings)})")
            except Exception:
                lb.insert('end', f"그룹 {i+1}  ({len(group)}장)")

        for w in tab_data['preview_inner'].winfo_children():
            w.destroy()
        self._current_cards = []

    def _update_summary(self, total: int = None):
        e = len(self._exact_tab['groups'])
        s = len(self._similar_tab['groups'])

        def calc_savings(groups):
            total = 0
            for g in groups:
                for fp in g[1:]:
                    try:
                        total += fp.stat().st_size
                    except Exception:
                        pass
            return total

        savings = calc_savings(self._exact_tab['groups']) + calc_savings(self._similar_tab['groups'])
        msg = f"완전 중복 {e}그룹 · 유사 중복 {s}그룹 · 절약 가능 {format_size(savings)}"
        if total is not None:
            msg = f"전체 {total}장 스캔 완료 — " + msg
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
        self._summary_var.set('스캔 결과가 여기에 표시됩니다.')
