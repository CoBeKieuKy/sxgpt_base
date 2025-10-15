"""共通処理を定義するモジュール"""

import base64
import json
import re
import time
from io import BytesIO
from math import ceil
from typing import Any
from PIL import Image, ImageOps
import tiktoken
from openai import Stream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
)

# ------------------------------------------------------------------------------
#   Parameter設定
# ------------------------------------------------------------------------------
# 画像インプットの設定 (OpenAIのマニュアル参考)
config_pic_params = {
    "unit_one_side": 512,
    "one_side_limit": 2048,
    "short_side_limit": 768,
    "base_token": 85,
    "extra_token": 170,
}


def crawring_message(message: str, sleep=0.01):
    """メッセージを1文字ずつストリーミング
    Args:
        message (str): メッセージ
        sleep (float): スリープ時間
    Yields:
            str: メッセージの1文字"""
    for w in message:
        yield w
        time.sleep(sleep)


def crawring_message_from_response(
    response: ChatCompletion | Stream[ChatCompletionChunk], sleep=0.01
):
    """ChatGPTのレスポンスから1文字ずつストリーミング
    Args:
        response (ChatCompletionChunk): ChatGPTのレスポンス
        sleep (float): スリープ時間
    Yields:
        str: メッセージの1文字
    """
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content is not None:  # type: ignore
            for w in chunk.choices[0].delta.content or " ":  # type: ignore
                yield w
                time.sleep(sleep)


