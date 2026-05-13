"""
索引构建器 - 扫描音乐文件夹，构建/更新索引
"""
from pathlib import Path
import json
import hashlib
from datetime import datetime
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4
from mutagen.wave import WAVE
from mutagen import File as MutagenFile
import logging

from music_player.config import MUSIC_DIR, INDEX_FILE, AUDIO_EXTENSIONS, VIDEO_EXTENSIONS

logger = logging.getLogger(__name__)

# 格式到 mutagen 类的映射
FORMAT_MAP = {
    ".mp3": "MP3",
    ".flac": "FLAC",
    ".wav": "WAVE",
    ".m4a": "MP4",
    ".ogg": "OggVorbis",
    ".aac": "MP4",
}

# 通用标签映射 (mutagen tags -> standard names)
TAG_MAP = {
    "title": ["TIT2", "title", "TITLE", "ttitle"],
    "artist": ["TPE1", "artist", "ARTIST", "TPE1"],
    "album": ["TALB", "album", "ALBUM"],
    "length": None,  # special handling
}


def get_file_hash(file_path: str) -> str:
    """计算文件 MD5 用于追踪变更"""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_audio_metadata(file_path: Path) -> dict:
    """提取音频元数据"""
    meta = {
        "title": file_path.stem,
        "artist": "未知歌手",
        "album": "未知专辑",
        "duration": 0.0,
        "size": file_path.stat().st_size,
    }

    try:
        audio = MutagenFile(str(file_path))
        if audio is None:
            return meta

        # 时长
        if hasattr(audio, "info") and hasattr(audio.info, "length"):
            meta["duration"] = round(audio.info.length, 2)

        # 标题
        title = _get_tag(audio, "title")
        if title:
            meta["title"] = title[0] if isinstance(title, list) else title

        # 艺术家
        artist = _get_tag(audio, "artist")
        if artist:
            meta["artist"] = artist[0] if isinstance(artist, list) else artist

        # 专辑
        album = _get_tag(audio, "album")
        if album:
            meta["album"] = album[0] if isinstance(album, list) else album

    except Exception as e:
        logger.warning(f"Failed to read metadata for {file_path}: {e}")

    return meta


def _get_tag(audio, tag_name: str):
    """从音频文件中获取标签"""
    for tag_key in TAG_MAP.get(tag_name, []):
        try:
            value = audio.get(tag_key)
            if value:
                # 确保返回字符串
                if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                    return [str(v) for v in value]
                return str(value)
        except (AttributeError, KeyError):
            continue
    return None


def build_index(target_dir: Path = None, force_rebuild: bool = False) -> list:
    """
    构建或更新索引
    :param target_dir: 要扫描的目录，默认为 MUSIC_DIR
    :param force_rebuild: 是否强制重新构建
    :return: 索引条目列表
    """
    if target_dir is None:
        target_dir = MUSIC_DIR

    if not target_dir.exists():
        logger.error(f"Music directory not found: {target_dir}")
        return []

    # 读取现有索引
    old_index = {}
    if INDEX_FILE.exists() and not force_rebuild:
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            old_index = {item["path"]: item for item in data.get("entries", [])}
        except (json.JSONDecodeError, KeyError):
            old_index = {}

    new_entries = []
    scanned_files = set()

    # 递归扫描
    for ext in (AUDIO_EXTENSIONS | VIDEO_EXTENSIONS):
        for file_path in target_dir.rglob(f"*{ext}"):
            if not file_path.is_file():
                continue
            abs_path = str(file_path.resolve())
            scanned_files.add(abs_path)

            # 检查是否需要更新
            if abs_path in old_index:
                old_hash = old_index[abs_path].get("hash", "")
                new_hash = get_file_hash(abs_path)
                if old_hash == new_hash:
                    # 文件未变化，直接使用
                    entry = old_index[abs_path]
                    entry["updated_at"] = datetime.now().isoformat()
                    new_entries.append(entry)
                    continue

            # 新文件或已修改
            logger.info(f"Indexing: {file_path.name}")
            meta = get_audio_metadata(file_path)
            entry = {
                "path": abs_path,
                "name": file_path.name,
                "title": meta["title"],
                "artist": meta["artist"],
                "album": meta["album"],
                "duration": meta["duration"],
                "size": meta["size"],
                "extension": file_path.suffix.lower(),
                "hash": get_file_hash(abs_path),
                "added_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            new_entries.append(entry)

    # 移除已删除文件的条目
    for entry in new_entries:
        if not Path(entry["path"]).exists():
            logger.warning(f"Indexed file missing: {entry['path']}")

    new_entries = [e for e in new_entries if Path(e["path"]).exists()]

    # 保存索引
    index_data = {
        "version": "1.0",
        "built_at": datetime.now().isoformat(),
        "music_dir": str(target_dir.resolve()),
        "total_files": len(new_entries),
        "entries": new_entries,
    }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Index built: {len(new_entries)} files indexed")
    return new_entries


def load_index() -> list:
    """加载索引，如果不存在则自动构建"""
    if not INDEX_FILE.exists():
        logger.info("索引文件不存在，自动构建索引...")
        return build_index()
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("entries", [])
    except (json.JSONDecodeError, KeyError):
        logger.warning("索引文件损坏，重新构建...")
        return build_index()


def get_index_stats() -> dict:
    """获取索引统计信息"""
    if not INDEX_FILE.exists():
        return {"total": 0, "total_duration": 0, "total_duration_str": "0h 0m", "message": "索引未构建"}

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    total_duration = sum(e.get("duration", 0) for e in entries)
    artists = set(e.get("artist", "未知") for e in entries)
    albums = set(e.get("album", "未知") for e in entries)

    return {
        "total": len(entries),
        "total_duration": round(total_duration, 2),
        "total_duration_str": f"{int(total_duration // 3600)}h {int((total_duration % 3600) // 60)}m",
        "artists": len(artists),
        "albums": len(albums),
        "built_at": data.get("built_at", "unknown"),
    }
