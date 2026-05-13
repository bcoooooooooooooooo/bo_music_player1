"""
歌词解析器 - 加载和解析 LRC 歌词文件
"""
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


def parse_lrc(lrc_text: str) -> list:
    """
    解析 LRC 歌词文本
    :return: list of (time_in_seconds, text) sorted by time
    """
    lines = []
    pattern = re.compile(r'\[(\d{2}):(\d{2})(?:\.(\d{1,6}))?\](.*)')

    for line in lrc_text.splitlines():
        line = line.strip()
        matches = pattern.findall(line)
        if not matches:
            continue
        text_parts = []
        time_list = []
        for match in matches:
            mins, secs, ms, text = match
            time_sec = int(mins) * 60 + int(secs)
            if ms:
                time_sec += int(ms.ljust(6, '0')) / 1_000_000
            time_list.append(time_sec)
            text_parts.append(text.strip())

        text = text_parts[-1] if text_parts else ""
        if text:
            for t in time_list:
                lines.append((t, text))

    lines.sort(key=lambda x: x[0])
    return lines


def find_lyric_file(audio_path: str) -> str:
    """
    查找对应音频文件的歌词文件
    优先级: 同目录同名.lrc > 同目录同名.txt > 无
    """
    audio = Path(audio_path)
    candidates = [
        audio.with_suffix(".lrc"),
        audio.with_suffix(".txt"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ""


def load_lyrics(audio_path: str) -> list:
    """
    加载歌词
    :return: list of (time, text)
    """
    lrc_path = find_lyric_file(audio_path)
    if not lrc_path:
        return []
    try:
        with open(lrc_path, "r", encoding="utf-8") as f:
            text = f.read()
        return parse_lrc(text)
    except Exception as e:
        logger.warning(f"Failed to load lyrics for {audio_path}: {e}")
        return []


def get_lyric_at_time(lyrics: list, current_time: float) -> str:
    """获取当前时间对应的歌词"""
    if not lyrics:
        return ""
    current_line = ""
    for t, text in lyrics:
        if t <= current_time:
            current_line = text
        else:
            break
    return current_line


def get_lyric_index(lyrics: list, current_time: float) -> int:
    """获取当前时间对应的歌词行索引"""
    if not lyrics:
        return -1
    idx = -1
    for i, (t, text) in enumerate(lyrics):
        if t <= current_time:
            idx = i
        else:
            break
    return idx
