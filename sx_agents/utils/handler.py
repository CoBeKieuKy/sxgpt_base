import datetime
import sys
import time
import uuid
from abc import ABCMeta, abstractmethod
from enum import Enum

from langchain.callbacks.base import BaseCallbackHandler, BaseCallbackManager
from PIL import Image


class Color(Enum):
    DEFAULT = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4
    RED = 5


ANSI_ESCAPE_SEQ = {
    Color.DEFAULT: "\033[0m",
    Color.BLUE: "\033[94m",
    Color.GREEN: "\033[92m",
    Color.YELLOW: "\033[93m",
    Color.RED: "\033[91m",
}

HTML_COLOR = {
    Color.DEFAULT: "black",
    Color.BLUE: "blue",
    Color.GREEN: "green",
    Color.YELLOW: "yellow",
    Color.RED: "red",
}


class TalkSender(metaclass=ABCMeta):
    message_placeholder: str = ""
    colors = Color
    with_color: bool = True  # 色付けするかどうか

    def __init__(self, with_color: bool = True):
        self.with_color = with_color
        self.init_stream()

    @abstractmethod
    def send(
        self,
        message: str | tuple[str, str],
        color: Color = Color.DEFAULT,
        images: list[Image.Image] | None = None,
    ):
        pass

    def init_stream(self):
        self.message_placeholder = ""

    def _ansi_color_text(self, text, color):
        """ANSI エスケープシーケンスで色付け"""
        if not (color == Color.DEFAULT):
            return f"{ANSI_ESCAPE_SEQ[color]}{text}{ANSI_ESCAPE_SEQ[Color.DEFAULT]}"
        return text

    def _html_color_text(self, text, color):
        """HTML タグで色付け"""
        if not (color == color.DEFAULT):
            text_html = text.replace("\n", "<br>")
            return (
                f'<span style="color: {HTML_COLOR[color]}">{text_html}</span>'
            )
        return text


class StdOutTalkSender(TalkSender):

    def __init__(self, with_color: bool = True):
        super().__init__(with_color)

    def send(
        self,
        message: str | tuple[str, str],
        color: Color = Color.DEFAULT,
        images: list[Image.Image] | None = None,
    ):
        if self.with_color:
            message = self._ansi_color_text(str(message), color)
        sys.stdout.write(str(message))
        sys.stdout.flush()


class AgentTalkCallbackHandler(BaseCallbackHandler):
    """Agentのトークとデバッグ時に手動ログ記録もできるカスタムコールバック"""

    chain_start_time: float | None = None  # チェーン開始時刻
    llm_start_time: float | None = None  # LLM開始時刻
    trace_id: str = ""  # トレースID
    sender: TalkSender  # トーク送信クラス
    debug: bool = False  # デバッグモード on/off
    color = Color

    def __init__(self, debug=False, sender: TalkSender = StdOutTalkSender()):
        self.debug = debug
        self.chain_start_time = None
        self.llm_start_time = None
        self.trace_id = str(uuid.uuid4())  # 実行ごとの一意な ID
        self.sender = sender

    def _timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log_custom_event(self, message, level="INFO"):
        """手動でメッセージをログに書き出す"""
        color = self.sender.colors
        color_map = {
            "INFO": color.BLUE,
            "WARNING": color.YELLOW,
            "ERROR": color.RED,
        }
        color = color_map.get(level, color.DEFAULT)  # 指定がない場合はDeault
        self.sender.send(f"[{self._timestamp()}] [{level}] {message}", color)

    def agent_speaks(
        self,
        my_name: str,
        message: str,
        color: Color = Color.GREEN,
        images: list[Image.Image] | None = None,
    ):
        """エージェントが発話する"""
        message_ = message
        if my_name:
            message_ = (my_name, message)
        self.sender.send(message_, color, images)

    def on_chain_start(self, serialized, inputs, **kwargs):
        if self.debug:
            color = self.sender.colors
            self.chain_start_time = time.time()
            chain_name = (
                kwargs.get("chain_name", "Unknown")
                if serialized is None
                else serialized.get("name", "Unknown")
            )
            self.sender.send("\n")
            self.sender.send("-" * 72 + "\n")
            self.sender.send(f"[{self._timestamp()}] Chain Start\n", color.BLUE)
            self.sender.send(f"Trace ID: {self.trace_id}\n")
            self.sender.send(f"Chain: {chain_name}\n")
            self.sender.send(f"Inputs: {inputs}\n")
            # self.sender.send("-" * 72 + "\n")

    def on_chain_end(self, outputs, **kwargs):
        if self.debug:
            elapsed = (
                time.time() - self.chain_start_time
                if self.chain_start_time
                else 0
            )
            color = self.sender.colors
            # self.sender.send("-" * 72 + "\n")
            self.sender.send(f"[{self._timestamp()}] Chain End\n", color.BLUE)
            self.sender.send(f"Execution Time: {elapsed * 1000:.2f} ms\n")
            self.sender.send(f"Outputs: {outputs}\n")
            self.sender.send(f"{outputs["messages"][-1]}\n", self.color.GREEN)
            self.sender.send("-" * 72 + "\n")

    @staticmethod
    def speaks(
        callbacks: (
            BaseCallbackHandler
            | list[BaseCallbackHandler]
            | BaseCallbackManager
            | None
        ),
        message: str,
        name: str = "",
        color: str = "GREEN",
        images: list[Image.Image] | None = None,
    ):
        """エージェントの発話を行うヘルパーメソッド"""
        if callbacks is None:
            return
        elif isinstance(callbacks, BaseCallbackManager):
            callbacks = callbacks.handlers
        elif not isinstance(callbacks, list):
            callbacks = [callbacks]

        callbacks_speaks = _extract_AgentTalkCallbackHandler(callbacks)
        for callback in callbacks_speaks:
            callback.agent_speaks(
                name,
                message,
                callback.color[color],
                images,
            )


def _extract_AgentTalkCallbackHandler(
    callbacks: list[BaseCallbackHandler] | None,
) -> list[AgentTalkCallbackHandler]:
    """AgentTalkCallbackHandlerを抽出する"""
    return [
        handler
        for handler in (callbacks or [])
        if isinstance(handler, AgentTalkCallbackHandler)
    ]
