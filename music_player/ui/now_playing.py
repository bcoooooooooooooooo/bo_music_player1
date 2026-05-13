"""
专辑封面 + 当前播放信息 - 可切换到歌词
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPixmap, QFont, QPen, QBrush, QLinearGradient, QImage

from music_player.config import THEME
from music_player.lyrics import load_lyrics, get_lyric_index


class AlbumCoverWidget(QWidget):
    """专辑封面显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cover_path = None
        self._current_song = {"title": "未播放", "artist": ""}
        self.setMinimumSize(300, 300)
        self.setMaximumSize(400, 400)

    def set_song(self, title: str, artist: str = "", cover_path: str = ""):
        self._current_song["title"] = title
        self._current_song["artist"] = artist
        if cover_path:
            self._cover_path = cover_path
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        size = min(w, h)

        # 背景
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor(THEME["bg_tertiary"]))
        gradient.setColorAt(1, QColor(THEME["bg_primary"]))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse((w - size) // 2, (h - size) // 2, size, size)

        # 唱片纹
        painter.setPen(QPen(QColor(THEME["border"]), 1))
        for r in range(size // 6, size // 2, 12):
            painter.drawEllipse((w - size) // 2 + (size - r * 2) // 2,
                                (h - size) // 2 + (size - r * 2) // 2, r * 2, r * 2)

        # 中心圆
        painter.setBrush(QBrush(QColor(THEME["accent"])))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(w // 2 - 20, h // 2 - 20, 40, 40)

        # 歌曲信息
        painter.setPen(QColor(THEME["text_primary"]))
        font = QFont("Microsoft YaHei", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(0, h - 80, w, 30, Qt.AlignmentFlag.AlignCenter,
                         self._current_song["title"][:20])

        painter.setPen(QColor(THEME["text_secondary"]))
        font = QFont("Microsoft YaHei", 11)
        painter.setFont(font)
        painter.drawText(0, h - 52, w, 25, Qt.AlignmentFlag.AlignCenter,
                         self._current_song["artist"][:30])

        painter.end()


class NowPlayingWidget(QWidget):
    """当前播放区域 - 封面/歌词切换"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lyrics = []
        self._current_lyric_idx = -1
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 左侧: 封面
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.album_cover = AlbumCoverWidget()
        left_layout.addWidget(self.album_cover, 0, Qt.AlignmentFlag.AlignHCenter)

        # 切换按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_cover = QPushButton("封面")
        self.btn_lyrics = QPushButton("歌词")
        for btn in [self.btn_cover, self.btn_lyrics]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME['bg_tertiary']};
                    color: {THEME['text_secondary']};
                    border: none;
                    border-radius: 16px;
                    padding: 6px 20px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['bg_hover']};
                    color: {THEME['text_primary']};
                }}
                QPushButton:checked {{
                    background-color: {THEME['accent']};
                    color: white;
                }}
            """)
            btn.setCheckable(True)
            btn_layout.addWidget(btn)

        self.btn_cover.setChecked(True)
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)
        left_layout.addStretch()
        layout.addLayout(left_layout, 1)

        # 右侧: 歌词/信息
        self.right_widget = QStackedWidget()
        self.right_widget.setStyleSheet("background-color: transparent;")

        # 歌曲详情页
        self._detail_page = self._create_detail_page()
        self.right_widget.addWidget(self._detail_page)

        # 歌词页
        from music_player.ui.lyrics_display import LyricsDisplay
        self.lyrics_display = LyricsDisplay()
        self.right_widget.addWidget(self.lyrics_display)

        layout.addWidget(self.right_widget, 2)

        self.btn_cover.toggled.connect(lambda c: self.right_widget.setCurrentIndex(0 if c else 0))
        self.btn_lyrics.toggled.connect(lambda c: self.right_widget.setCurrentIndex(1 if c else 0))
        self.btn_cover.toggled.connect(self._on_view_toggle)
        self.btn_lyrics.toggled.connect(self._on_view_toggle)

    def _create_detail_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_title = QLabel("未播放歌曲")
        self.label_title.setStyleSheet(f"""
            color: {THEME['text_primary']};
            font-size: 22px;
            font-weight: bold;
        """)
        self.label_title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_title)

        self.label_artist = QLabel("")
        self.label_artist.setStyleSheet(f"""
            color: {THEME['text_secondary']};
            font-size: 16px;
            margin-top: 8px;
        """)
        self.label_artist.setFont(QFont("Microsoft YaHei", 13))
        self.label_artist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_artist)

        self.label_album = QLabel("")
        self.label_album.setStyleSheet(f"""
            color: {THEME['text_dim']};
            font-size: 14px;
            margin-top: 4px;
        """)
        self.label_album.setFont(QFont("Microsoft YaHei", 11))
        self.label_album.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_album)

        layout.addStretch()
        return page

    def _on_view_toggle(self, checked: bool):
        if self.btn_lyrics.isChecked():
            self.right_widget.setCurrentIndex(1)
        else:
            self.right_widget.setCurrentIndex(0)

    def set_song(self, title: str, artist: str = "", album: str = "", audio_path: str = ""):
        """更新当前播放信息"""
        self.album_cover.set_song(title, artist)
        self.label_title.setText(title)
        self.label_artist.setText(artist)
        self.label_album.setText(album)

        # 加载歌词
        if audio_path:
            self.lyrics_display.set_lyrics(audio_path)

    def update_lyrics_position(self, position_ms: int):
        """更新歌词位置"""
        self.lyrics_display.update_position(position_ms)

    def clear(self):
        """清空"""
        self.set_song("未播放", "", "")
        self.lyrics_display.clear()
