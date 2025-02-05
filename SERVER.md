# server

## VPSコントロールパネルログイン

[会員メニュー](https://secure.sakura.ad.jp/menu/top/)

契約中のサービス一覧 -> サーバーを選択して「コントロールパネルを開く」

## ターミナル

ターミナル系アプリを開いて

```bash
ssh ubuntu@tk2-217-18362.vs.sakura.ne.jp
```

パスワードを聞かれるのでパスワードを入力。
またはコントロールパネルから
「コンソール」->「VNCコンソール」

## 作業ディレクトリ

```bash
cd /home/ubuntu/Stamp-rally-Digital/app
```

## 起動系

### サービスファイルをリロード

```bash
sudo systemctl daemon-reload
```

### サービスを有効化（システム起動時に自動起動）

```bash
sudo systemctl enable flask-app
```

### サービスを起動

```bash
sudo systemctl start flask-app
```

### サービスのステータスを確認

```bash
sudo systemctl status flask-app
```

## 停止系

### サービスの停止

```bash
sudo systemctl stop flask-app
```

### サービスの再起動

```bash
sudo systemctl restart flask-app
```

### ログの確認

```bash
sudo journalctl -u flask-app
```
