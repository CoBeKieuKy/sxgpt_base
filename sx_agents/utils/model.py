"""ChatGPTクライアントとプロンプト操作関連の関数を提供するモジュール"""

from typing import Any
from dataclasses import dataclass

from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI, Stream

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
)

from .common import num_tokens_from_messages, reduce_messages


@dataclass
class Model:
    """モデルを生成するためのパラメータを保持するデータクラス"""

    type: str  # 環境名: "Azure"
    name: str  # モデル名
    key: str  # APIキー
    base: str  # エンドポイント
    version: str  # APIバージョン
    vision: bool = True  # 画像モデルかどうか
    safety_factor: float = 0.95
    token_limit: int = 8192
    max_response_token: int = 500

    def create_client(self, **kwargs) -> AzureOpenAI:
        """AzureOpenAIクライアントを生成する
        Args:
            **kwargs: OpenAI APIの初期化に渡すキーワード引数
        Returns:
            AzureOpenAI: AzureOpenAIクライアント
        """
        if self.type != "azure":
            raise NotImplementedError("This enviroment is not implemented.")
        try:
            client = AzureOpenAI(
                azure_endpoint=self.base,
                api_key=self.key,
                api_version=self.version,
                **kwargs,
            )
        except Exception as e:
            raise IOError(f"Failed to create AzureOpenAI client: {e}") from e
        return client

    def create_chat(
        self,
        messages: list[dict[str, Any]],
        stream: bool = False,
        **kwargs,
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        """ChatGPTのリクエストを送信する
        Args:
            model_name (str): モデル名
            messages (list[dict]): メッセージリスト
            stream (bool): ストリームモード
            **kwargs: その他のパラメータ
        Returns:
            ChatCompletion | Stream[ChatCompletionChunk]: ChatGPTのレスポンス
        """
        client = self.create_client()
        response = client.chat.completions.create(
            model=self.name,
            messages=messages,  # type: ignore
            stream=stream,
            **kwargs,
        )
        return response

    #
    def create_langchain_client(
        self, stream=False, callbacks=None, **kwargs
    ) -> AzureOpenAI:
        """Langchainのクライアントを生成する
        Args:
            streaming (bool): ストリーミングモード
            callbacks (list[Callable]): コールバック関数
            **kwargs: その他のパラメータ
        Returns:
            AzureOpenAI: Langchainのクライアント
        """
        raise NotImplementedError("This client was not implimented yet.")

    def create_langchain_chat(
        self, callbacks=None, **kwargs
    ) -> AzureChatOpenAI:
        """LangchainのChatGPTクライアントを生成する
        Args:
            streaming (bool): ストリーミングモード
            callbacks (list[Callable]): コールバック関数
            **kwargs: その他のパラメータ
        Returns:
            AzureChatOpenAI: LangchainのChatGPTクライアント
        """
        if self.type == "azure":
            # 2024/02/06 環境変数OPEN_AI_BASEがセットされていると、
            # Azureクライアントはそこから変数を読んでエラーを出すため、
            # Azure環境ではOPEN_AI_BASEはセットしないこと
            temp = kwargs.pop("temperature", 1)
            if self.name == "gpt-4o":
                temp = 0.3
            reasoning_effort = kwargs.pop("reasoning_effort", "medium")
            if self.name == "gpt-4o":
                reasoning_effort = None

            client = AzureChatOpenAI(
                openai_api_version=self.version,  # type: ignore
                openai_api_key=self.key,  # type: ignore
                azure_endpoint=self.base,
                deployment_name=self.name,  # type: ignore
                model_name=self.name,  # type: ignore
                # streaming=streaming,
                temperature=temp,
                # reasoning_effort=reasoning_effort,
                callbacks=callbacks,
                **kwargs,
            )
        else:
            raise ValueError(f"{self.type} is not supported.")
        return client

    #
    def count_tokens_from_message(self, messages: list[dict[str, Any]]) -> int:
        """メッセージリストからトークン数をカウントする
        Args:
            messages (list[dict]): メッセージリスト
        Returns:
            int: トークン数
        """
        return num_tokens_from_messages(messages, model=self.name)

    #
    def is_less_than_token_limit(self, messages: list[dict[str, Any]]) -> bool:
        """トークン数が制限以下かどうかを判定する
        Args:
            messages (list[dict]): メッセージリスト
        Returns:
            bool: トークン数が制限以下かどうか
        """
        num_token = self.count_tokens_from_message(messages)
        return (
            num_token + self.max_response_token
            < self.token_limit * self.safety_factor
        )

    #
    def reduce_messages(
        self,
        messages: list[dict[str, Any]],
        safety_factor=None,
        token_limit=None,
        max_response_token=None,
    ) -> list[dict[str, Any]]:
        """メッセージリストを削減する
        Args:
            messages (list[dict]): メッセージリスト
            safety_factor (float): 安全率
            token_limit (int): トークン数制限
            max_response_token (int): レスポンスのトークン数
        Returns:
            list[dict]: 削減されたメッセージリスト
        """
        token_limit_ = self.token_limit
        if token_limit:
            token_limit_ = token_limit
        safety_factor_ = self.safety_factor
        if safety_factor:
            safety_factor_ = safety_factor
        max_response_token_ = self.max_response_token
        if max_response_token:
            max_response_token_ = max_response_token
        reduced_messages = reduce_messages(
            messages,
            self.name,
            safety_factor=safety_factor_,
            token_limit=token_limit_,
            max_response_token=max_response_token_,
        )
        return reduced_messages
