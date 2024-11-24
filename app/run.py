from app import app
    #データベースの設定やテストデータの挿入に何か知らのコードを追加するなど、変更を加えたらdata.dbのファイルを削除して再度実行。
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8888, threaded=True)  