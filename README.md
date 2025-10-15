# LLMDemo
## Change Log
### v1.8.3 - 2024-11-29
- [Added] o1-preview, o1-miniを追加
- [changed] モデルごとに対応しているプラグインを設定
- [changed] Streamlit v1.40.2へアップデート
- [changed] LangChain v0.3.9へアップデート
- [changed] AzureOpenAIのAPIバージョンを2024-10-01-previewへアップデート
### v1.8.2 - 2024-10-21
- [Fixed] 画像プラグインでサイズが大きな画像の場合正しくリサイズされないバグを修正
- [Added] multimodalプラグインへxlsxのアップロードモードを追加
### v1.8.1 - 2024-10-04
- [Fixed] multimodalプラグイン中のi_pageとpython配列定義のズレを修正
### v1.8.0 - 2024-10-01
- [Changed] python3.12へアップデート
- [Changed] Streamlit v1.38.0へアップデート
- [Changed] LangChain v0.3へアップデート
- [Changed] unstructuredでpdfの読み込みを行わずpypdfを別に読み込み、モジュールサイズを削減
- [Added] 画像プラグインにpdf/ppt読みとり機能も追加し画像/pdf/pptプラグインへ変更
### v1.7.1 - 2024-09-12
- [Fixed] スプレッドシート逐次実行でCSVでの文字コード認識を修正
### v1.7.0 - 2024-09-04
- [Fixed] プラグインのセッションでのメモリーリークを修正
- [Changed] コピー&ペースト要約プラグインの復活
- [Changed] クリップボードコピーでユーザプロンプトを除外
- [Added] 文書要約でtxtファイルの対応
### v1.6.1 - 2024-08-24
- [Added] マニュアルリンク追加
### v1.6.0 - 2024-08-05
- [Added] spreadsheetプラグインの追加
- [Changed] コピー&ペースト要約プラグインの廃止
### v1.5.1 - 2024-07-22
- [Fixed] 本番環境でのsummarizeプラグイン名の修正
### v1.5.0 - 2024-07-12
- [Added] 画像アップロードプラグイン追加
- [Changed] それに伴いLLDemoのMemoryからmessagesの構造を変更
- [Changed] ファイル文書要約とコピー&ペースト要約が統合されファイル/コピー&ペースト文書要約へ
- [Fixed] クリップボードへのコピーでテキストに改行が含まれていた時にコピーできないバグを修正
### v1.4.0 - 2024-06-28
- [Changed] Streamlit v1.36.0へアップデート
- [Changed] GPT-4oへ変更
### v1.3.0 - 2024-04-11
- [Changed] Streamlit v1.33.0へアップデート
- [Changed] mainとdevで別々のプラグインリストをjsonで設定可能に
- [Added] copyとdownloadボタンを追加
### v1.2.0 - 2024-02-09
- [FIX] パフォーマンスチューニングを実施
- [Changed] プラグインで入口にplaceholderをmainから渡すように仕様変更
- [Changed] パッケージ管理をpoetryへ移行
- [Changed] コーディングルールをBlack Formatterへ統一
### v1.1.0 - 2024-02-09
- [Added] UI/UXの改善 (画面遷移、余計なコンポーネントの削除)
- [Added] メッセージ履歴管理様にmemoryクラスを追加
- [Changed] コード全般の大幅なリファクタリング
- [Changed] プラグイン仕様を策定
- [Changed] GPTModelのAPIを変更、初期化時に渡すインプットの変更
- [Changed] config.jsonへ変更 (json with comment形式)
### v1.0.3 - 2024-02-06
- [Fixed] cloud runのログでjsonPyloadが認識されないバグを修正
### v1.0.2 - 2024-02-06
- [Fixed] summarizeのファイルアップロード失敗で無限ループが発生するバグを修正
- [Fixed] エラーログでmodelを参照する時の例外を修正
### v1.0.1 - 2024-02-05
- [Added] 要約のアップロードページにキャンセルボタンを追加
- [Fixed] ログが多重で生成されるバグを修正
### v1.0.0 - 2024-02-05
- 正式版リリース
### v1.0.0b - 2024-02-01
- 全社公開プレビュー版

