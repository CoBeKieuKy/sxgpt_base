#-------------------------------------------------------------------------------
# build part
#-------------------------------------------------------------------------------
FROM python:3.12-bookworm as builder
#
WORKDIR /opt/app

# 必要なパッケージをインストール
RUN apt-get update \
    && apt-get install -y graphviz libgraphviz-dev pkg-config
COPY requirements.txt /opt/app
RUN pip3 install -r requirements.txt

#-------------------------------------------------------------------------------
# run part
#-------------------------------------------------------------------------------
FROM python:3.12-bookworm as runner
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends locales \
    && rm -rf /var/lib/apt/lists/*

# ロケールを設定
RUN echo "ja_JP.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8

# "appuser" という専用のグループとユーザーを作成（ログイン不要のシェル設定）
RUN groupadd -r appgroup && useradd -r -s /usr/sbin/nologin -g appgroup appuser

# 環境変数の設定
ARG _TARGET
ARG _PLATFORM
ARG _GOOGLE_CLIENT_ID
ARG _GOOGLE_CLIENT_SECRET
ARG _REDIRECT_URI
ARG _OPENAI_API_KEY
ARG _AZURE_API_BASE
ARG _AZURE_API_KEY1
ARG _AZURE_API_KEY2

ENV TARGET ${_TARGET}
ENV PLATFORM ${_PLATFORM}
ENV GOOGLE_CLIENT_ID ${_GOOGLE_CLIENT_ID}
ENV GOOGLE_CLIENT_SECRET ${_GOOGLE_CLIENT_SECRET}
ENV REDIRECT_URI ${_REDIRECT_URI}
ENV OPENAI_API_KEY ${_OPENAI_API_KEY}
ENV AZURE_API_BASE ${_AZURE_API_BASE}
ENV AZURE_API_KEY1 ${_AZURE_API_KEY1}
ENV AZURE_API_KEY2 ${_AZURE_API_KEY2}

RUN apt-get update \
    && apt-get install -y fonts-noto-cjk libgl1-mesa-dev nkf

WORKDIR /opt
COPY app ./app
COPY sx_agents ./sx_agents
COPY data/retriever data/retriever
COPY pyproject.toml .
COPY README.md .
RUN pip3 install .

RUN chown -R appuser:appgroup /opt
USER appuser

ENV PYTHONPATH="/opt:${PYTHONPATH}"
WORKDIR /opt/app/streamlit
ENTRYPOINT streamlit run main.py --server.port $PORT --browser.gatherUsageStats false --server.address=0.0.0.0 --server.enableStaticServing=true

#-------------------------------------------------------------------------------
# develop part
#-------------------------------------------------------------------------------
FROM python:3.12-bookworm as develop

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends locales \
    && rm -rf /var/lib/apt/lists/*

# ロケールを設定
RUN echo "ja_JP.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=ja_JP.UTF-8

# 環境変数の設定
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8

RUN apt-get update \
    && apt-get install -y bash curl build-essential zsh vim git curl fonts-noto-cjk nkf graphviz libgraphviz-dev pkg-config

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-cli -y

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
WORKDIR /workspace
# Poetryをインストール
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/home/$USERNAME/.local/bin:$PATH"
    
# Poetryの仮想環境設定をプロジェクト内にする
RUN poetry config virtualenvs.in-project true
