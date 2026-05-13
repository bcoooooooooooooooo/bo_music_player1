"""
歌单管理 - 创建、删除、修改歌单
"""
from pathlib import Path
import json
import uuid
from datetime import datetime
import logging

from music_player.config import PLAYLISTS_DIR

logger = logging.getLogger(__name__)


class PlaylistManager:
    """歌单管理器"""

    # 内置默认歌单
    BUILT_IN_PLAYLISTS = [
        {"id": "all_music", "name": "全部音乐", "icon": "🎵", "built_in": True},
        {"id": "favorites", "name": "我喜欢的", "icon": "❤️", "built_in": True},
        {"id": "recent", "name": "最近播放", "icon": "🕐", "built_in": True},
        {"id": "history", "name": "播放历史", "icon": "📜", "built_in": True},
    ]

    def __init__(self):
        self._playlists = {}
        self._load_all()

    def _get_playlist_path(self, playlist_id: str) -> Path:
        return PLAYLISTS_DIR / f"{playlist_id}.json"

    def _load_all(self):
        """加载所有歌单"""
        for playlist in self.BUILT_IN_PLAYLISTS:
            pid = playlist["id"]
            path = self._get_playlist_path(pid)
            if path.exists():
                self._playlists[pid] = self._load_one(path)
            else:
                self._playlists[pid] = {
                    "id": pid,
                    "name": playlist["name"],
                    "icon": playlist["icon"],
                    "built_in": True,
                    "songs": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "cover": None,
                }

        # 加载用户创建的歌单
        if PLAYLISTS_DIR.exists():
            for f in PLAYLISTS_DIR.glob("*.json"):
                pid = f.stem
                if pid not in self._playlists:
                    try:
                        self._playlists[pid] = self._load_one(f)
                    except Exception as e:
                        logger.error(f"Failed to load playlist {f}: {e}")

    def _load_one(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, playlist: dict):
        """保存单个歌单"""
        playlist["updated_at"] = datetime.now().isoformat()
        path = self._get_playlist_path(playlist["id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(playlist, f, ensure_ascii=False, indent=2)

    def get_all(self) -> list:
        """获取所有歌单"""
        return list(self._playlists.values())

    def get(self, playlist_id: str) -> dict:
        """获取指定歌单"""
        return self._playlists.get(playlist_id)

    def create(self, name: str, icon: str = "🎶") -> dict:
        """创建新歌单"""
        pid = uuid.uuid4().hex[:8]
        playlist = {
            "id": pid,
            "name": name,
            "icon": icon,
            "built_in": False,
            "songs": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "cover": None,
        }
        self._playlists[pid] = playlist
        self._save(playlist)
        return playlist

    def delete(self, playlist_id: str) -> bool:
        """删除歌单（不能删除内置歌单）"""
        pl = self._playlists.get(playlist_id)
        if not pl or pl.get("built_in"):
            return False
        path = self._get_playlist_path(playlist_id)
        if path.exists():
            path.unlink()
        del self._playlists[playlist_id]
        return True

    def rename(self, playlist_id: str, new_name: str) -> bool:
        """重命名歌单"""
        pl = self._playlists.get(playlist_id)
        if not pl:
            return False
        pl["name"] = new_name
        self._save(pl)
        return True

    def add_song(self, playlist_id: str, song_path: str, index: int = None) -> bool:
        """添加歌曲到歌单"""
        pl = self._playlists.get(playlist_id)
        if not pl:
            return False
        # 检查是否已存在
        for s in pl["songs"]:
            if s["path"] == song_path:
                return False
        song = {
            "path": song_path,
            "added_at": datetime.now().isoformat(),
        }
        if index is not None:
            pl["songs"].insert(index, song)
        else:
            pl["songs"].append(song)
        self._save(pl)
        return True

    def remove_song(self, playlist_id: str, song_path: str) -> bool:
        """从歌单移除歌曲"""
        pl = self._playlists.get(playlist_id)
        if not pl:
            return False
        original_len = len(pl["songs"])
        pl["songs"] = [s for s in pl["songs"] if s["path"] != song_path]
        if len(pl["songs"]) < original_len:
            self._save(pl)
            return True
        return False

    def reorder_song(self, playlist_id: str, from_index: int, to_index: int) -> bool:
        """调整歌曲在歌单中的位置"""
        pl = self._playlists.get(playlist_id)
        if not pl:
            return False
        if from_index < 0 or from_index >= len(pl["songs"]):
            return False
        if to_index < 0 or to_index >= len(pl["songs"]):
            return False
        song = pl["songs"].pop(from_index)
        pl["songs"].insert(to_index, song)
        self._save(pl)
        return True

    def set_songs(self, playlist_id: str, songs: list) -> bool:
        """直接设置歌单歌曲列表"""
        pl = self._playlists.get(playlist_id)
        if not pl:
            return False
        pl["songs"] = songs
        self._save(pl)
        return True

    def get_songs(self, playlist_id: str) -> list:
        """获取歌单中的歌曲路径列表"""
        pl = self._playlists.get(playlist_id)
        if not pl:
            return []
        return [s["path"] for s in pl["songs"]]

    def add_to_recent(self, song_path: str):
        """添加到最近播放"""
        pl = self._playlists.get("recent")
        if not pl:
            return
        # 移除旧的
        pl["songs"] = [s for s in pl["songs"] if s["path"] != song_path]
        # 加到前面
        song = {
            "path": song_path,
            "added_at": datetime.now().isoformat(),
        }
        pl["songs"].insert(0, song)
        # 限制最多 100 首
        if len(pl["songs"]) > 100:
            pl["songs"] = pl["songs"][:100]
        self._save(pl)

    def add_to_history(self, song_path: str):
        """添加到播放历史"""
        pl = self._playlists.get("history")
        if not pl:
            return
        pl["songs"] = [s for s in pl["songs"] if s["path"] != song_path]
        song = {
            "path": song_path,
            "added_at": datetime.now().isoformat(),
        }
        pl["songs"].insert(0, song)
        if len(pl["songs"]) > 200:
            pl["songs"] = pl["songs"][:200]
        self._save(pl)


# 全局单例
playlist_manager = PlaylistManager()
