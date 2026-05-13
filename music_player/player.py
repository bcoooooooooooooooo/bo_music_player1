"""
音频引擎 - 基于 PyQt6 QMediaPlayer
"""
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, pyqtSignal, QObject
import logging

logger = logging.getLogger(__name__)


class PlayMode:
    SEQUENTIAL = "sequential"    # 顺序播放
    LOOP = "loop"                # 列表循环
    SINGLE_LOOP = "single_loop"  # 单曲循环
    RANDOM = "random"            # 随机播放


class PlayerEngine(QObject):
    """音频播放引擎"""

    # 信号
    playing_changed = pyqtSignal(bool)
    current_position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    media_changed = pyqtSignal(str)
    playback_ended = pyqtSignal()
    volume_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        # 播放列表
        self._playlist = []
        self._current_index = -1
        self._play_mode = PlayMode.LOOP

        # 连接信号
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)

        # 默认音量 70%
        self.set_volume(70)

    @property
    def player(self):
        return self._player

    @property
    def play_mode(self):
        return self._play_mode

    @play_mode.setter
    def play_mode(self, mode):
        self._play_mode = mode

    @property
    def playlist(self):
        return self._playlist

    @property
    def current_index(self):
        return self._current_index

    @property
    def current_url(self) -> str:
        if 0 <= self._current_index < len(self._playlist):
            return self._playlist[self._current_index]
        return ""

    def set_playlist(self, playlist: list, start_index: int = 0):
        self._playlist = playlist[:]
        self._current_index = start_index
        if playlist:
            self.play_file(playlist[start_index])

    def play_file(self, file_path: str, auto_play: bool = True):
        import os
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        url = QUrl.fromLocalFile(os.path.abspath(file_path))
        self._player.setSource(url)

        if file_path in self._playlist:
            self._current_index = self._playlist.index(file_path)

        self.media_changed.emit(file_path)

        if auto_play:
            self._player.play()
        return True

    def play(self):
        self._player.play()

    def pause(self):
        self._player.pause()

    def stop(self):
        self._player.stop()

    def toggle_play_pause(self):
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def next(self):
        if not self._playlist:
            return
        if self._play_mode == PlayMode.RANDOM:
            import random
            self._current_index = random.randint(0, len(self._playlist) - 1)
        else:
            self._current_index = (self._current_index + 1) % len(self._playlist)
        self.play_file(self._playlist[self._current_index])

    def previous(self):
        if not self._playlist:
            return
        if self._player.position() > 3000:
            self._player.setPosition(0)
            return
        if self._play_mode == PlayMode.RANDOM:
            import random
            self._current_index = random.randint(0, len(self._playlist) - 1)
        else:
            self._current_index = (self._current_index - 1) % len(self._playlist)
        self.play_file(self._playlist[self._current_index])

    def seek(self, position_ms: int):
        self._player.setPosition(position_ms)

    def set_volume(self, volume: int):
        volume = max(0, min(100, volume))
        self._audio_output.setVolume(volume / 100.0)

    def get_volume(self) -> int:
        return int(self._audio_output.volume() * 100)

    def set_playback_rate(self, rate: float):
        self._player.setPlaybackRate(rate)

    def is_playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _on_position_changed(self, position_ms: int):
        self.current_position_changed.emit(position_ms)

    def _on_duration_changed(self, duration_ms: int):
        self.duration_changed.emit(duration_ms)

    def _on_state_changed(self, state):
        is_playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.playing_changed.emit(is_playing)

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.playback_ended.emit()
            self._handle_end_of_media()

    def _handle_end_of_media(self):
        if self._play_mode == PlayMode.SINGLE_LOOP:
            self._player.setPosition(0)
            self._player.play()
        elif self._play_mode == PlayMode.SEQUENTIAL:
            if self._current_index < len(self._playlist) - 1:
                self.next()
            else:
                self.stop()
        else:
            self.next()
