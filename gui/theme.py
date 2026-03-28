# theme.py — 앱 전체 폰트/색상 설정
# ── 여기만 수정하면 전체 적용 ──────────────────────────
APP_FONT_FAMILY = 'Malgun Gothic'   # apply_language_font()가 런타임에 업데이트
APP_FONT_SIZE   = 9

_FONTS_BY_LANG = {
    'ko': '맑은 고딕',
    'en': 'Segoe UI',
}


def apply_language_font(lang: str, available_families: tuple) -> None:
    """언어에 맞는 폰트를 APP_FONT_FAMILY에 적용. 없으면 TkDefaultFont 사용."""
    global APP_FONT_FAMILY
    want = _FONTS_BY_LANG.get(lang, 'TkDefaultFont')
    APP_FONT_FAMILY = want if want in available_families else 'TkDefaultFont'
