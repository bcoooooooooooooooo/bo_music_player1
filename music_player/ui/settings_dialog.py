"""
设置对话框 - 主题颜色 / 字体大小 / 背景图片 / 构建索引
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QFormLayout, QSpinBox, QFileDialog,
    QMessageBox, QColorDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QPixmap

from music_player.settings import (
    load_settings, save_settings, DEFAULT_THEME, DEFAULT_FONT_SIZES,
    THEME_COLOR_LABELS, save_background_image
)
from music_player.config import THEME


class ColorPickerButton(QPushButton):
    """颜色选择按钮 - 点击弹出选色器"""

    def __init__(self, color: str, label: str, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(36, 28)
        self.setToolTip(f"{label}: {color}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid rgba(255,255,255,0.2);
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: rgba(255,255,255,0.5);
            }}
        """)
        self.clicked.connect(self._pick)
        self.color_picked.connect(self._on_color_picked)

    def _pick(self):
        color = QColorDialog.getColor(QColor(self._color), self, f"选择颜色")
        if color.isValid():
            self.color_picked.emit(color.name())

    def _on_color_picked(self, color_name: str):
        self._color = color_name
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_name};
                border: 2px solid rgba(255,255,255,0.2);
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: rgba(255,255,255,0.5);
            }}
        """)

    color_picked = pyqtSignal(str)

    def get_color(self) -> str:
        return self._color


class ThemeTab(QWidget):
    """主题颜色页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🎨 主题颜色设置 — 点击色块修改颜色"))
        layout.addWidget(QPushButton("恢复默认配色", clicked=self._reset))

        theme = load_settings().get("theme", DEFAULT_THEME)
        for key, label in THEME_COLOR_LABELS.items():
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label}"))
            row.addStretch()
            btn = ColorPickerButton(theme.get(key, DEFAULT_THEME.get(key, "#ffffff")), label)
            self._buttons[key] = btn
            row.addWidget(btn)
            layout.addLayout(row)

        layout.addStretch()

    def _reset(self):
        for key, btn in self._buttons.items():
            btn._color = DEFAULT_THEME.get(key, "#ffffff")
            btn._on_color_picked(btn._color)

    def get_theme(self) -> dict:
        return {key: btn.get_color() for key, btn in self._buttons.items()}


class FontSizeTab(QWidget):
    """字体大小页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._spins = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🔤 字体大小设置"))

        sizes = load_settings().get("font_sizes", DEFAULT_FONT_SIZES)
        labels = {
            "title": "标题字号",
            "subtitle": "副标题字号",
            "normal": "正文字号",
            "small": "小字号",
            "tiny": "极小字号",
        }

        form = QFormLayout()
        for key, label in labels.items():
            spin = QSpinBox()
            spin.setMinimum(8)
            spin.setMaximum(48)
            spin.setValue(sizes.get(key, DEFAULT_FONT_SIZES.get(key, 12)))
            self._spins[key] = spin
            form.addRow(label, spin)
        layout.addLayout(form)
        layout.addStretch()

    def get_font_sizes(self) -> dict:
        return {key: spin.value() for key, spin in self._spins.items()}


class BackgroundTab(QWidget):
    """背景图片页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg_path = load_settings().get("background_image", "")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🖼️ 自定义背景图片"))

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(150)
        self.preview.setStyleSheet("border: 1px dashed #555; border-radius: 6px;")

        if self._bg_path:
            self._show_preview(self._bg_path)
        else:
            self.preview.setText("暂无背景图片")
            self.preview.setStyleSheet("color: #666; border: 1px dashed #555; border-radius: 6px;")

        layout.addWidget(self.preview)

        btn_layout = QHBoxLayout()
        btn_select = QPushButton("📁 选择图片")
        btn_select.clicked.connect(self._select)
        btn_layout.addWidget(btn_select)

        btn_remove = QPushButton("🗑️ 移除背景")
        btn_remove.clicked.connect(self._remove)
        btn_layout.addWidget(btn_remove)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

    def _select(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", "",
            "图片 (*.jpg *.jpeg *.png *.bmp *.gif *.webp)"
        )
        if path:
            self._bg_path = save_background_image(path)
            self._show_preview(self._bg_path)

    def _show_preview(self, path: str):
        pm = QPixmap(path)
        if not pm.isNull():
            scaled = pm.scaled(400, 200, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
            self.preview.setPixmap(scaled)
        else:
            self.preview.setText("图片加载失败")

    def _remove(self):
        self._bg_path = ""
        self.preview.clear()
        self.preview.setText("暂无背景图片")

    def get_background(self) -> str:
        return self._bg_path


class IndexTab(QWidget):
    """索引管理页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🔍 音乐索引管理"))

        self.status_label = QLabel("点击下方按钮构建或更新索引")
        self.status_label.setStyleSheet("color: #a0a0a0; padding: 10px; font-size: 13px;")
        layout.addWidget(self.status_label)

        # 加载当前统计
        try:
            from music_player.indexer import get_index_stats
            stats = get_index_stats()
            if stats.get("total"):
                self.status_label.setText(
                    f"当前索引: {stats['total']} 首 · {stats['total_duration_str']} · "
                    f"{stats['artists']} 歌手 · {stats['albums']} 专辑\n"
                    f"索引时间: {stats.get('built_at', '未知')[:19]}"
                )
        except Exception:
            pass

        btn = QPushButton("🔍 构建/更新索引")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #c20c0c; color: white;
                border: none; border-radius: 6px;
                padding: 12px 32px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #e8432d; }
            QPushButton:disabled { background-color: #555; }
        """)
        btn.clicked.connect(self._build)
        layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

    def _build(self):
        self.status_label.setText("⏳ 正在构建索引...")
        self.findChild(QPushButton).setEnabled(False)
        QTimer.singleShot(100, self._do_build)

    def _do_build(self):
        try:
            from music_player.indexer import build_index, get_index_stats
            build_index(force_rebuild=True)
            stats = get_index_stats()
            self.status_label.setText(
                f"✅ 索引构建完成！\n{stats['total']} 首 · {stats['total_duration_str']} · "
                f"{stats['artists']} 歌手 · {stats['albums']} 专辑"
            )
        except Exception as e:
            self.status_label.setText(f"❌ 构建失败: {e}")
        finally:
            self.findChild(QPushButton).setEnabled(True)


