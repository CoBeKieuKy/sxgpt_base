#!/bin/bash

# エラーハンドリングの設定
set -euo pipefail

# .envファイルの存在確認と読み込み
# if [ -f .env ]; then
#     set -a
#     source .env
#     set +a
# fi

# poetry installの実行
poetry install
