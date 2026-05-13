"""
侧边栏 - 歌单列表 + 右键菜单
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QMenu, QLineEdit, QInputDialog
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon

from music_player.config import THEME
from music_player.playlist_manager import playlist_manager


class SidebarPlaylistItem(QListWidgetItem):
    """侧边栏歌单项 - 支持自定义图标"""
    pass


class Sidebar(QWidget):
    """侧边栏 - 显示歌单列表"""

    # 信号
    playlist_selected = pyqtSignal(str)      # 选中歌单
    playlist_created = pyqtSignal()          # 创建歌单后刷新索引
    playlist_deleted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_playlist = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题
        title = QLabel("🎵 我的音乐")
        title.setStyleSheet(f"""
            QLabel {{
                color: {THEME['text_primary']};
                font-size: 16px;
                font-weight: bold;
                padding: 16px 12px 8px;
            }}
        """)
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # 新建歌单按钮
        btn_new = QPushButton("+ 新建歌单")
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_light']};
            }}
        """)
        btn_new.clicked.connect(self._on_create_playlist)
        layout.addWidget(btn_new, 0, Qt.AlignmentFlag.AlignHCenter)

        # 歌单列表
        self.playlist_list = QListWidget()
        self.playlist_list.setIconSize(QSize(32, 32))
        self.playlist_list.setSpacing(4)
        self.playlist_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                padding: 8px 4px;
                outline: none;
            }}
            QListWidget::item {{
                color: {THEME['text_secondary']};
                padding: 8px 8px;
                border-radius: 4px;
                margin: 1px 0;
            }}
            QListWidget::item:selected {{
                background-color: {THEME['bg_hover']};
                color: {THEME['text_primary']};
            }}
            QListWidget::item:hover {{
                background-color: {THEME['bg_tertiary']};
            }}
        """)
        self.playlist_list.currentItemChanged.connect(self._on_playlist_selected)
        self.playlist_list.itemClicked.connect(self._on_playlist_clicked)
        self.playlist_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.playlist_list, 1)

        self._refresh_list()

    def _refresh_list(self):
        """刷新歌单列表"""
        self.playlist_list.clear()
        for pl in playlist_manager.get_all():
            item = QListWidgetItem(f"{pl.get('icon', '🎶')}  {pl['name']}")
            item.setData(Qt.ItemDataRole.UserRole, pl["id"])
            song_count = len(pl.get("songs", []))
            item.setToolTip(f"{pl['name']} ({song_count}首)")
            self.playlist_list.addItem(item)

    def _on_playlist_selected(self, current, previous):
        if current:
            pid = current.data(Qt.ItemDataRole.UserRole)
            self._selected_playlist = pid
            self.playlist_selected.emit(pid)

    def _on_playlist_clicked(self, item):
        pid = item.data(Qt.ItemDataRole.UserRole)
        self._selected_playlist = pid
        self.playlist_selected.emit(pid)

    def _on_create_playlist(self):
        name, ok = QInputDialog.getText(self, "新建歌单", "歌单名称:", text="我的新歌单")
        if ok and name.strip():
            playlist_manager.create(name.strip())
            self._refresh_list()
            self.playlist_created.emit()

    def _show_context_menu(self, pos):
        item = self.playlist_list.itemAt(pos)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        pl = playlist_manager.get(pid)
        if not pl or pl.get("built_in"):
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME['bg_secondary']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border']};
            }}
            QMenu::item:selected {{
                background-color: {THEME['bg_hover']};
            }}
        """)

        # 重命名
        act_rename = QAction("✏️  重命名", menu)
        act_rename.triggered.connect(lambda: self._on_rename(pid))
        menu.addAction(act_rename)

        menu.addSeparator()

        # 删除
        act_delete = QAction("🗑️  删除", menu)
        act_delete.triggered.connect(lambda: self._on_delete(pid))
        menu.addAction(act_delete)

        menu.exec(self.playlist_list.mapToGlobal(pos))

    def _on_rename(self, pid):
        pl = playlist_manager.get(pid)
        if not pl:
            return
        name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=pl["name"])
        if ok and name.strip():
            playlist_manager.rename(pid, name.strip())
            self._refresh_list()

    def _on_delete(self, pid):
        if playlist_manager.delete(pid):
            self._refresh_list()
            self.playlist_deleted.emit()
