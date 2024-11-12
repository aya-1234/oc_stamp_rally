from flask import Flask, request, render_template, flash
import sqlite3
import pandas as pd
from init4 import db, initialize_db, Login, Checkpoint, Quiz, Quiz_Response, Stamp, Survey, Survey_Choice, Survey_Response 
from services.user_service import authenticate_user
#やることは、全部のビジネスロジックと最低限のHTMLでべた付でいい。

#フォルダの下に写真を入れる。
# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

initialize_db(app)
# アプリケーションのテーブルにアクセスした後にセッションを閉じるための teardown_appcontext ハンドラを追加
@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception:  # 例外が発生した場合の処理を追加
        print(f"エラーが発生しました: {exception}")  # エラーログを出力
    db.session.remove()  # リクエストコンテキスト終了時にセッションを閉じる

# テーブルを操作する関数の例
def get_all_logins():
    return db.session.query(Login).all()  

def get_all_Checkpoint():
    return db.session.query(Checkpoint).all()  

def get_all_Quiz():
    return db.session.query(Quiz).all()  

def get_all_Quiz_Response():
    return db.session.query(Quiz_Response).all()  

def get_all_Stamp():
    return db.session.query(Stamp).all()  

def get_all_Survey():
    return db.session.query(Survey).all()  

def get_all_Survey_Choice():
    return db.session.query(Survey_Choice).all()  

def get_all_Survey_Response():
    return db.session.query(Survey_Response).all() 

@app.route('/logins', methods=['GET'])
def show_logins():
    try:
        logins = get_all_logins()
        output = '<h1>ログイン情報</h1><ul>'
        for login in logins:
           output += f'<li>ID: {login.id}, アカウント: {login.account}</li>'
        output += '</ul><br><a href="/">Back</a>'
        return output
    except Exception as e:
        return f'<h1>エラーが発生しました</h1><p>{str(e)}</p>'

#全てのルートからのルーティング　　flask 画像　表示staticフォルダーで表示
@app.route('/')
def hello():
    output='''
<h1>Hello World</h1>
<ul>
<li><a href="/next1">メニュー１</a>
<li><a href="/next2">メニュー２</a>
<li><a href="/next3">メニュー３</a>
<li><a href="/table">テーブル</a>
<li><a href="/enq/ljalkjsdf">アンケート1</a>
<li><a href="/enq/klsjklsdf">アンケート2</a>
<li><a href="/login">ログイン</a>
<li><a href="/loginexample">ログイン例</a>
<li><a href="/logins">ログイン情報</a></li>
</ul>
'''
    return output

# ... 既存のコード ...
@app.route('/login', methods=['GET', 'POST'])  # GETとPOSTの両方を受け取るように修正
def login():
    if request.method == 'POST':
        login_id = request.form.get("loginId")
        user = authenticate_user(login_id)  # サービス層の関数を呼び出す

        if user:
            output = f'''
            <h1>ログイン成功</h1>
            <p>ユーザーID: {user[0]}</p>
            <p>ログイン日時: {user[1]}</p>
            <p>使用状況: {'使用済み' if user[2] else '未使用'}</p>
            <br>
            <a href="/">Back</a>
            '''
        else:
            output = '''
            <h1>ログイン失敗</h1>
            <p>ユーザーIDが見つかりません。</p>
            <br>
            <a href="/">Back</a>
            '''
        
        return output
    else:
        return render_template('login.html')  # GETリクエストの場合はログインページを表示

# ... 既存のコード ...

@app.route('/next1')
def next1():
    output='''
Next1
<br>
<a href="/">Back</a>
'''
    return output
#ログイン画面
@app.route('/loginexample', methods=['POST'])
def login_example():
    login_id = request.form.get("loginId")
    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USER WHERE loginId = ?', (login_id,))
        user = cursor.fetchone()

    if user:
        output = f'''
        <h1>ログイン成功</h1>
        <p>ユーザーID: {user[0]}</p>
        <p>ログイン日時: {user[1]}</p>
        <p>使用状況: {'使用済み' if user[2] else '未使用'}</p>
        <br>
        <a href="/">Back</a>
        '''
    else:
        output = '''
        <h1>ログイン失敗</h1>
        <p>ユーザーIDが見つかりません。</p>
        <br>
        <a href="/">Back</a>
        '''
    
    return output

@app.route('/next2')
def next2():
    output='''
Next1
<br>
<a href="/">Back</a>
'''
    return output

@app.route('/next3')
def next3():
    output='''
Next1
<br>
<a href="/">Back</a>
'''
    return output

@app.route('/table')
def table():
    output=''
    with sqlite3.connect('data.db')as conn:
        df = pd.read_sql_query('SELECT * FROM USER',conn)
        output = df.to_html()
    output+='''
<br>Next1
<br>
<a href="/">Back</a>
'''
    return output
#アンケートとボタン作成
enquirely = {
    "ljalkjsdf":("エコポイントとはなんですか？", "回答１", "回答2"),
    "klsjklsdf":("エコな行動は", "水を再利用", "水を捨てる")
}
#上と一緒にルーティングの変数にしてしまう。backでルートに戻る。　インプットでボタンと数字を入れてる。
#form actionで次に飛ばす。keyはルーティングで求められている。nameは必要。CSVから読み込むのもあり。不正解の際はもう１回表示する。
@app.route('/enq/<key>')
def enq(key):
    output=f'''
    {enquirely[key][0]}
<br>
<form action="/ans/{key}" method="POST">
<input type="radio" name="answer" value="1">{enquirely[key][1]}
<input type="radio" name="answer" value="2">{enquirely[key][2]}
<input type="submit">
</form>
<br>
<a href="/">Back</a>
'''
    return output
#回答ans　ルーティングから行ってる。HTTPから受け取るときは文字列だからintにしている。
@app.route('/ans/<key>',methods=["POST"])#ansという関数を使って回答を作る。GETとPOSTを基本使うreturnの前にレスポンスを保存する。
def ans(key):
    ret = request.form.get("answer")
    answer = enquirely[key][int(ret)]
    output=f'''
回答は、{answer}でした。
<br>
<a href="/">Back</a>
'''
    
    return output
@app.route('/user/<int:id>')
def user(id):
    output=''
    with sqlite3.connect('data.db')as conn:
        df = pd.read_sql('SELECT * FROM USER WHERE id=?',conn,params=[id])
        output = df.to_html()
    output+='''
<br>Next1
<br>
<a href="/">Back</a>
'''
    return output
