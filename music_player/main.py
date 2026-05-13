#!/usr/bin/env python3
"""
音乐播放器 - 启动入口
仿网易云音乐播放器
"""
import sys
import os
import logging
import importlib.resources

# 高 DPI 支持 - 必须在导入 PyQt6 之前设置
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont

from music_player.ui.main_window import MainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)


def get_font_path() -> str:
    """获取字体文件路径（兼容开发和打包环境）"""
    # 打包后 _MEIPASS 是临时解压目录
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    font_path = os.path.join(base_dir, "hanqizaimin.ttf")
    if os.path.exists(font_path):
        return font_path
    return ""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("音乐播放器")
    app.setApplicationDisplayName("🎵 音乐播放器")
    app.setStyle("Fusion")

    # 注册自定义字体
    font_path = get_font_path()
    if font_path:
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id >= 0:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app.setFont(QFont(family, 10))
            print(f"✅ 已加载自定义字体: {family}")
        else:
            print(f"⚠️ 字体加载失败: {font_path}，使用系统默认字体")
            app.setFont(QFont("Noto Sans CJK SC, Microsoft YaHei, Sans Serif", 10))
    else:
        print("⚠️ 未找到自定义字体，使用系统默认字体")
        app.setFont(QFont("Noto Sans CJK SC, Microsoft YaHei, Sans Serif", 10))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
