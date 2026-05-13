# 🎵 Music Player - 仿网易云音乐播放器

基于 Python + PyQt6 的桌面音乐播放器，仿网易云音乐界面风格。

## ✨ 功能特性

- 🎵 **音乐索引**：自动扫描音乐文件夹，构建索引
- 📋 **歌单管理**：创建、删除、重命名歌单，拖拽调整歌曲顺序
- 🎨 **主题定制**：自定义颜色主题、字体大小、背景图片
- 🎶 **播放模式**：列表循环 / 单曲循环 / 随机播放 / 顺序播放
- ⌨️ **快捷键**：空格播放/暂停，上下切歌，左右 ±5 秒
- 📝 **歌词显示**：支持 LRC 歌词文件，封面/歌词切换
- 🔀 **右键菜单**：加入歌单、收藏、移动歌曲位置
- 📦 **跨平台打包**：支持 Windows .exe 和 Linux 可执行文件

## 📸 界面预览

深色主题，仿网易云音乐布局：
- 左侧：歌单列表（可折叠）
- 中间上部：专辑封面 / 歌词切换
- 中间下部：歌曲列表（可折叠）
- 底部：播放控制栏（进度条、音量、播放按钮）

## 🚀 快速开始

### 从发行版运行（Linux）

下载最新 Release 中的 `MusicPlayer` 可执行文件：

```bash
chmod +x MusicPlayer
./MusicPlayer
```

首次运行会在 `~/.music_player/musics/` 创建音乐文件夹，把音乐文件放进去后程序会自动构建索引。

### 从源代码运行

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/MusicPlayer.git
cd MusicPlayer

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install PyQt6 mutagen -i https://mirrors.ustc.edu.cn/pypi/simple/

# 4. 运行
python -m music_player.main
```

## 📁 项目结构

```
MusicPlayer/
├── music_player/           # 源代码
│   ├── __init__.py
│   ├── main.py             # 入口
│   ├── config.py           # 配置和主题
│   ├── settings.py         # 用户设置管理
│   ├── indexer.py          # 音乐索引构建
│   ├── player.py           # QMediaPlayer 音频引擎
│   ├── playlist_manager.py # 歌单管理
│   ├── lyrics.py           # LRC 歌词解析
│   └── ui/                 # UI 界面
│       ├── main_window.py  # 主窗口
│       ├── sidebar.py      # 侧边栏
│       ├── song_table.py   # 歌曲列表
│       ├── now_playing.py  # 当前播放/歌词
│       ├── player_bar.py   # 底部播放控制
│       ├── lyrics_display.py # 歌词显示
│       └── settings_dialog.py # 设置对话框
├── musics/                 # 音乐文件夹（空，放你的音乐文件）
├── data/                   # 数据目录（自动生成）
│   ├── index.json          # 音乐索引
│   ├── settings.json       # 用户设置
│   ├── playlists/          # 歌单文件
│   └── backgrounds/        # 背景图片
├── hanqizaimin.ttf         # 自定义字体
├── venv/                   # 虚拟环境
├── build_linux.spec        # Linux 打包配置
├── build_windows.spec      # Windows 打包配置
├── run.sh                  # 快捷启动脚本
├── requirements.txt        # 依赖列表
├── README.md
└── LICENSE
```

## ⌨️ 快捷键

| 按键 | 功能 |
|------|------|
| 空格 | 播放/暂停 |
| ↑ | 上一首 |
| ↓ | 下一首 |
| ← | 后退 5 秒 |
| → | 前进 5 秒 |

## 🛠️ 打包发布

### Linux

```bash
pip install pyinstaller -i https://mirrors.ustc.edu.cn/pypi/simple/
pyinstaller build_linux.spec
# 输出: dist/MusicPlayer
```

### Windows

在 Windows 机器上执行：

```bash
pip install pyinstaller PyQt6 mutagen
pyinstaller build_windows.spec
# 输出: dist\MusicPlayer.exe
```

## ⚙️ 设置说明

点击侧边栏顶部的 ⚙️ 按钮打开设置界面：

- **🎨 主题**：自定义 14 种颜色（背景、文字、强调色等）
- **🔤 字号**：设置标题/正文/小字等不同元素的字号
- **🖼️ 背景**：上传自定义背景图片
- **🔍 索引**：手动构建/更新音乐索引

设置保存在 `~/.music_player/data/settings.json`

## 📜 许可证

MIT License
