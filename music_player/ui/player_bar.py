"""
底部播放控制栏 - 进度条 + 播放控制 + 音量
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QMouseEvent, QCursor

from music_player.config import THEME
from music_player.player import PlayerEngine, PlayMode


class VolumeSlider(QSlider):
    """音量滑块 - 加大尺寸，支持点击"""
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setFixedHeight(28)
        self.setFixedWidth(160)
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {THEME['progress_bg']};
                height: 6px;
                border-radius: 3px;
                margin: 0 12px;
            }}
            QSlider::handle:horizontal {{
                background: {THEME['text_primary']};
                width: 20px;
                height: 20px;
                margin: -7px 0;
                border-radius: 10px;
            }}
            QSlider::sub-page:horizontal {{
                background: {THEME['accent']};
                border-radius: 3px;
            }}
        """)

    def mousePressEvent(self, event: QMouseEvent):
        """点击轨道直接跳转"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._jump_to(event)
        super().mousePressEvent(event)

    def _jump_to(self, event):
        groove_w = self.width() - 24  # subtract margins
        ratio = max(0.0, min(1.0, (event.position().x() - 12) / groove_w))
        value = int(ratio * 100)
        self.setValue(value)


class ProgressBar(QWidget):
    """进度条 - 完全自定义绘制，支持点击和拖动 seek"""

    sliderMoved = pyqtSignal(int)
    sliderReleased = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 1000
        self._value = 0
        self._is_dragging = False
        self.setMouseTracking(True)
        self.setFixedHeight(30)
        self.setMinimumWidth(200)

    def minimum(self) -> int:
        return self._minimum

    def maximum(self) -> int:
        return self._maximum

    def value(self) -> int:
        return self._value

    def setMinimum(self, min_val: int):
        self._minimum = min_val
        self.update()

    def setMaximum(self, max_val: int):
        self._maximum = max(max_val, 1)
        self.update()

    def setValue(self, val: int):
        self._value = max(self._minimum, min(val, self._maximum))
        self.update()

    def _get_ratio(self, x: float) -> float:
        margin = 8
        groove_w = self.width() - margin * 2
        if groove_w <= 0:
            return 0.0
        return max(0.0, min(1.0, (x - margin) / groove_w))

    def _ratio_to_value(self, ratio: float) -> int:
        return int(ratio * (self._maximum - self._minimum)) + self._minimum

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            ratio = self._get_ratio(event.position().x())
            self._value = self._ratio_to_value(ratio)
            self.sliderMoved.emit(self._value)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging:
            ratio = self._get_ratio(event.position().x())
            self._value = self._ratio_to_value(ratio)
            self.sliderMoved.emit(self._value)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_dragging:
            self._is_dragging = False
            self.sliderReleased.emit(self._value)

    @property
    def is_scrubbing(self):
        return self._is_dragging

    def blockSignals(self, blocked: bool):
        # 我们不需要 block，直接覆盖 setValue 逻辑
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 8
        groove_w = self.width() - margin * 2
        groove_h = 4
        groove_y = (self.height() - groove_h) // 2

        # 背景轨道
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(THEME["progress_bg"]))
        painter.drawRoundedRect(margin, groove_y, groove_w, groove_h, 2, 2)

        # 已播放进度
        ratio = (self._value - self._minimum) / max(self._maximum - self._minimum, 1)
        filled_w = int(groove_w * ratio)
        if filled_w > 0:
            painter.setBrush(QColor(THEME["accent"]))
            painter.drawRoundedRect(margin, groove_y, filled_w, groove_h, 2, 2)

        # 拖动圆点
        handle_x = margin + int(groove_w * ratio)
        handle_y = self.height() // 2
        handle_r = 7
        painter.setBrush(QColor(THEME["accent"]))
        painter.drawEllipse(int(handle_x) - handle_r, int(handle_y) - handle_r,
                            handle_r * 2, handle_r * 2)

        painter.end()


class PlayerControlBar(QWidget):
    """底部播放控制栏"""

    def __init__(self, player: PlayerEngine, parent=None):
        super().__init__(parent)
        self._player = player
        self._play_mode = PlayMode.LOOP
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)
        self.setMinimumHeight(90)
        self.setMaximumHeight(110)
        self.setStyleSheet(f"background-color: {THEME['bg_secondary']}; border-top: 1px solid {THEME['border']};")

        # --- 左侧: 当前歌曲信息 ---
        left_layout = QHBoxLayout()
        left_layout.setSpacing(10)

        self.current_song_icon = QLabel("🎵")
        self.current_song_icon.setStyleSheet("font-size: 24px;")
        left_layout.addWidget(self.current_song_icon)

        song_info_layout = QVBoxLayout()
        self.current_title = QLabel("未播放")
        self.current_title.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 13px;")
        self.current_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Medium))
        song_info_layout.addWidget(self.current_title)

        self.current_artist = QLabel("")
        self.current_artist.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 11px;")
        self.current_artist.setFont(QFont("Microsoft YaHei", 9))
        song_info_layout.addWidget(self.current_artist)
        left_layout.addLayout(song_info_layout, 1)

        # 喜爱按钮
        self.btn_favorite = QPushButton("🤍")
        self.btn_favorite.setFixedSize(32, 32)
        self.btn_favorite.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_favorite.setStyleSheet("background: transparent; border: none; font-size: 18px;")
        left_layout.addWidget(self.btn_favorite)

        layout.addLayout(left_layout)

        # --- 中间: 播放控制 ---
        center_layout = QVBoxLayout()
        center_layout.setSpacing(6)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)

        # 播放模式
        self.btn_mode = QPushButton("🔁")
        self.btn_mode.setFixedSize(36, 36)
        self.btn_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; font-size: 16px;
                color: {THEME['text_secondary']};
            }}
            QPushButton:hover {{ color: {THEME['text_primary']}; }}
        """)
        self.btn_mode.setToolTip("列表循环")
        self.btn_mode.clicked.connect(self._on_toggle_play_mode)
        controls_layout.addWidget(self.btn_mode)

        # 上一首
        self.btn_prev = QPushButton("⏮")
        self.btn_prev.setFixedSize(36, 36)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; font-size: 18px;
                color: {THEME['text_secondary']};
            }}
            QPushButton:hover {{ color: {THEME['text_primary']}; }}
        """)
        self.btn_prev.clicked.connect(self._on_prev)
        controls_layout.addWidget(self.btn_prev)

        # 播放/暂停
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(48, 48)
        self.btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['bg_tertiary']};
                border: none; border-radius: 24px;
                font-size: 20px; color: {THEME['text_primary']};
            }}
            QPushButton:hover {{ background-color: {THEME['bg_hover']}; }}
        """)
        self.btn_play.clicked.connect(self._on_toggle_play_pause)
        controls_layout.addWidget(self.btn_play)

        # 下一首
        self.btn_next = QPushButton("⏭")
        self.btn_next.setFixedSize(36, 36)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; font-size: 18px;
                color: {THEME['text_secondary']};
            }}
            QPushButton:hover {{ color: {THEME['text_primary']}; }}
        """)
        self.btn_next.clicked.connect(self._on_next)
        controls_layout.addWidget(self.btn_next)

        # 加载本地文件
        self.btn_load = QPushButton("📂")
        self.btn_load.setFixedSize(32, 32)
        self.btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load.setToolTip("加载本地文件")
        self.btn_load.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; font-size: 14px;
                color: {THEME['text_dim']};
            }}
            QPushButton:hover {{ color: {THEME['text_primary']}; }}
        """)
        self.btn_load.clicked.connect(self._on_load_file)
        controls_layout.addWidget(self.btn_load)

        center_layout.addLayout(controls_layout)

        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)

        self.time_current = QLabel("00:00")
        self.time_current.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 11px;")
        self.time_current.setFont(QFont("Consolas", 10))
        self.time_current.setFixedWidth(50)
        progress_layout.addWidget(self.time_current)

        self.progress_bar = ProgressBar()
        progress_layout.addWidget(self.progress_bar, 1)

        self.time_total = QLabel("00:00")
        self.time_total.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 11px;")
        self.time_total.setFont(QFont("Consolas", 10))
        self.time_total.setFixedWidth(50)
        progress_layout.addWidget(self.time_total)

        center_layout.addLayout(progress_layout)
        layout.addLayout(center_layout, 3)

        # --- 右侧: 音量 ---
        right_layout = QHBoxLayout()
        right_layout.setSpacing(8)

        self.volume_icon = QLabel("🔊")
        self.volume_icon.setStyleSheet("font-size: 16px;")
        self.volume_icon.setFixedSize(30, 30)
        self.volume_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.volume_icon)

        self.volume_slider = VolumeSlider()
        self.volume_slider.setValue(70)
        right_layout.addWidget(self.volume_slider)

        self.volume_text = QLabel("70%")
        self.volume_text.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 11px;")
        self.volume_text.setFont(QFont("Consolas", 9))
        self.volume_text.setFixedWidth(36)
        right_layout.addWidget(self.volume_text)

        layout.addLayout(right_layout)

    def _connect_signals(self):
        """连接播放器信号"""
        self._player.playing_changed.connect(self._on_playing_changed)
        self._player.current_position_changed.connect(self._on_position_changed)
        self._player.duration_changed.connect(self._on_duration_changed)
        self._player.media_changed.connect(self._on_media_changed)

        # 进度条
        self.progress_bar.sliderMoved.connect(self._on_progress_slider_moved)
        self.progress_bar.sliderReleased.connect(self._on_progress_released)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

    def _on_playing_changed(self, playing: bool):
        self.btn_play.setText("⏸" if playing else "▶")

    def _on_position_changed(self, position_ms: int):
        # 拖动/点击时不自动更新进度条
        if not self.progress_bar.is_scrubbing:
            self.progress_bar.setValue(position_ms)
        self.time_current.setText(self._format_time(position_ms))
        self.position_update_signal.emit(position_ms)

    def _on_duration_changed(self, duration_ms: int):
        self.progress_bar.setMaximum(max(duration_ms, 1))
        self.time_total.setText(self._format_time(duration_ms))

    def _on_media_changed(self, path: str):
        import os
        name = os.path.basename(path)
        stem = os.path.splitext(name)[0]
        if " - " in stem:
            parts = stem.split(" - ", 1)
            self.current_artist.setText(parts[0])
            self.current_title.setText(parts[1])
        else:
            self.current_title.setText(stem)
            self.current_artist.setText("")

    def _on_progress_slider_moved(self, value: int):
        """拖动/点击过程中实时 seek"""
        self._player.seek(value)

    def _on_progress_released(self, value: int):
        """释放后确保 seek"""
        self._player.seek(value)

    def _on_volume_changed(self, value: int):
        self._player.set_volume(value)
        self.volume_text.setText(f"{value}%")
        if value == 0:
            self.volume_icon.setText("🔇")
        elif value < 50:
            self.volume_icon.setText("🔉")
        else:
            self.volume_icon.setText("🔊")

    def _on_toggle_play_mode(self):
        modes = [
            (PlayMode.LOOP, "🔁", "列表循环"),
            (PlayMode.SINGLE_LOOP, "🔂", "单曲循环"),
            (PlayMode.RANDOM, "🔀", "随机播放"),
            (PlayMode.SEQUENTIAL, "➡️", "顺序播放"),
        ]
        current_idx = next(i for i, (m, _, _) in enumerate(modes) if m == self._play_mode)
        next_idx = (current_idx + 1) % len(modes)
        self._play_mode, icon, tooltip = modes[next_idx]
        self._player.play_mode = self._play_mode
        self.btn_mode.setText(icon)
        self.btn_mode.setToolTip(tooltip)
        self.play_mode_changed.emit(self._play_mode)

    def _on_toggle_play_pause(self):
        self._player.toggle_play_pause()

    def _on_prev(self):
        self._player.previous()

    def _on_next(self):
        self._player.next()

    def _on_load_file(self):
        from music_player.config import MUSIC_DIR
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", str(MUSIC_DIR),
            "音频/视频文件 (*.mp3 *.flac *.wav *.m4a *.ogg *.wma *.aac *.mp4 *.mkv)"
        )
        if files:
            self.files_loaded.emit(files)

    def set_current_song_info(self, title: str, artist: str, album: str = ""):
        self.current_title.setText(title)
        self.current_artist.setText(artist)

    def _format_time(self, ms: int) -> str:
        total_sec = ms // 1000
        m = total_sec // 60
        s = total_sec % 60
        return f"{m:02d}:{s:02d}"

    # 信号
    play_mode_changed = pyqtSignal(str)
    position_update_signal = pyqtSignal(int)
    files_loaded = pyqtSignal(list)
