# notecli

ローカルにメモを保存して管理する小さなCLIツールです。  
保存形式は JSON ファイルで、依存は標準ライブラリのみです。

## 実行方法

このリポジトリ内では、`projects/notecli/` に移動して次のように実行できます。

```bash
python -m notecli list
```

パッケージとしてインストールしたい場合は、`projects/notecli/` で以下を実行してください。

```bash
pip install -e .
```

## 保存先

デフォルトの保存先は次の通りです。

- `~/.local/share/notecli/notes.json`

保存先を変更したい場合は、全コマンドで共通の `--store PATH` を指定できます。

```bash
python -m notecli --store /tmp/notes.json add "メモ"
```

## コマンド

### add

```bash
python -m notecli add <text>
```

メモを1件追加し、追加したメモのIDを標準出力に表示します。  
`<text>` が複数語の場合は空白で区切って書くと自動的に結合されます（必要なら引用符で囲ってください）。

### list

```bash
python -m notecli list
```

保存されているメモを全件表示します。  
各行は `ID<TAB>created_at<TAB>text` の形式です。

### search

```bash
python -m notecli search <query>
```

`text` に `<query>` が含まれるメモを部分一致で表示します。  
検索は大文字小文字を区別しません。

### delete

```bash
python -m notecli delete <id>
```

指定したIDのメモを削除します。  
存在しないIDを指定した場合はエラーメッセージを表示して終了コード1で終了します。

## 開発

テストは `projects/notecli/` で以下を実行します。

```bash
python -m pytest
```

テストでは `--store` を使って一時ファイルに保存するようにしています。

