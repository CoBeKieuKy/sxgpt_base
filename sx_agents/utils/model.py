import os
from dataclasses import dataclass, field
from typing import Any

from langchain.chat_models.base import BaseChatModel
from langchain_openai import ChatOpenAI

from .common import num_tokens_from_messages


@dataclass
class Model:
    """モデル設定クラス"""

    name: str = ""
    type: str = "openai"  # 環境名
    secret_keys: dict[str, str] = field(default_factory=dict)  # 秘密情報の環境変数名
    config: dict[str, Any] = field(default_factory=dict)  # モデル設定
    vision: bool = False  # 画像モデルかどうか
    visible: bool = True  # UI表示するかどうか
    token_limit: int | None = None
    max_response_token: int | None = None

    def create_langchain_chat(self, callbacks=None, **kwargs) -> BaseChatModel:
        """LangchainのChatGPTクライアントを生成する
        Args:
            callbacks (list[Callable]): コールバック関数
            **kwargs: その他のパラメータ
        Returns:
            BaseChatModel: LangchainのChatGPTクライアント
        """
        secret_keys = {k: os.getenv(v, "") for k, v in self.secret_keys.items()}
        config_ = self.config | secret_keys

        if self.type == "azure":
            client = create_langchain_chat_azure(config_, callbacks=callbacks, **kwargs)
        else:
            raise ValueError(f"{self.type} is not supported.")
        return client

    def count_tokens_from_message(self, messages: list[dict[str, Any]]) -> int:
        """メッセージリストからトークン数をカウントする
        Args:
            messages (list[dict]): メッセージリスト
        Returns:
            int: トークン数
        """
        return num_tokens_from_messages(
            messages, model=self.config.get("model_name", "gpt-3.5-turbo")
        )

    #
    def is_less_than_token_limit(self, messages: list[dict[str, Any]]) -> bool:
        """トークン数が制限以下かどうかを判定する
        Args:
            messages (list[dict]): メッセージリスト
        Returns:
            bool: トークン数が制限以下かどうか
        """
        num_token = self.count_tokens_from_message(messages)
        return num_token + self.max_response_token < self.token_limit


def create_langchain_chat_azure(
    config: dict[str, Any], callbacks=None, **kwargs
) -> BaseChatModel:
    """LangchainのChatGPTクライアントを生成する
    Args:
        callbacks (list[Callable]): コールバック関数
        **kwargs: その他のパラメータ
    Returns:
        BaseChatModel: LangchainのChatGPTクライアント
    """

    config_ = config | kwargs

    temp = kwargs.get("temperature", 1.0)
    if config["model_name"] == "gpt-4o":
        temp = 0.3

    client = ChatOpenAI(
        temperature=temp,
        # callbacks=callbacks,
        **config_,
    )
    return client
