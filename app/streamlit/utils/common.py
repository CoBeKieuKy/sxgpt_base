import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Self
from zoneinfo import ZoneInfo

import streamlit as st
from PIL import Image
from sx_agents.utils import load_jsonc
from sx_agents.utils.common import crawring_message, to_thumbnail_pic
from sx_agents.utils.handler import Color, TalkSender


# ------------------------------------------------------------------------------
# Parameter設定
# ------------------------------------------------------------------------------
@dataclass(frozen=True)
class ParameterSession:
    """
    グローバルパラメータを保持するクラス
    config.jsoncを読み込み、環境変数に応じて上書きする
    """

    VERSION: str
    DEFUALT_ENV: str
    WELLCOME_MESSAGE: str
    SYSTEM_ROLE: str
    PLUGINS: dict
    MODEL_CONFIG: dict
    DISPLAY_PIC_HEIGHT: int
    DISPLAY_PIC_BACKGROUND_COLOR: tuple[int, int, int]

    @classmethod
    def get(cls) -> Self:
        """
        Parametersのセッションステートを取得する
        """
        if "parameter" not in st.session_state:
            file_path = os.path.join(
                os.path.dirname(__file__), "../config.jsonc"
            )
            data = load_jsonc(file_path)
            TARGET = os.getenv("TARGET", "dev")
            # ENVに依存する変数は上書き
            data["PLUGINS"] = data["PLUGINS"][TARGET]
            data["DISPLAY_PIC_BACKGROUND_COLOR"] = tuple(
                data["DISPLAY_PIC_BACKGROUND_COLOR"]
            )
            # MODLEL_CONFIGのkeyとbaseを環境変数から取得
            config = data["MODEL_CONFIG"][data["DEFUALT_ENV"]]["config"]
            config["key"] = os.getenv(config["key"])
            config["base"] = os.getenv(config["base"])
            st.session_state["parameter"] = cls(**data)
        return st.session_state["parameter"]


class StreamlitTalkSender(TalkSender):
    def send(
        self,
        message: str | tuple[str, str],
        color: Color = Color.DEFAULT,
        images: list[Image.Image] | None = None,
    ):
        name, message_ = "エージェント", message
        if isinstance(message, tuple):
            name, message_ = message

        message_, code = extract_message_and_code(message_)
        with st.container():
            with st.status(name, expanded=True):
                st.write_stream(crawring_message(message_, sleep=0.001))
            if code:
                with st.status("pythonコード", expanded=False):
                    st.code(code, language="python")
            if images:
                for image in images:
                    st.image(to_thumbnail_pic(image))
        self.message_placeholder += f"{message_}\n"


def extract_message_and_code(text: str) -> tuple[str, str | None]:
    """
    text 中の ```python\n...``` ブロックを探し、
    - code: ブロック内部のコード（見つからなければ None）
    - message: コードブロックを除いた残りのテキスト
    を返す
    """
    m = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not m:
        return text, None
    pre, code, post = text[: m.start()], m.group(1), text[m.end() :]
    return pre + post, code


def hello():
    now = datetime.now(ZoneInfo("Asia/Tokyo")).hour
    if now < 5:
        return "夜遅くまでご苦労さまです、"
    if now < 10:
        return "おはようございます！"
    if now < 18:
        return "こんにちは！"
    else:
        return "こんばんは、"
