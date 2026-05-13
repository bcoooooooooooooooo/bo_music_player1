"""
主窗口 - 仿网易云布局
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QFont, QKeySequence

from music_player.config import THEME, MUSIC_DIR, DATA_DIR
from music_player.player import PlayerEngine, PlayMode
from music_player.indexer import build_index, load_index, get_index_stats
from music_player.playlist_manager import playlist_manager
from music_player.settings import load_settings, get_theme, get_font_sizes
from music_player.ui.sidebar import Sidebar
from music_player.ui.song_table import SongTableWidget
from music_player.ui.now_playing import NowPlayingWidget
from music_player.ui.player_bar import PlayerControlBar
from music_player.ui.settings_dialog import SettingsDialog

import logging
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._index_map = {}  # path -> entry
        self._current_playlist = None

        # 创建播放器引擎
        self.player_engine = PlayerEngine()

        self._init_ui()
        self._connect_signals()
        self._load_index()

    def _init_ui(self):
        self.setWindowTitle("🎵 音乐播放器")
        self.setMinimumSize(900, 600)
        self.resize(1280, 800)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {THEME['bg_primary']};
            }}
        """)

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== 左侧边栏 =====
        self._SIDEBAR_EXPANDED = 220
        self._SIDEBAR_COLLAPSED = 48

        self.sidebar_container = QWidget()
        self.sidebar_container.setFixedWidth(self._SIDEBAR_EXPANDED)  # 固定宽度，不伸缩
        self.sidebar_container.setStyleSheet(f"background-color: {THEME['bg_secondary']}; border-right: 1px solid {THEME['border']};")
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # 侧边栏折叠按钮 + 设置按钮（在顶部）
        sidebar_toggle_layout = QHBoxLayout()
        sidebar_toggle_layout.setContentsMargins(4, 4, 4, 0)

        # 设置按钮
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setFixedSize(24, 24)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['bg_tertiary']};
                border: none;
                color: {THEME['text_dim']};
                font-size: 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ color: {THEME['text_primary']}; background-color: {THEME['bg_hover']}; }}
        """)
        self.btn_settings.setToolTip("设置")
        sidebar_toggle_layout.addWidget(self.btn_settings)

        sidebar_toggle_layout.addStretch()
        self.btn_toggle_sidebar = QPushButton("◀")
        self.btn_toggle_sidebar.setFixedSize(24, 24)
        self.btn_toggle_sidebar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_sidebar.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['bg_tertiary']};
                border: none;
                color: {THEME['text_dim']};
                font-size: 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ color: {THEME['text_primary']}; background-color: {THEME['bg_hover']}; }}
        """)
        self.btn_toggle_sidebar.setToolTip("折叠侧边栏")
        sidebar_toggle_layout.addWidget(self.btn_toggle_sidebar)
        sidebar_layout.addLayout(sidebar_toggle_layout)

        self.sidebar = Sidebar()
        self.sidebar.setMinimumHeight(400)
        sidebar_layout.addWidget(self.sidebar, 1)

        self._sidebar_collapsed = False
        main_layout.addWidget(self.sidebar_container)

        # ===== 右侧主区域 =====
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 顶部区域: 封面/歌词 + 歌单信息
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        content_splitter.setHandleWidth(4)

        # 上方: 当前播放 / 歌词
        self.now_playing = NowPlayingWidget()
        self.now_playing.setMinimumHeight(350)
        content_splitter.addWidget(self.now_playing)

        # ===== 下方: 歌曲列表（可折叠） =====
        self.song_list_container = QWidget()
        self.song_list_layout = QVBoxLayout(self.song_list_container)
        self.song_list_layout.setContentsMargins(12, 8, 12, 8)
        self.song_list_layout.setSpacing(8)

        # 歌单标题栏
        header_layout = QHBoxLayout()
        self.playlist_title = QLabel("全部音乐")
        self.playlist_title.setStyleSheet(f"""
            color: {THEME['text_primary']};
            font-size: 18px;
            font-weight: bold;
        """)
        self.playlist_title.setFont(QFont("Microsoft YaHei", 15, QFont.Weight.Bold))
        header_layout.addWidget(self.playlist_title)

        self.playlist_count = QLabel("")
        self.playlist_count.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 12px;")
        self.playlist_count.setFont(QFont("Microsoft YaHei", 10))
        header_layout.addWidget(self.playlist_count)

        header_layout.addStretch()

        # 折叠歌单按钮
        self.btn_toggle_playlist = QPushButton("▼")
        self.btn_toggle_playlist.setFixedSize(28, 24)
        self.btn_toggle_playlist.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_playlist.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['bg_tertiary']};
                border: 1px solid {THEME['border']};
                color: {THEME['text_dim']};
                font-size: 10px;
                border-radius: 4px;
                padding: 0 6px;
            }}
            QPushButton:hover {{ color: {THEME['text_primary']}; background-color: {THEME['bg_hover']}; }}
        """)
        self.btn_toggle_playlist.setToolTip("折叠/展开歌单")
        header_layout.addWidget(self.btn_toggle_playlist)

        # 操作按钮
        self.btn_build_index = QPushButton("🔍 构建索引")
        self.btn_build_index.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_build_index.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['bg_tertiary']};
                color: {THEME['text_secondary']};
                border: 1px solid {THEME['border']};
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {THEME['bg_hover']};
                color: {THEME['text_primary']};
            }}
        """)
        header_layout.addWidget(self.btn_build_index)

        self.btn_add_files = QPushButton("➕ 添加文件")
        self.btn_add_files.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_files.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_light']};
            }}
        """)
        header_layout.addWidget(self.btn_add_files)

        self.song_list_layout.addLayout(header_layout)

        self.song_table = SongTableWidget()
        self.song_list_layout.addWidget(self.song_table)

        content_splitter.addWidget(self.song_list_container)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 1)

        right_layout.addWidget(content_splitter, 1)

        # 底部播放控制栏
        self.player_bar = PlayerControlBar(self.player_engine)
        right_layout.addWidget(self.player_bar)

        main_layout.addWidget(right_widget, 1)

    def _connect_signals(self):
        """连接所有信号"""
        self.sidebar.playlist_selected.connect(self._on_playlist_selected)

        # 歌曲列表 -> 播放
        self.song_table.song_double_clicked.connect(self._on_song_play)
        self.song_table.song_play_clicked.connect(self._on_song_play)

        # 播放器引擎
        self.player_engine.playback_ended.connect(self._on_playback_ended)
        self.player_engine.media_changed.connect(self._on_media_changed)
        self.player_engine.playing_changed.connect(self._on_playing_state_changed)

        # 底部控制栏
        self.player_bar.play_mode_changed.connect(self._on_play_mode_changed)
        self.player_bar.position_update_signal.connect(self._on_position_update)
        self.player_bar.files_loaded.connect(self._on_files_loaded)

        # 按钮
        self.btn_build_index.clicked.connect(self._on_build_index)
        self.btn_add_files.clicked.connect(self._on_add_files)

        # 折叠按钮
        self.btn_toggle_sidebar.clicked.connect(self._toggle_sidebar)
        self.btn_toggle_playlist.clicked.connect(self._toggle_playlist)

        # 设置按钮
        self.btn_settings.clicked.connect(self._open_settings)

        # 创建设置对话框（单例）
        self._settings_dialog = SettingsDialog(self)
        self._settings_dialog.theme_changed.connect(self._apply_theme)
        self._settings_dialog.font_sizes_changed.connect(self._apply_font_sizes)
        self._settings_dialog.background_changed.connect(self._apply_background)

    def _toggle_sidebar(self):
        """折叠/展开侧边栏 - 固定宽度切换"""
        if self._sidebar_collapsed:
            # 展开
            self.sidebar_container.setFixedWidth(self._SIDEBAR_EXPANDED)
            self.sidebar.setVisible(True)
            self.btn_toggle_sidebar.setText("◀")
            self.btn_toggle_sidebar.setToolTip("折叠侧边栏")
            self._sidebar_collapsed = False
        else:
            # 折叠
            self.sidebar_container.setFixedWidth(self._SIDEBAR_COLLAPSED)
            self.sidebar.setVisible(False)
            self.btn_toggle_sidebar.setText("▶")
            self.btn_toggle_sidebar.setToolTip("展开侧边栏")
            self._sidebar_collapsed = True

    def _toggle_playlist(self):
        """折叠/展开歌单区域"""
        table_visible = self.song_table.isVisible()
        if table_visible:
            self.song_table.hide()
            self.btn_toggle_playlist.setText("▶")
            self.btn_toggle_playlist.setToolTip("展开歌单")
        else:
            self.song_table.show()
            self.btn_toggle_playlist.setText("▼")
            self.btn_toggle_playlist.setToolTip("折叠歌单")

    def keyPressEvent(self, event):
        """键盘快捷键"""
        key = event.key()

        # 空格: 播放/暂停
        if key == Qt.Key.Key_Space:
            self.player_engine.toggle_play_pause()
            return

        # 上键: 上一首
        if key == Qt.Key.Key_Up:
            self.player_engine.previous()
            return

        # 下键: 下一首
        if key == Qt.Key.Key_Down:
            self.player_engine.next()
            return

        # 左键: -5秒
        if key == Qt.Key.Key_Left:
            current = self.player_engine.player.position()
            self.player_engine.seek(max(0, current - 5000))
            return

        # 右键: +5秒
        if key == Qt.Key.Key_Right:
            duration = self.player_engine.player.duration()
            current = self.player_engine.player.position()
            self.player_engine.seek(min(duration, current + 5000))
            return

        super().keyPressEvent(event)

    def _load_index(self):
        """加载索引并更新界面"""
        entries = load_index()
        self._index_map = {e["path"]: e for e in entries}

        # 更新"全部音乐"歌单
        if entries:
            playlist_manager.set_songs("all_music", [{"path": e["path"]} for e in entries])

        # 更新统计
        stats = get_index_stats()
        self.playlist_count.setText(f"{stats['total']}首 · {stats['total_duration_str']}")

        # 自动选中第一个歌单
        first = self.sidebar.playlist_list.item(0)
        if first:
            pid = first.data(Qt.ItemDataRole.UserRole)
            self._on_playlist_selected(pid)

    def _on_playlist_selected(self, playlist_id: str):
        """选中歌单"""
        self._current_playlist = playlist_id
        pl = playlist_manager.get(playlist_id)
        if not pl:
            return

        self.playlist_title.setText(f"{pl.get('icon', '🎶')} {pl['name']}")
        song_count = len(pl.get("songs", []))
        self.playlist_count.setText(f"{song_count}首")

        self.song_table.set_index_map(self._index_map)
        self.song_table.load_playlist(playlist_id)

    def _on_song_play(self, path: str):
        """点击播放按钮/双击歌曲播放"""
        if not path:
            return
        entry = self._index_map.get(path, {})
        title = entry.get("title", path.split("/")[-1])
        artist = entry.get("artist", "未知歌手")
        album = entry.get("album", "未知专辑")

        # 始终从当前歌单获取完整播放列表
        playlist_songs = self._get_current_playlist_songs()
        if playlist_songs and path in playlist_songs:
            idx = playlist_songs.index(path)
            self.player_engine.set_playlist(playlist_songs, idx)
        else:
            # 回退: 直接播放
            self.player_engine.play_file(path)

        # 更新 UI
        self.now_playing.set_song(title, artist, album, path)
        self.player_bar.set_current_song_info(title, artist, album)

        # 记录到最近播放和历史
        playlist_manager.add_to_recent(path)
        playlist_manager.add_to_history(path)

    def _get_current_playlist_songs(self) -> list:
        """获取当前歌单的歌曲路径列表"""
        if not self._current_playlist:
            return []
        if self._current_playlist == "all_music":
            return [e["path"] for e in load_index()]
        return playlist_manager.get_songs(self._current_playlist)

    def _on_playback_ended(self):
        """播放结束"""
        pass

    def _on_media_changed(self, path: str):
        """媒体切换"""
        pass

    def _on_playing_state_changed(self, playing: bool):
        """播放状态变化"""
        if playing:
            self.setWindowTitle("🎵 音乐播放器 - 播放中")
        else:
            self.setWindowTitle("🎵 音乐播放器")

    def _on_play_mode_changed(self, mode: str):
        """播放模式变化"""
        pass

    def _on_position_update(self, position_ms: int):
        """进度更新 - 同步歌词"""
        self.now_playing.update_lyrics_position(position_ms)

    def _on_build_index(self):
        """构建索引"""
        self.btn_build_index.setText("⏳ 构建中...")
        self.btn_build_index.setEnabled(False)
        QTimer.singleShot(50, self._do_build_index)

    def _do_build_index(self):
        try:
            build_index(force_rebuild=True)
            self._load_index()
            stats = get_index_stats()
            QMessageBox.information(self, "索引完成",
                                    f"索引构建完成！\n共 {stats['total']} 首歌曲\n总时长: {stats['total_duration_str']}")
        except Exception as e:
            QMessageBox.critical(self, "索引失败", f"构建索引时出错:\n{e}")
        finally:
            self.btn_build_index.setText("🔍 构建索引")
            self.btn_build_index.setEnabled(True)

    def _on_add_files(self):
        """添加文件到当前歌单"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", str(MUSIC_DIR),
            "音频/视频文件 (*.mp3 *.flac *.wav *.m4a *.ogg *.wma *.aac *.mp4 *.mkv)"
        )
        if files and self._current_playlist and self._current_playlist != "all_music":
            for f in files:
                playlist_manager.add_song(self._current_playlist, f)
            self._on_playlist_selected(self._current_playlist)

    def _on_files_loaded(self, files: list):
        """底部栏加载文件"""
        for f in files:
            if f not in self._index_map:
                self._index_map[f] = {"path": f, "title": f.split("/")[-1], "artist": "未知", "album": "未知", "duration": 0}
        if files:
            self._on_song_play(files[0])

    # ===== 设置相关方法 =====

    def _open_settings(self):
        """打开设置对话框"""
        self._settings_dialog.exec()

    def _apply_theme(self, theme: dict):
        """应用主题（需要重启生效完整样式，这里做基本更新）"""
        # 更新全局 THEME
        global THEME
        for key in THEME:
            if key in theme:
                THEME[key] = theme[key]
        # 建议用户重启
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "主题已保存", "主题已保存！部分界面可能需要重启播放器才能完全生效。")

    def _apply_font_sizes(self, font_sizes: dict):
        """应用字号（需要重启完全生效）"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "字号已保存", "字号已保存！重启播放器后完全生效。")

    def _apply_background(self, bg_path: str):
        """应用背景图片"""
        if bg_path:
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-image: url({bg_path});
                    background-repeat: no-repeat;
                    background-position: center;
                }}
            """)
        else:
            theme = get_theme()
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {theme.get('bg_primary', THEME['bg_primary'])};
                }}
            """)
