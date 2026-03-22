"""
result_panel.py — 결과 목록 + 미리보기 패널
"""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from send2trash import send2trash
from PIL import Image

from .theme import APP_FONT_FAMILY, APP_FONT_SIZE

from .preview_card import PreviewCard, format_size


class ResultPanel(tk.Frame):
    """스캔 결과 표시 패널 (그룹 목록 + 미리보기)."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._exact_groups: list[list[Path]] = []
        self._similar_groups: list[list[Path]] = []
        self._current_cards: list[PreviewCard] = []

        self._build()

    def _build(self):
        # 요약 행
        summary_frame = tk.Frame(self)
        summary_frame.pack(fill='x', padx=8, pady=(6, 4))

        self._summary_var = tk.StringVar(value='스캔 결과가 여기에 표시됩니다.')
        tk.Label(summary_frame, textvariable=self._summary_var,
                 font=(APP_FONT_FAMILY, APP_FONT_SIZE), foreground='#333333').pack(side='left')

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
                             selectmode='single', activestyle='none',
                             font=(APP_FONT_FAMILY, APP_FONT_SIZE - 1), width=28)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side='right', fill='y')
        listbox.pack(side='left', fill='both', expand=True)

        # 오른쪽: 미리보기 + 버튼
        right = tk.Frame(frame)
        right.pack(side='left', fill='both', expand=True, padx=4, pady=4)

        btn_row = tk.Frame(right)
        btn_row.pack(fill='x', pady=(0, 4))

        keep_btn = tk.Button(btn_row, text='원본 유지 (나머지 선택)',
                             command=lambda: self._auto_select(label))
        keep_btn.pack(side='left', padx=(0, 6))

        delete_btn = tk.Button(btn_row, text='선택 항목 삭제',
                               bg='#f44336', fg='white',
                               font=(APP_FONT_FAMILY, APP_FONT_SIZE, 'bold'),
                               command=lambda: self._delete_selected(label))
        delete_btn.pack(side='left', padx=(0, 6))

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
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))

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

        listbox.bind('<<ListboxSelect>>', lambda e, td=tab_data: self._on_group_select(td))

        tk.Button(btn_row, text='전부 삭제',
                  bg='#b71c1c', fg='white',
                  font=(APP_FONT_FAMILY, APP_FONT_SIZE, 'bold'),
                  command=lambda td=tab_data: self._delete_all(td)).pack(side='left')

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
        idx = sel[0]
        groups = tab_data['groups']
        if idx >= len(groups):
            return
        self._show_preview(tab_data, groups[idx])

    def _show_preview(self, tab_data: dict, group: list[Path]):
        inner = tab_data['preview_inner']
        for w in inner.winfo_children():
            w.destroy()
        self._current_cards = []

        for fp in group:
            card = PreviewCard(inner, fp)
            card.pack(side='left', padx=6, pady=6, anchor='n')
            self._current_cards.append(card)

        tab_data['canvas'].yview_moveto(0)

    def _delete_all(self, tab_data: dict):
        """현재 그룹의 모든 파일을 휴지통으로 이동."""
        if not self._current_cards:
            messagebox.showinfo('선택 없음', '먼저 그룹을 선택해주세요.')
            return

        targets = [c.filepath for c in self._current_cards]
        names = '\n'.join(f'  • {p.name}' for p in targets)
        confirmed = messagebox.askyesno(
            '전부 삭제 확인',
            f'이 그룹의 모든 {len(targets)}개 파일을 휴지통으로 이동하시겠습니까?\n\n{names}\n\n'
            '(휴지통에서 복구할 수 있습니다)',
            icon='warning',
        )
        if not confirmed:
            return

        errors = []
        for fp in targets:
            print(f"[삭제→휴지통] {fp}")
            try:
                send2trash(str(fp))
            except Exception as e:
                errors.append(f"{fp.name}: {e}")

        if errors:
            messagebox.showerror('삭제 오류', '\n'.join(errors))

        sel = tab_data['listbox'].curselection()
        if sel:
            group_idx = sel[0]
            tab_data['groups'].pop(group_idx)
            tab_data['listbox'].delete(group_idx)
            for w in tab_data['preview_inner'].winfo_children():
                w.destroy()
            self._current_cards = []
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

        best_idx = max(range(len(self._current_cards)),
                       key=lambda i: score(self._current_cards[i].filepath))

        for i, card in enumerate(self._current_cards):
            card.set_selected(i != best_idx)
            card.highlight(i != best_idx)

    def _delete_selected(self, label: str):
        targets = [c.filepath for c in self._current_cards if c.is_selected()]
        if not targets:
            messagebox.showinfo('선택 없음', '삭제할 파일을 먼저 선택해주세요.')
            return

        names = '\n'.join(f'  • {p.name}' for p in targets)
        confirmed = messagebox.askyesno(
            '삭제 확인',
            f'아래 {len(targets)}개 파일을 휴지통으로 이동하시겠습니까?\n\n{names}\n\n'
            '(휴지통에서 복구할 수 있습니다)',
            icon='warning',
        )
        if not confirmed:
            return

        errors = []
        for fp in targets:
            print(f"[삭제→휴지통] {fp}")
            try:
                send2trash(str(fp))
            except Exception as e:
                errors.append(f"{fp.name}: {e}")

        if errors:
            messagebox.showerror('삭제 오류', '\n'.join(errors))

        # 현재 그룹에서 삭제된 카드 제거
        tab_data = self._get_current_tab()
        sel = tab_data['listbox'].curselection()
        if sel:
            group_idx = sel[0]
            deleted_set = set(targets)
            tab_data['groups'][group_idx] = [
                fp for fp in tab_data['groups'][group_idx] if fp not in deleted_set
            ]
            remaining = tab_data['groups'][group_idx]
            if len(remaining) < 2:
                # 그룹이 더 이상 중복이 아니므로 제거
                tab_data['groups'].pop(group_idx)
                tab_data['listbox'].delete(group_idx)
                for w in tab_data['preview_inner'].winfo_children():
                    w.destroy()
                self._current_cards = []
                self._update_summary()
            else:
                self._show_preview(tab_data, remaining)

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
        self._summary_var.set('스캔 결과가 여기에 표시됩니다.')
