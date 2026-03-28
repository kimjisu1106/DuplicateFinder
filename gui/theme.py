# theme.py — 앱 전체 폰트/색상 설정
# ── 여기만 수정하면 전체 적용 ──────────────────────────
APP_FONT_FAMILY = 'Malgun Gothic'   # apply_language_font()가 런타임에 업데이트
APP_FONT_SIZE   = 9

# 같은 폰트의 한/영 이름을 순서대로 시도 (시스템 로케일에 따라 다를 수 있음)
_FONTS_BY_LANG = {
    'ko': ('맑은 고딕', 'Malgun Gothic'),
    'en': ('Segoe UI',),
}


def apply_language_font(lang: str, available_families: tuple) -> None:
    """언어에 맞는 폰트를 APP_FONT_FAMILY에 적용. 없으면 TkDefaultFont 사용."""
    global APP_FONT_FAMILY
    for want in _FONTS_BY_LANG.get(lang, ()):
        if want in available_families:
            APP_FONT_FAMILY = want
            return
    APP_FONT_FAMILY = 'TkDefaultFont'
