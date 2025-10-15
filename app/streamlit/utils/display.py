from html import escape
import pandas as pd
import streamlit as st

from sx_agents.utils import ChatMessage

# css = """
# <style>
# #MainMenu {visibility: hidden;}
# .stDeployButton {display:none;}
# </style>
# """
CSS_STYLE = """
<style>
.stDeployButton {display:none;}
</style>
"""


# ------------------------------------------------------------------------------
# Streamlitのスタイルを設定
# ------------------------------------------------------------------------------
def set_common_style():
    st.set_page_config(layout="wide", page_title="SX版GPT&文書要約")
    st.markdown(CSS_STYLE, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# @st.cache_data
def display_all_messages(messages: list[ChatMessage]) -> None:
    """メモリ内のメッセージを全て表示する
    Args:
        messages (list[ChatMemory]): メッセージのリスト
    Returns:
        None
    """
    # メモリ内にあるメッセージを表示
    for message in messages:
        if message.role == "system":
            continue
        elif message.role in ["error", "warning", "info", "success"]:
            display_attention(message.role, message.content)
        elif message.role == "status":
            with st.status(message.label, expanded=False, state="complete"):
                st.markdown(
                    message.content, unsafe_allow_html=message.unsafe_allow_html
                )
        else:
            with st.chat_message(message.role):
                with st.container():
                    st.markdown(
                        message.content,
                        unsafe_allow_html=message.unsafe_allow_html,
                    )
                    if message.thumbnails:
                        for image in message.thumbnails:
                            st.image(image)
                    elif message.images:
                        for image in message.images:
                            st.image(image)
                    if message.metadata:
                        for mdata in message.metadata:
                            if isinstance(mdata, pd.DataFrame):
                                st.dataframe(mdata)


def display_attention(role: str, content: str) -> None:
    """ステータス系のメッセージを表示する
    Args:
        role (str): メッセージの種類
        content (str): メッセージの内容
    Returns:
        None
    """
    if role == "error":
        st.error(content)
    elif role == "warning":
        st.warning(content)
    elif role == "info":
        st.info(content)
    elif role == "success":
        st.success(content)


# ------------------------------------------------------------------------------
# クリップボードへコピーするボタンを作成
# ------------------------------------------------------------------------------
# @st.cache_data
def clipboard_buttom_HTML(text_to_clipboard):
    clipboard_text = escape(f"{text_to_clipboard}\\n")

    # テーマ色を取得
    primary_color = st.get_option("theme.primaryColor")
    background_color = st.get_option("theme.backgroundColor")
    # secondary_background_color = st.get_option("theme.secondaryBackgroundColor")
    #    text_color = st.get_option("theme.textColor")
    text_color = "#FFFFFF"

    html = f"""
    <style>
    .clipboard-button {{
    background-color: {primary_color};
    color: {text_color};
    padding:  8px 8px;
    margin: -8px -8px;
    border: 2px solid {primary_color};
    border-radius: 8px;
    cursor: pointer;
    }}
    .clipboard-button:hover {{
    opacity: 0.9;
    border: 1px solid {primary_color};
    color: {text_color};
    }}
    </style>"""

    html += f"""<button class="clipboard-button" onclick='navigator.clipboard.writeText("{clipboard_text}");toggleButtonColor(this)'>Copy</button>
    """
    html += f"""
    <script>
        function toggleButtonColor(element) {{
            const originalColor = window.getComputedStyle(element).backgroundColor; // 元の背景色を取得
            const temporaryColor = '{background_color}'; // 一時的に変更する色
            element.style.backgroundColor = temporaryColor; // 色を変更
            // 500ミリ秒後に元の色に戻す
            setTimeout(function() {{
                element.style.backgroundColor = originalColor;
            }},70);
        }}
    </script>
"""
    return html
