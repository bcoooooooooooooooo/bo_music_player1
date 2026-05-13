"""
歌曲列表 - 支持拖拽排序、右键菜单
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QMenu, QAbstractItemView,
    QStyledItemDelegate, QInputDialog
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QModelIndex
from PyQt6.QtGui import QFont, QColor

from music_player.config import THEME, DATA_DIR
from music_player.playlist_manager import playlist_manager


class SongTableWidget(QTableWidget):
    """歌曲表格"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_playlist = None
        self._index_map = {}  # path -> entry data

        # 列: 播放, 序号, 歌曲名, 歌手, 专辑, 时长
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(["▶", "#", "歌曲", "歌手", "专辑", "时长"])

        header = self.horizontalHeader()
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {THEME['bg_tertiary']};
                color: {THEME['text_dim']};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {THEME['border']};
            }}
        """)
        header.setStretchLastSection(True)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 44)
        self.setColumnWidth(1, 40)
        self.setColumnWidth(3, 150)
        self.setColumnWidth(4, 150)
        self.setColumnWidth(5, 80)

        # 样式
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                gridline-color: transparent;
                outline: none;
                selection-background-color: {THEME['bg_hover']};
            }}
            QTableWidget::item {{
                color: {THEME['text_secondary']};
                padding: 6px 8px;
                border-bottom: 1px solid rgba(255,255,255,0.03);
            }}
            QTableWidget::item:selected {{
                background-color: {THEME['bg_hover']};
                color: {THEME['text_primary']};
            }}
            QTableWidget::item:hover:!selected {{
                background-color: rgba(255,255,255,0.03);
            }}
        """)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setCornerButtonEnabled(False)

        # 禁用编辑 - 双击不进入编辑模式
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 启用拖拽接收歌词
        self.setAcceptDrops(True)

        # 右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # 双击播放
        self.doubleClicked.connect(self._on_double_click)

    def set_index_map(self, index_map: dict):
        """设置索引映射 (path -> entry)"""
        self._index_map = index_map

    def load_playlist(self, playlist_id: str):
        """加载歌单内容"""
        self._current_playlist = playlist_id
        self.clearContents()
        self.setRowCount(0)

        pl = playlist_manager.get(playlist_id)
        if not pl:
            return

        songs = pl.get("songs", [])
        if not songs and playlist_id == "all_music":
            # 全部音乐: 从索引加载
            from music_player.indexer import load_index
            songs_data = load_index()
            self.setRowCount(len(songs_data))
            for i, entry in enumerate(songs_data):
                self._add_row(i, entry.get("path", ""), entry.get("title", ""),
                              entry.get("artist", "未知"), entry.get("album", "未知"),
                              entry.get("duration", 0))
            return

        self.setRowCount(len(songs))
        for i, song in enumerate(songs):
            path = song["path"]
            entry = self._index_map.get(path, {})
            self._add_row(i, path,
                          entry.get("title", path.split("/")[-1]),
                          entry.get("artist", "未知歌手"),
                          entry.get("album", "未知专辑"),
                          entry.get("duration", 0))

    def _add_row(self, row: int, path: str, title: str, artist: str, album: str, duration: float):
        from PyQt6.QtWidgets import QPushButton

        # 播放按钮
        btn = QPushButton("▶")
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(title)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 12px;
                color: {THEME['text_dim']};
            }}
            QPushButton:hover {{
                color: {THEME['accent']};
            }}
        """)
        btn.clicked.connect(lambda checked, p=path: self.song_play_clicked.emit(p))
        self.setCellWidget(row, 0, btn)

        # 序号
        idx_item = QTableWidgetItem(str(row + 1))
        idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        idx_item.setForeground(QColor(THEME["text_dim"]))
        idx_item.setFlags(idx_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, 1, idx_item)

        # 歌曲名
        name_item = QTableWidgetItem(title)
        name_item.setData(Qt.ItemDataRole.UserRole, path)
        self.setItem(row, 2, name_item)

        # 歌手
        artist_item = QTableWidgetItem(artist)
        self.setItem(row, 3, artist_item)

        # 专辑
        album_item = QTableWidgetItem(album)
        self.setItem(row, 4, album_item)

        # 时长
        dur_str = self._format_duration(duration)
        dur_item = QTableWidgetItem(dur_str)
        dur_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        dur_item.setFlags(dur_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, 5, dur_item)

    def _format_duration(self, seconds: float) -> str:
        if not seconds:
            return "--:--"
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"

    def _on_double_click(self, index):
        row = index.row()
        path_item = self.item(row, 2)
        if path_item:
            path = path_item.data(Qt.ItemDataRole.UserRole)
            if path:
                self.song_double_clicked.emit(path)

    def _show_context_menu(self, pos):
        row = self.rowAt(pos.y())
        if row < 0:
            return

        path_item = self.item(row, 2)
        if not path_item:
            return
        path = path_item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME['bg_secondary']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border']};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 32px 8px 12px;
            }}
            QMenu::item:selected {{
                background-color: {THEME['bg_hover']};
            }}
            QMenu::separator {{
                background-color: {THEME['border']};
                height: 1px;
            }}
        """)

        # 播放
        act_play = QAction("▶️  播放", menu)
        act_play.triggered.connect(lambda: self.song_double_clicked.emit(path))
        menu.addAction(act_play)

        menu.addSeparator()

        # 移到上/下
        act_move_up = QAction("⬆️  向上移动", menu)
        act_move_up.triggered.connect(lambda: self._move_song(row, -1))
        menu.addAction(act_move_up)

        act_move_down = QAction("⬇️  向下移动", menu)
        act_move_down.triggered.connect(lambda: self._move_song(row, 1))
        menu.addAction(act_move_down)

        menu.addSeparator()

        # 加入歌单
        act_add = QAction("📋  加入歌单...", menu)
        act_add.triggered.connect(lambda: self._add_to_playlist(path))
        menu.addAction(act_add)

        # 从当前歌单移除
        if self._current_playlist and self._current_playlist != "all_music":
            act_remove = QAction("❌  从歌单移除", menu)
            act_remove.triggered.connect(lambda: self._remove_from_playlist(path, row))
            menu.addAction(act_remove)

        # 收藏
        act_fav = QAction("❤️  加入收藏", menu)
        act_fav.triggered.connect(lambda: self._toggle_favorite(path))
        menu.addAction(act_fav)

        menu.exec(self.mapToGlobal(pos))

    def _move_song(self, row: int, direction: int):
        """移动歌曲位置"""
        if not self._current_playlist or self._current_playlist == "all_music":
            return
        new_row = row + direction
        if new_row < 0 or new_row >= self.rowCount():
            return
        playlist_manager.reorder_song(self._current_playlist, row, new_row)
        self.load_playlist(self._current_playlist)

    def _add_to_playlist(self, path: str):
        """加入歌单"""
        playlists = playlist_manager.get_all()
        user_playlists = [p for p in playlists if p["id"] not in ("all_music", "recent", "history")]
        if not user_playlists:
            return

        names = [f"{p.get('icon', '🎶')} {p['name']}" for p in user_playlists]
        chosen, ok = QInputDialog.getItem(self, "加入歌单", "选择歌单:", names, 0, False)
        if ok and chosen:
            # 找到对应的 playlist id
            idx = names.index(chosen)
            pid = user_playlists[idx]["id"]
            playlist_manager.add_song(pid, path)

    def _remove_from_playlist(self, path: str, row: int):
        """从歌单移除"""
        if not self._current_playlist:
            return
        playlist_manager.remove_song(self._current_playlist, path)
        self.load_playlist(self._current_playlist)

    def _toggle_favorite(self, path: str):
        """切换收藏"""
        fav_paths = playlist_manager.get_songs("favorites")
        if path in fav_paths:
            playlist_manager.remove_song("favorites", path)
        else:
            playlist_manager.add_song("favorites", path)

    # 信号
    song_double_clicked = pyqtSignal(str)
    song_play_clicked = pyqtSignal(str)
