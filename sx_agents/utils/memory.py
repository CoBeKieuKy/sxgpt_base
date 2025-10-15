"""メモリ操作とプロンプト作成用モジュール"""

import base64
from typing import Any
from io import BytesIO
from PIL import Image
from sx_agents.utils.common import to_thumbnail_pic, to_normalized_pic

SYSTEM_ROLE: str = (
    "I'm a consultant and prefer logical answers. "
    "I live in Tokyo, Japan, and I want to know information about Japan and other countries separately. "
    "Explanation of basic knowledge may be omitted from the answer. "
    "If there are no instructions, please answer in Japanese."
)


class ChatMessage:
    """メッセージを保持するクラス
    Args:
        role (str): System, User, Assistantもしくはerror, warning, info, successのステータスを含む
        content (str): メッセージの内容
        images (list[Image.Image]): 画像データ
        label (str): 画面表示するときのタグのラベル
    """

    role: str = ""
    content: str = ""
    images: list[Image.Image] = []
    metadata: list[Any] = []
    label: str = ""
    thumbnails: list[Image.Image] = []
    unsafe_allow_html: bool = False

    def __init__(
        self,
        role: str,
        content: str,
        images: (
            Image.Image
            | BytesIO
            | bytes
            | list[Image.Image | BytesIO | bytes]
            | None
        ) = None,
        label: str | None = None,
        unsafe_allow_html: bool = True,
        metadata: list[Any] | None = None,
        with_thumbnail: bool = True,
        thumbnail_hight: int = 180,
        thumbnail_bg_color: tuple[int, int, int] | None = None,
    ):
        self.role = role
        self.content = content
        self.label = label or ""
        self.unsafe_allow_html = unsafe_allow_html
        #
        self.images = []
        self.thumbnails = []
        self.metadata = metadata or []
        #
        if images:
            if not isinstance(images, list):
                images = [images]
            for image in images:
                self.append_image(
                    image, with_thumbnail, thumbnail_hight, thumbnail_bg_color
                )

    def append_image(
        self,
        image: Image.Image | BytesIO | bytes,
        with_thumbnail: bool = True,
        thumbnail_hight: int = 180,
        thumbnail_bg_color: tuple[int, int, int] | None = None,
    ):
        """画像データを追加する
        Args:
            image (Image.Image): 画像データ
        """
        if isinstance(image, BytesIO):
            image = Image.open(image)
        elif isinstance(image, bytes):
            image = Image.open(BytesIO(image))
        if not isinstance(image, Image.Image):
            raise NotImplementedError
        self.images.append(to_normalized_pic(image))
        if with_thumbnail:
            self.thumbnails.append(
                to_thumbnail_pic(image, thumbnail_hight, thumbnail_bg_color)
            )

    def to_image_url(self) -> list[str]:
        """画像データをBase64エンコードしてURLに変換する
        Returns:
            list[str]: 画像URLのリスト
        """
        contents = []
        for image in self.images:
            image_buffer = BytesIO()
            image.save(image_buffer, format="png")
            image_byte = image_buffer.getvalue()
            image_base64 = base64.b64encode(image_byte).decode("utf-8")
            contents.append(f"data:image/png;base64,{image_base64}")
        return contents

    def to_message(self, vision: bool = True) -> dict[str, Any]:
        """メッセージクラスをOpenAI API用のメッセージ形式へ変換する
        Returns:
            dict[str, str]: OpenAI API用のメッセージ形式
            dict[str, list[str,str]]: 画像データがある場合
        """
        content = self.content
        if vision and self.images:
            content = []
            content.append({"type": "text", "text": self.content})
            if self.images:
                for image_url in self.to_image_url():
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        }
                    )
        return {"role": self.role, "content": content}


