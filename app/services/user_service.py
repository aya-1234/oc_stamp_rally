import sqlite3
#必要に応じてservices層の関数にはサポートに以下を追加する。

#セッションを開くdb.session.commit()、閉じるdb.session.close()。

#エラーハンドリングtry,except,finally文
#トランザクションのロールバック、Exceptでエラーの時などdb.session.rollback(),エラーログを出すロギング。

#    except SQLAlchemyError as e:
#        db.session.rollback()
#        current_app.logger.error(f"Database error: {e}")
#        return None, str(e)

#成功時: (結果, None)
#失敗時: (None, エラーメッセージ)とタプルで返すとNoneを返せたり便利な関数になりそうなのだ。


#入力バリデーション
#認証と認可。必要に応じて。


#メインの関数には以下のような形。
#    try:このトライはエラーハンドリングを実装しようとした場合。
#        db = current_app.extensions['sqlalchemy'].db←これはデータベースへの接続準備
#
#        user = db.session.get(User, user_id)←これは 特定のユーザーデータの取得の関数。

#Flask-SQLAlchemy を使うと、Pythonコードでデータベースを操作できます。 
# db = current_app.extensions['sqlalchemy'].db と user = db.session.get(User, user_id) は、
# そのための２つの重要なステップです。
#一度 db を設定すれば、データベースとのやり取りに必要な機能が使えるようになります。


def authenticate_user(login_id):
    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USER WHERE loginId = ?', (login_id,))
        user = cursor.fetchone()
    return user  

# ユーザー情報を返す