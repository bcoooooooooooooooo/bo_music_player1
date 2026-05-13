"""
歌词显示组件 - 仿网易云滚动歌词
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRectF, pyqtProperty
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QPen

from music_player.config import THEME
from music_player.lyrics import load_lyrics, get_lyric_index


class LyricLine(QWidget):
    """单行歌词"""
    def __init__(self, text: str, is_active: bool = False, parent=None):
        super().__init__(parent)
        self._text = text
        self._is_active = is_active
        self.setFixedHeight(36)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    @property
    def text(self):
        return self._text

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont("Microsoft YaHei", 14 if self._is_active else 12)
        if self._is_active:
            font.setBold(True)
        painter.setFont(font)

        color = QColor(THEME["accent"]) if self._is_active else QColor(THEME["text_secondary"])
        painter.setPen(color)

        rect = self.rect()
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)

        painter.end()


class LyricsDisplay(QWidget):
    """歌词显示区域"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lyrics = []       # list of (time, text)
        self._current_index = -1
        self._current_time = 0
        self._lyric_widgets = []
        self._init_ui()

    def _init_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 30, 20, 30)
        self._layout.setSpacing(2)

        # 滚动区域
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {THEME['scrollbar_bg']};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {THEME['scrollbar_handle']};
                border-radius: 3px;
                min-height: 30px;
            }}
        """)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(2)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll.setWidget(self._content)
        self._layout.addWidget(self._scroll)

        # 默认提示
        self._set_placeholder("暂无歌词")

    def _set_placeholder(self, text: str):
        """设置占位文本"""
        self._clear_lyrics()
        label = QWidget()
        label.setFixedHeight(100)
        label.setStyleSheet(f"""
            QWidget {{
                qproperty-alignment: AlignCenter;
            }}
        """)
        from PyQt6.QtWidgets import QLabel
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 14px;")
        self._content_layout.addWidget(label, 0, Qt.AlignmentFlag.AlignCenter)

    def _clear_lyrics(self):
        """清除所有歌词"""
        for w in self._lyric_widgets:
            w.deleteLater()
        self._lyric_widgets = []
        # 清除 layout 中的 widgets (除了 placeholder)
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def set_lyrics(self, audio_path: str):
        """设置歌词"""
        self._lyrics = load_lyrics(audio_path)
        if not self._lyrics:
            self._set_placeholder("暂无歌词")
            return

        self._clear_lyrics()
        self._current_index = -1

        for time_sec, text in self._lyrics:
            widget = LyricLine(text)
            self._lyric_widgets.append(widget)
            self._content_layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignHCenter)

        # 底部填充
        spacer = QWidget()
        spacer.setMinimumHeight(200)
        self._content_layout.addWidget(spacer)

    def update_position(self, current_time_ms: int):
        """更新当前播放位置"""
        self._current_time = current_time_ms / 1000.0
        idx = get_lyric_index(self._lyrics, self._current_time)

        if idx != self._current_index and 0 <= idx < len(self._lyric_widgets):
            # 取消之前的 active
            if self._current_index >= 0:
                self._lyric_widgets[self._current_index].is_active = False

            self._current_index = idx
            self._lyric_widgets[idx].is_active = True

            # 滚动到当前行
            self._scroll_to_center(self._lyric_widgets[idx])

    def _scroll_to_center(self, widget: QWidget):
        """滚动使指定 widget 居中"""
        pos = widget.pos()
        center = pos.y() + widget.height() // 2
        scroll_bar = self._scroll.verticalScrollBar()
        current = scroll_bar.value()
        range_half = self._scroll.viewport().height() // 2
        scroll_bar.setValue(current + (center - range_half))

    def clear(self):
        """清空"""
        self._lyrics = []
        self._current_index = -1
        self._set_placeholder("暂无歌词")