## 1. 作業環境準備
  - ### VM作成(P6 ~ P7) / VSCodeサーバ構築(P14 ~ P16)
    以下資料を参照し、作業用VMを構築する。OSはUbuntuを推奨。  
    [GCP開発環境ガイド.pptx](https://sigmaxyz.app.box.com/file/1306083164966?s=ljsl59p3449d5mmsz7dgizxyoz7bzomg)
    
    1.2. 開発環境構築 ：VM構築（1/3）~ VM構築（2/3）  
    1.4. 開発環境構築 ：VSCodeサーバ（1/3）~ VSCodeサーバ（3/3）
  
  - ### GitRepositoryクローン
    構築したVM上で、以下コマンドを実行しリポジトリからコード一式をクローンする。  
    この際PATを用いた認証が必要となる為、事前にPATを生成しておく事。  
    [個人用アクセス トークンを管理する - GitHub Docs](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

        git clone https://github.com/SxSkillupTask/LLMDemo.git
    
  - ### Python3.11インストール
    LLMDemoではpython3.11が必要な為、個別にインストールする。  
    以下コマンドを順に実施。

        sudo add-apt-repository ppa:deadsnakes/ppa  
        sudo apt update  
        sudo apt install python3.11  
        sudo apt install pip  
        sudo pip install --upgrade virtualenv  
        sudo apt install python3.11-venv  

  - ### poetryをインストール
    パッケージ管理にはpoetryを使うため、pip3によりインストール
        pip3.11 install poetry

  - ### ビルドツール、依存関係パッケージインストール
    LLMDemoではmakeコマンドを利用する為、個別にインストールする。  
  
        sudo apt install make  
        (クローンしたカレントディレクトリにて)
        sudo make init
        を実行すること。
  
## 2. コンテナイメージの作成、準備
  - ### Artifact Registory 作成 ( GCP ) 
    名前、ロケーションを手動で設定。入力は任意。  
    その他はデフォルトで作成。（形式：Docker、モード：標準、暗号化：Google管理、クリーンナップ：ドライラン）

  - ### Makefileファイル & .envファイルの修正 ( VM ) 
    作成したArtifact Registoryにコンテナイメージをアップロード出来るか確認の為、
    以下2ファイルのパラメータを修正する。.envについてはキー情報等が含まれる為、個別に確認する事。
    
        Makefile:
        PLATFORM=GCP  
        REGION=<レポジトリ作成時のリージョン>  
        PROJECT_ID=ats-ai-genaiapp-internal  
        REPOSITORY=<レポジトリ名>  
        IMAGE_NAME=<任意のイメージ名>  
        SERVICE_NAME=default  
        IMAGE_URL=$(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPOSITORY)/$(IMAGE_NAME):runner  
        REDIRECT_URI= default
    
        .env: 
        PLATFORM=GCP
        GOOGLE_CLIENT_ID=default
        GOOGLE_CLIENT_SECRET= default
        OPENAI_API_KEY=*****
        AZURE_API_BASE=*****
        AZURE_API_KEY1=*****
        AZURE_API_KEY2=*****

  - ### イメージアップロード ( VM ) 
    以下のコマンドを実行の上、コンテナイメージを作成/Artifact Registoryへアップロードする。  
    依存モジュール等のダウンロードが行われる為、数十分かかる。  

        (クローンしたカレントディレクトリにて) make build_full

## 3. アプリケーション展開
  - ### Cloud Runサービス作成 ( GCP ) 
    Cloud Runのページで手動で追加   
    既存コンテナイメージからデプロイ：Artifact Registory  
    サービス名：任意  
    CPU割り当て：リクエストの処理中のみ  
    自動スケーリング：min 0 max 5
    Ingressの制御：すべて（デプロイ後のアクセス確認の為、一時的に設定）  
    認証：未認証の呼び出しを許可  
    上り（内向き）の制御：内部  
    外部アプリケーション ロードバランサからのトラフィックを許可する
    
  - ### Makefileファイル & .envファイルの再修正 ( VM ) 
    cloudrunサービス作成後、URI情報等が確認出来る為、以下2ファイルの対象パラメータを個別に修正する。
    
        Makefile:
        SERVICE_NAME='<CloudRunサービス名>'   
        REDIRECT_URI="<CloudRunサービスURL>"
    
        .env: 
        REDIRECT_URI=<CloudRunサービスURL>  

  - ### コンテナイメージ更新、CloudRunアプリ更新 ( VM )
    以下コマンドを順に実施する。
    
        make build_full
        make deploy
    
## 4. CloudRunアプリへのアクセス制御追加
Cloud runのページへ行き、タブから設定する。
  - ### ネットワーキングタブからIngress制御変更
    上り（内向き）の制御：「すべて」から「内部＋LB(チェックボックス)」に変更
    
  - ### CloudRun統合機能の有効化（LB＋アクセス制御） ( GCP )
    統合[プレビュー]機能から「インテグレーションを追加」し、「カスタムドメイン」を選択。
   
    Routes - 「Domain指定」にて <任意文字>を入力。
    
    必要な API をそれぞれ有効化する。  
    ・Serverless Integrations API  
    ・Compute Engine API  

    SUBMITを実行し、必要なリソースが作成されるまで待つ。  
    リソースがデプロイされた後、登録が必要なDNSレコードが表示される為、  
    CloudDNSへAレコードを登録。  

  - ### IAP（Identity-Aware Proxy）実装
    アクセス制御をシグマドメインのみとする。  
    Identity-Aware Proxyページにアクセスし、Resourceから対象のLBを選択し、IAPを有効化。  
    デフォルトではIAPポリシー管理者や、PJ管理者などしかアクセス不可。  
    その為、メニュー右の「プリンシパルを追加」から以下のロールを追加し、保存する。  
    新しいプリンシパル：sigmaxyz.com  
    ロール：IAP-secured Web App User  
  
  ## 5. ローカル環境での検証方法
  - ### Pythonの仮想環境起動
    VSCodeにて「ターミナル」を開き、以下コマンドを実行
     
        source <クローンしたカレントディレクトリ>.venv/bin/activate
    
  - ### ローカル環境サーバ起動
    以下コマンドを実行後、ローカルにてサーバが起動する。
    
        make run

　　サーバ起動後、画面右下に「ブラウザで開く」ポップアップが出る為、クリック。  
　　その後「開く」ボタンをクリックし、アプリ画面に接続できることを確認する。
    
## 6. GCP VMセキュリティ設定
  - ### FW設定
    ※us-centralリージョンにVMが建てられている前提とする  

    1. Googleコンソールより、VMインスタンスを選択。  
    2. VM名をクリックし、詳細タブから編集にてネットワークタグを設定。他者と重複しなければ内容は何でも可。  
    3. VMの関連アクションより「ファイアウォール ルールの設定」を選択。  
    4. 以下の内容を考慮しつつ、新しくFWルールを設定。  
    ・方向：内向き  
    ・ポート：any  
    ・ターゲット：ネットワークタグで設定したタグ  
    ・IP：172.217.0.0/16  
　　
