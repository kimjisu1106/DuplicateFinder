"""
i18n.py — 한국어 / 영어 텍스트 딕셔너리 + t() 함수
"""

_LANG = 'ko'

_STRINGS: dict[str, dict[str, str]] = {
    # ── 폴더 선택 다이얼로그 ─────────────────────────────────────────
    'dlg_title_folder_select':      {'ko': '폴더 선택',             'en': 'Select Folder'},
    'btn_navigate_up':              {'ko': '▲ 위로',                'en': '▲ Up'},
    'btn_confirm':                  {'ko': '확인',                   'en': 'OK'},
    'btn_cancel':                   {'ko': '취소',                   'en': 'Cancel'},

    # ── 스캔 설정 패널 ───────────────────────────────────────────────
    'label_frame_scan_settings':    {'ko': ' 스캔 설정 ',            'en': ' Scan Settings '},
    'label_folder':                 {'ko': '폴더:',                  'en': 'Folder:'},
    'status_no_folder_selected':    {'ko': '선택된 폴더 없음',        'en': 'No folder selected'},
    'btn_choose_folder':            {'ko': '폴더 선택',              'en': 'Browse'},
    'cb_include_subfolders':        {'ko': '하위 폴더 포함',          'en': 'Include subfolders'},
    'label_search_target':          {'ko': '   검색 대상:',           'en': '   Search:'},
    'cb_images':                    {'ko': '이미지',                  'en': 'Images'},
    'cb_videos':                    {'ko': '영상',                   'en': 'Videos'},
    'cb_audio':                     {'ko': '오디오',                  'en': 'Audio'},
    'cb_all_files':                 {'ko': '전체 파일 (확장자 무관)',   'en': 'All files (any extension)'},
    'cb_similar_images':            {'ko': '유사 이미지 검색',         'en': 'Similar image search'},
    'label_sensitivity':            {'ko': '   민감도:',              'en': '   Sensitivity:'},
    'label_sensitivity_hint':       {'ko': '← 엄격  관대 →',         'en': '← strict  loose →'},
    'label_sponsor':                {'ko': '☕후원하기 Buy me a coffee', 'en': '☕ Buy me a coffee'},
    'btn_scan_start':               {'ko': '스캔 시작',               'en': 'Start Scan'},
    'btn_pause':                    {'ko': '일시중지',                'en': 'Pause'},
    'btn_resume':                   {'ko': '재개',                   'en': 'Resume'},
    'btn_cancel_scan':              {'ko': '취소',                   'en': 'Cancel'},
    'dlg_title_select_scan_folder': {'ko': '스캔할 폴더를 선택하세요', 'en': 'Select a folder to scan'},
    'dlg_title_no_folder':          {'ko': '폴더 미선택',             'en': 'No Folder Selected'},
    'dlg_msg_select_folder_first':  {'ko': '스캔할 폴더를 먼저 선택해주세요.', 'en': 'Please select a folder to scan.'},
    'status_scan_preparing':        {'ko': '스캔 준비 중...',          'en': 'Preparing scan...'},
    'status_paused':                {'ko': '일시중지됨',               'en': 'Paused'},
    'status_processing_results':    {'ko': '결과 정리 중...',          'en': 'Processing results...'},

    # ── 진행 상황 (동적) ─────────────────────────────────────────────
    'status_progress_count':        {'ko': '{current} / {total}개  ({pct:.1f}%)',
                                     'en': '{current} / {total}  ({pct:.1f}%)'},
    'status_eta_hours_mins':        {'ko': '남은 시간: 약 {h}시간 {m}분',   'en': 'ETA: ~{h}h {m}m'},
    'status_eta_mins_secs':         {'ko': '남은 시간: 약 {m}분 {s}초',     'en': 'ETA: ~{m}m {s}s'},
    'status_eta_secs':              {'ko': '남은 시간: 약 {s}초',           'en': 'ETA: ~{s}s'},

    # ── 결과 패널 ────────────────────────────────────────────────────
    'status_no_results':            {'ko': '스캔 결과가 여기에 표시됩니다.', 'en': 'Scan results will appear here.'},
    'cb_show_thumbnail':            {'ko': '썸네일 표시',              'en': 'Show thumbnails'},
    'tab_exact_duplicates':         {'ko': '완전 중복',                'en': 'Exact Duplicates'},
    'tab_similar_duplicates':       {'ko': '유사 중복',                'en': 'Similar'},
    'tab_exact_label':              {'ko': '완전 중복  ',              'en': 'Exact  '},
    'tab_similar_label':            {'ko': '유사 중복  ',              'en': 'Similar  '},
    'label_group_list':             {'ko': '그룹 목록',                'en': 'Groups'},
    'btn_keep_original':            {'ko': '원본 유지 (나머지 선택)',    'en': 'Keep original (select rest)'},
    'btn_select_all':               {'ko': '전부 선택',                'en': 'Select All'},
    'btn_delete_selected':          {'ko': '선택 항목 삭제',            'en': 'Delete Selected'},
    'btn_dismiss_group':            {'ko': '중복 아님',                'en': 'Not a duplicate'},
    'dlg_title_deleting':           {'ko': '삭제 중...',               'en': 'Deleting...'},
    'dlg_title_processing':         {'ko': '처리 중...',               'en': 'Processing...'},
    'dlg_title_no_selection':       {'ko': '선택 없음',                'en': 'No Selection'},
    'dlg_msg_select_group_first':   {'ko': '먼저 그룹을 선택해주세요.', 'en': 'Please select a group first.'},
    'dlg_msg_select_files_first':   {'ko': '삭제할 파일을 먼저 선택해주세요.', 'en': 'Please select files to delete.'},
    'dlg_title_delete_confirm':     {'ko': '삭제 확인',                'en': 'Confirm Delete'},
    'dlg_title_bulk_delete_confirm':{'ko': '일괄 삭제 확인',            'en': 'Confirm Bulk Delete'},
    'dlg_title_deletion_error':     {'ko': '삭제 오류',                'en': 'Delete Error'},
    'status_analyzing_originals':   {'ko': '원본 파일 분석 중...',      'en': 'Analyzing originals...'},
    'status_deletion_started':      {'ko': '삭제 시작...',             'en': 'Deleting...'},

    # ── 결과 패널 (동적) ─────────────────────────────────────────────
    'msg_file_list_more':           {'ko': '  ... 외 {n}개',           'en': '  ... and {n} more'},
    'dlg_msg_moving_files':         {'ko': '총 {total}개 파일을 휴지통으로 이동 중...',
                                     'en': 'Moving {total} files to Trash...'},
    'status_too_many_cards':        {'ko': '{n_groups}개 그룹  /  {total_files}개 파일 선택됨\n(파일이 너무 많아 미리보기를 표시하지 않습니다)',
                                     'en': '{n_groups} groups  /  {total_files} files selected\n(Too many files to preview)'},
    'btn_bulk_keep_delete':         {'ko': '원본 유지 후 나머지 삭제  ({n}개 삭제 예정)',
                                     'en': 'Keep originals & delete rest  ({n} to delete)'},
    'btn_bulk_dismiss':             {'ko': '중복 아님  ({n}개 그룹 목록에서 제거)',
                                     'en': 'Not duplicates  (remove {n} groups)'},
    'dlg_msg_bulk_delete_confirm':  {'ko': '{n}개 그룹에서 원본을 제외한 나머지 파일을\n휴지통으로 이동하시겠습니까?\n\n(휴지통에서 복구할 수 있습니다)',
                                     'en': 'Move non-original files from {n} groups to Trash?\n\n(Recoverable from Trash)'},
    'dlg_msg_processing_groups':    {'ko': '{n}개 그룹 처리 중...',     'en': 'Processing {n} groups...'},
    'dlg_msg_delete_confirm':       {'ko': '아래 {n}개 파일을 휴지통으로 이동하시겠습니까?\n\n{names}\n\n(휴지통에서 복구할 수 있습니다)',
                                     'en': 'Move {n} files to Trash?\n\n{names}\n\n(Recoverable from Trash)'},
    'label_group_separator':        {'ko': '── 그룹 {idx}  ({n}개) ──', 'en': '── Group {idx}  ({n} files) ──'},
    'label_group_info_savings':     {'ko': '그룹 {idx}  ({n}개, -{savings})', 'en': 'Group {idx}  ({n} files, -{savings})'},
    'label_group_info':             {'ko': '그룹 {idx}  ({n}개)',       'en': 'Group {idx}  ({n} files)'},
    'status_summary':               {'ko': '완전 중복 {e}그룹 · 유사 중복 {s}그룹 · 절약 가능 {savings}',
                                     'en': '{e} exact · {s} similar · {savings} saveable'},
    'status_summary_total':         {'ko': '전체 {total}개 스캔 완료 — {msg}',
                                     'en': 'Scanned {total} files — {msg}'},

    # ── 미리보기 카드 ────────────────────────────────────────────────
    'btn_play':                     {'ko': '▶  재생',                  'en': '▶  Play'},
    'cb_select':                    {'ko': '선택',                     'en': 'Select'},
    'label_no_preview':             {'ko': '미리보기\n불가',             'en': 'No\nPreview'},

    # ── 메인 윈도우 ──────────────────────────────────────────────────
    'window_title':                 {'ko': 'Duplicate Finder',         'en': 'Duplicate Finder'},
    'status_scan_complete':         {'ko': '스캔 완료!',               'en': 'Scan complete!'},
    'status_scan_cancelled':        {'ko': '스캔이 취소되었습니다.',    'en': 'Scan cancelled.'},
    'status_cancelled':             {'ko': '취소됨',                   'en': 'Cancelled'},
    'dlg_title_scan_error':         {'ko': '스캔 오류',                'en': 'Scan Error'},
    'btn_lang_toggle':              {'ko': 'English',                  'en': '한국어'},
}


def set_language(lang: str) -> None:
    """언어 설정 ('ko' 또는 'en')."""
    global _LANG
    if lang in ('ko', 'en'):
        _LANG = lang


def get_language() -> str:
    return _LANG


def t(key: str, **kwargs) -> str:
    """키에 해당하는 현재 언어 문자열 반환. kwargs가 있으면 .format() 적용."""
    text = _STRINGS.get(key, {}).get(_LANG) or _STRINGS.get(key, {}).get('ko') or key
    return text.format(**kwargs) if kwargs else text