class SettingsDialog(QDialog):
    """设置对话框"""

    theme_changed = pyqtSignal(dict)
    font_sizes_changed = pyqtSignal(dict)
    background_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 设置")
        self.setMinimumSize(480, 560)
        self.resize(520, 600)
        self.setModal(True)

        # 对话框样式
        self.setStyleSheet("""
            QDialog { background-color: #232328; }
            QTabWidget::pane {
                border: 1px solid #3a3a40;
                background-color: #1a1a1e;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #2a2a30;
                color: #a0a0a0;
                padding: 8px 18px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background-color: #333339;
                color: #e8e8e8;
            }
            QLabel { color: #c0c0c0; font-size: 12px; }
            QSpinBox {
                background-color: #2a2a30;
                color: #e8e8e8;
                border: 1px solid #3a3a40;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 80px;
            }
            QFormLayout { spacing: 10px; }
            QPushButton {
                background-color: #2a2a30;
                color: #e8e8e8;
                border: 1px solid #3a3a40;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #333339; }
        """)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        self._theme_tab = ThemeTab()
        self._font_tab = FontSizeTab()
        self._bg_tab = BackgroundTab()
        self._index_tab = IndexTab()

        tabs.addTab(self._theme_tab, "🎨 主题")
        tabs.addTab(self._font_tab, "🔤 字号")
        tabs.addTab(self._bg_tab, "🖼️ 背景")
        tabs.addTab(self._index_tab, "🔍 索引")

        layout.addWidget(tabs)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("✅ 保存")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #c20c0c; color: white;
                border: none; border-radius: 6px;
                padding: 8px 28px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #e8432d; }
        """)
        btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _on_save(self):
        """保存所有设置"""
        settings = load_settings()

        # 主题
        new_theme = self._theme_tab.get_theme()
        settings["theme"] = new_theme

        # 字号
        new_sizes = self._font_tab.get_font_sizes()
        settings["font_sizes"] = new_sizes

        # 背景
        new_bg = self._bg_tab.get_background()
        settings["background_image"] = new_bg

        save_settings(settings)

        # 发送信号
        self.theme_changed.emit(new_theme)
        self.font_sizes_changed.emit(new_sizes)
        self.background_changed.emit(new_bg)

        QMessageBox.information(self, "保存成功", "设置已保存并生效！")
        self.accept()

    def _on_cancel(self):
        reply = QMessageBox.question(
            self, "放弃更改",
            "设置尚未保存，确定要放弃更改吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.reject()