def num_tokens_from_messages(
    messages, model="gpt-3.5-turbo-0301", config_pic: dict | None = None
):
    """メッセージリストからトークン数をカウントする
    Args:
        messages (list[dict]): メッセージリスト
        model (str): モデル名
        config_pic (dict): 画像の設定
    Returns:
        int: トークン数
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    #
    config_pic_ = config_pic or config_pic_params
    #
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            if (key == "content") and (isinstance(value, list)):
                for data in value:
                    if data["type"] == "image_url":
                        num_tokens += num_toke_from_pic_url(
                            data["image_url"]["url"], **config_pic_
                        )
                    else:
                        k = data["type"]
                        num_tokens += len(encoding.encode(data[k]))
            else:
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += (
                        -1
                    )  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def reduce_messages(
    messages: list[dict[str, str]],
    model: str = "gpt-3.5-turbo-0301",
    token_limit: int = 4097,
    safety_factor: float = 0.9,
    max_response_token: int = 500,
) -> list[dict[str, Any]]:
    """メッセージリストを設定トークン最大数まで削減する
    Args:
        messages (list[dict]): メッセージリスト
        model (str): モデル名
        token_limit (int): トークン最大数
        safety_factor (float): 安全率
        max_response_token (int): レスポンス最大トークン数
    Returns:
        list[dict]: メッセージリスト
    """
    itoken = num_tokens_from_messages(messages)
    token_limit = int(token_limit * safety_factor)
    while (itoken + max_response_token) >= token_limit:
        del messages[1]
        if len(messages) < 3:
            break
        itoken = num_tokens_from_messages(messages, model)
    return messages


pattern = r"data:image/[a-zA-Z0-9]+;base64,(?P<base64_data>[a-zA-Z0-9+/=]+)"
re_base64 = re.compile(pattern)


def num_toke_from_pic_url(
    image_url: str,
    unit_one_side: int = 512,
    one_side_limit: int = 2048,
    short_side_limit: int = 768,
    base_token: int = 85,
    extra_token: int = 170,
) -> int:
    """画像URLからトークン数をカウントする
    Args:
        image_url (str): 画像URL
        unit_one_side (int): 一辺の基準サイズ
        one_side_limit (int): 一辺の最大サイズ
        short_side_limit (int): 短辺の最大サイズ
        base_token (int): 基本トークン数
        extra_token (int): 追加トークン数
    Returns:
        int: トークン数
    """
    #    image_base64 = re_base64.match(image_url)
    image_base64 = image_url.split(",")[-1]
    image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data))

    width, height = image.size

    num = num_token_from_pic(
        width,
        height,
        unit_one_side,
        one_side_limit,
        short_side_limit,
        base_token,
        extra_token,
    )
    return num


def num_token_from_pic(
    width: int,
    height: int,
    unit_one_side: int = 512,
    one_side_limit: int = 2048,
    short_side_limit: int = 768,
    base_token: int = 85,
    extra_token: int = 170,
) -> int:
    """画像からトークン数をカウントする
    Args:
        width (int): 幅
        height (int): 高さ
        unit_one_side (int): 一辺の基準サイズ
        one_side_limit (int): 一辺の最大サイズ
        short_side_limit (int): 短辺の最大サイズ
        base_token (int): 基本トークン数
        extra_token (int): 追加トークン数
    Returns:
        int: トークン数
    """
    width_, height_ = get_normalized_pic_size(
        width, height, one_side_limit, short_side_limit
    )
    num_token = base_token
    if (width_ > unit_one_side) or (height_ > unit_one_side):
        w = ceil(width_ / float(unit_one_side))
        h = ceil(height_ / float(unit_one_side))
        num_token += extra_token * w * h

    return num_token


# ------------------------------------------------------------------------------
# JSONCファイルのパース
# ------------------------------------------------------------------------------
def remove_comments(text):
    pattern = re.compile(
        r"""
        ("(?:\\.|[^"\\])*") |   # ダブルクオーテーションで囲まれた文字列（グループ1）
        (/\*[\s\S]*?\*/)|       # マルチラインコメント（グループ2）
        (//.*?$)                # シングルラインコメント（グループ3）
    """,
        re.VERBOSE | re.MULTILINE,
    )

    def replacer(match):
        # 文字列リテラルがマッチしている場合はそのまま返す
        if match.group(1):
            return match.group(1)
        # コメント部分は空文字に置換する
        return ""

    return pattern.sub(replacer, text)


def load_jsonc(filepath, encoding="utf-8") -> dict[Any, Any]:
    """JSONCファイルを読み込む
    Args:
        filepath (str): ファイルパス
        encoding (str): エンコーディング
    Returns:
        dict[str, str]: JSONCファイルの内容
    """
    with open(filepath, "rb") as f:
        text = f.read().decode(encoding)
        text_without_comment = remove_comments(text)
    return json.loads(text_without_comment)


# ------------------------------------------------------------------------------
# 画像のリサイズ
# ------------------------------------------------------------------------------
def get_normalized_pic_size(
    width: int, height: int, one_side_limit=2048, short_side_limit=768
) -> tuple[int, int]:
    """ChatGPT画像インプットの適正サイズを取得する (縦横比は変わらない)
    Args:
        width (int): 幅
        height (int): 高さ
        one_side_limit (int): 一辺の最大サイズ
        short_side_limit (int): 短辺の最大サイズ
    Returns:
        tuple[int, int]: 幅, 高さ
    """
    ratio = width / float(height)
    r = 1.0
    if ratio > 1.0:
        if width > one_side_limit:
            r = width / float(one_side_limit)
        if height * r > short_side_limit:
            r *= one_side_limit / (r * height)
    else:
        if height > one_side_limit:
            r = one_side_limit / float(height)
        if width * r > short_side_limit:
            r *= short_side_limit / (r * width)

    width_, height_ = int(r * width), int(r * height)

    return width_, height_


def resize_pic(image: Image.Image, size):

    image_ = ImageOps.fit(
        image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)
    )
    return image_


def to_normalized_pic(image: Image.Image):
    width, height = image.size
    size = get_normalized_pic_size(width, height)
    image_ = resize_pic(image, size)
    return image_


def to_thumbnail_pic(
    image: Image.Image,
    height: int = 180,
    bgcolor: tuple[int, int, int] | None = None,
):
    #
    image_ = image
    if image.height > height:
        width = int(image.width / float(image.height) * height)
        size = (width, height)
        image_ = resize_pic(image, size)

    bgcolor = bgcolor or (220, 220, 220)
    thumbnail_image = Image.new("RGB", image_.size, bgcolor)
    try:
        thumbnail_image.paste(image_, (0, 0), image_)
    except ValueError:
        thumbnail_image = image_
    return thumbnail_image


def convert_byte_to_image(
    image_byte: bytes, normalization: bool = False
) -> Image.Image:
    """バイナリデータを画像に変換する
    Args:
        image_byte (bytes): バイナリデータ
    Returns:
        Image.Image: 画像
    """
    image = Image.open(BytesIO(image_byte))
    if normalization:
        image = to_normalized_pic(image)
    return image


def convert_image_to_url(image: Image.Image) -> str:
    """画像データをBase64エンコードしてURLに変換する
    Returns:
        str: 画像URL
    """
    image_buffer = BytesIO()
    image.save(image_buffer, format="png")
    image_byte = image_buffer.getvalue()
    image_base64 = base64.b64encode(image_byte).decode("utf-8")
    return image_base64
