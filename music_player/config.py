"""
配置模块 - 存储路径常量
"""
from pathlib import Path
import sys
import json

# 项目根目录（兼容开发和打包环境）
if getattr(sys, 'frozen', False):
    # 打包后：使用用户家目录作为数据根目录
    BASE_DIR = Path.home() / ".music_player"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# 音乐文件夹（默认为项目目录下的 musics，用户可以自定义）
MUSIC_DIR = BASE_DIR / "musics"
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

# 数据目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 索引文件
INDEX_FILE = DATA_DIR / "index.json"
# 歌单目录
PLAYLISTS_DIR = DATA_DIR / "playlists"
PLAYLISTS_DIR.mkdir(exist_ok=True)

# 支持的音频格式
AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".wav", ".m4a", ".ogg", ".wma", ".aac", ".opus", ".ape"
}

# 支持的视频格式
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".flv", ".wmv", ".mov", ".webm"
}

# 所有支持的格式
SUPPORTED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS

# 歌词格式
LYRICS_EXTENSIONS = {".lrc", ".txt"}

# 网易云经典配色
THEME = {
    "bg_primary": "#1a1a1e",
    "bg_secondary": "#232328",
    "bg_tertiary": "#2a2a30",
    "bg_hover": "#333339",
    "accent": "#c20c0c",          # 网易云红
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
