"""
用户配置管理
"""
from pathlib import Path
import json
import shutil
import logging

from music_player.config import DATA_DIR, BASE_DIR

logger = logging.getLogger(__name__)

SETTINGS_FILE = DATA_DIR / "settings.json"
BACKGROUND_DIR = DATA_DIR / "backgrounds"
BACKGROUND_DIR.mkdir(exist_ok=True)

# 默认主题
DEFAULT_THEME = {
    "bg_primary": "#1a1a1e",
    "bg_secondary": "#232328",
    "bg_tertiary": "#2a2a30",
    "bg_hover": "#333339",
    "accent": "#c20c0c",
    "accent_light": "#e8432d",
    "text_primary": "#e8e8e8",
    "text_secondary": "#a0a0a0",
    "text_dim": "#666666",
    "border": "#3a3a40",
    "progress_bg": "#444444",
    "progress_fill": "#c20c0c",
    "scrollbar_bg": "#333339",
    "scrollbar_handle": "#555555",
}

DEFAULT_FONT_SIZES = {
    "title": 18,
    "subtitle": 14,
    "normal": 12,
    "small": 11,
    "tiny": 9,
}

THEME_COLOR_LABELS = {
    "bg_primary": "主背景色",
    "bg_secondary": "次背景色",
    "bg_tertiary": "三背景色",
    "bg_hover": "悬浮色",
    "accent": "强调色",
    "accent_light": "强调亮色",
    "text_primary": "主文字色",
    "text_secondary": "次文字色",
    "text_dim": "暗淡文字色",
    "border": "边框色",
    "progress_bg": "进度条底色",
    "progress_fill": "进度条填充",
    "scrollbar_bg": "滚动条底色",
    "scrollbar_handle": "滚动条滑块",
}


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
    return get_defaults()


def save_settings(s: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    logger.info("设置已保存")


def get_defaults() -> dict:
    return {
        "theme": dict(DEFAULT_THEME),
        "font_sizes": dict(DEFAULT_FONT_SIZES),
        "background_image": "",
    }


def get_theme() -> dict:
    return load_settings().get("theme", dict(DEFAULT_THEME))


def get_font_sizes() -> dict:
    return load_settings().get("font_sizes", dict(DEFAULT_FONT_SIZES))


def save_background_image(src_path: str) -> str:
    """将用户选择的背景图片复制到 data/backgrounds/，返回保存后的路径"""
    if not src_path or not Path(src_path).exists():
        return ""
    name = Path(src_path).name
    dest = BACKGROUND_DIR / name
    shutil.copy2(src_path, dest)
    return str(dest)