class ChatMemory:
    """今までのチャットの履歴を保存するクラス
    Args:
        system_role (str): システムロールの保存/取得
        messages (list[ChatMessage]): チャットメッセージのリスト
    """

    messages: list[ChatMessage]
    THUMBNAIL_WIDTH: int = 180
    THUMBNAIL_BG_COLOR: tuple[int, int, int] = (220, 220, 220)

    def __init__(
        self,
        system_role: str | None = None,
        thumbnail_width: int | None = None,
        thumbnail_bg_color: tuple[int, int, int] | None = None,
    ):
        if (system_role is None) or (system_role is False):
            self.messages = []
        else:
            system_role_ = system_role or SYSTEM_ROLE
            self.messages: list[ChatMessage] = [
                ChatMessage("system", system_role_)
            ]
        self.THUMBNAIL_WIDTH = thumbnail_width or self.THUMBNAIL_WIDTH
        self.THUMBNAIL_BG_COLOR = thumbnail_bg_color or self.THUMBNAIL_BG_COLOR

    def clear(self):
        """システムロール以外のメッセージを削除する"""
        self.messages = [self.messages[0]]

    @property
    def system_role(self) -> str:
        """システムロールを取得する"""
        return self.messages[0].content

    @system_role.setter
    def system_role(self, system_role):
        self.messages[0] = self.messages[0].content = system_role

    def fetch_messages(
        self, roles=None, vision: bool = True
    ) -> list[dict[str, Any]]:
        """メッセージをChatGPTクライアントの形式で取得する
        Args:
            roles (list[str]): 取得したいメッセージのロール
        Returns:
            list[dict[str, str]]: ChatGPTクライアントの形式のメッセージリスト
        """
        if roles is None:
            roles = ["user", "assistant", "system"]
        messages = [
            memory.to_message(vision)
            for memory in self.messages
            if memory.role in roles
        ]
        return messages

    def fetch_recent_message(self, role: str) -> str:
        """指定したロールの最新のメッセージを取得する
        Args:
            role (str): System, User, Assistantもしくはerror, warning, info, successのステータスを含む
        Returns:
            ChatMessage: メッセージ
        """
        content = ""
        for message in self.messages[::-1]:
            if message.role == role:
                content = message.content
                break
        return content

    def append(
        self,
        role: str,
        content: str,
        images=None,
        label=None,
        metadata: list[Any] | None = None,
        unsafe_allow_html=False,
    ) -> None:
        """メッセージを追加する
        Args:
            role (str): System, User, Assistantもしくはerror, warning, info, successのステータスを含む
            content (str): メッセージの内容
            images (list[Image.Image]): 画像データ
            label (str): 画面表示するときのタグのラベル
        """
        self.messages.append(
            ChatMessage(
                role,
                content,
                images=images,
                label=label,
                unsafe_allow_html=unsafe_allow_html,
                metadata=metadata,
                thumbnail_hight=self.THUMBNAIL_WIDTH,
                thumbnail_bg_color=self.THUMBNAIL_BG_COLOR,
            )
        )

    def append_user(
        self,
        content: str,
        images=None,
        label: str | None = None,
        metadata: list[Any] | None = None,
    ):
        """ユーザーのメッセージを追加する
        Args:
            content (str): メッセージの内容
            images (list[Image.Image]): 画像データ
            label (str): 画面表示するときのタグのラベル
        """
        self.append("user", content, images, label, metadata=metadata)

    def append_assistant(self, content: str, label=None, metadata=None):
        """アシスタントのメッセージを追加する
        Args:
            content (str): メッセージの内容
            label (str): 画面表示するときのタグのラベル
        """
        self.append("assistant", content, label=label, metadata=metadata)

    def append_status(
        self, content: str, label=None, unsafe_allow_html=False, metadata=None
    ):
        """ステータスのメッセージを追加する
        Args:
            content (str): メッセージの内容
            label (str): 画面表示するときのタグのラベル
        """
        self.append(
            "status",
            content,
            label=label,
            unsafe_allow_html=unsafe_allow_html,
            metadata=metadata,
        )

    def append_warning(self, content: str):
        """警告メッセージを追加する
        Args:
            content (str): メッセージの内容
        """
        self.append("error", content)

    def append_error(self, content: str):
        """エラーメッセージを追加する
        Args:
            content (str): メッセージの内容
        """
        self.append("error", content)

    def prompt_with_all_messages(
        self,
        role: str,
        prompt: str,
        images: (
            Image.Image
            | BytesIO
            | bytes
            | list[Image.Image | BytesIO | bytes]
            | None
        ) = None,
        vision: bool = True,
        roles: list[str] | None = None,
        metadata: list[Any] | None = None,
    ) -> list[dict[str, Any]]:
        """入力したプロンプトと今までの全てのメッセージをつけてChatGPTクライアントの形式で取得 (ただし入力したプロンプトはメモリには記録しない)
        Args:
            role (str): System, User, Assistant
            prompt (str): プロンプト
            images (list[BytesIO | bytes | None]): 画像データ
            roles (list[str]): 取得したいメッセージのロール
        Returns:
            list[dict[str, str]]: OpenAI API形式のメッセージリスト"""
        roles_ = roles or ["user", "assistant", "system"]
        messages = self.fetch_messages(roles=roles_, vision=vision)
        message = ChatMessage(
            role,
            prompt,
            images,
            metadata=metadata,
            thumbnail_hight=self.THUMBNAIL_WIDTH,
            thumbnail_bg_color=self.THUMBNAIL_BG_COLOR,
        )
        messages.append(message.to_message(vision=vision))
        return messages

    def prompt_with_system_role(
        self,
        role: str,
        prompt: str,
        images: (
            Image.Image
            | BytesIO
            | bytes
            | list[Image.Image | BytesIO | bytes]
            | None
        ) = None,
        vision: bool = True,
        metadata: list[Any] | None = None,
    ) -> list[dict[str, Any]]:
        """入力したプロンプトにシステムロールをつけてChatGPTクライアントの形式で取得
        Args:
            role (str): System, User, Assistant
            prompt (str): プロンプト
            images (list[BytesIO | bytes | None]): 画像データ
        Returns:
            list[dict[str, str]]: ChatGPTクライアントの形式のメッセージリスト
        """
        messages = []
        messages.append(self.messages[0].to_message())
        messages.append(
            ChatMessage(
                role,
                prompt,
                images,
                metadata=metadata,
                thumbnail_hight=self.THUMBNAIL_WIDTH,
                thumbnail_bg_color=self.THUMBNAIL_BG_COLOR,
            ).to_message(vision=vision)
        )
        return messages

    def remove_temporary_messages(self, roles: list[str] | None = None) -> None:
        """ステータス、エラー、警告メッセージを削除する
        Args:
            roles (str): 削除するメッセージのロール
        """
        if roles is None:
            roles = ["status", "error", "warning"]
        self.messages = [
            message for message in self.messages if message.role not in roles
        ]
