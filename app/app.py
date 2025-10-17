from flask import Flask, request, render_template, flash, url_for, session, redirect, jsonify
from werkzeug.routing import BuildError
import sqlite3
from datetime import datetime, timedelta
import pytz
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from init import db, initialize_db, Login, Checkpoint, Quiz, Quiz_Response, Stamp, Survey, Survey_Choice, Survey_Response 
from services.user_service import authenticate_user
#from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
#from flask_wtf import CSRFProtect
from functools import wraps
import os
from sqlalchemy import func, and_,exists
import csv
from io import StringIO  
from flask import send_file
from flask import make_response
from collections import defaultdict

#以下をpipインストールしてください。
#pip install Flask-Login
#pip install Flask-WTF


#フォルダの下に写真を入れる。
# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # ここにユニークで秘密のキーを設定

initialize_db(app)
# グローバル変数でセッションクリアフラグを管理
_session_cleared = False
###ここでコメントアウトで無効化。
@app.before_request
def clear_session():
    global _session_cleared
    if not _session_cleared:
        session.clear()
        _session_cleared = True
        print("アプリケーション起動時のセッションをクリアしました。")
###
# アプリケーションのテーブルにアクセスした後にセッションを閉じるための teardown_appcontext ハンドラを追加
@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception:  # 例外が発生した場合の処理を追加
        print(f"エラーが発生しました: {exception}")  # エラーログを出力
    db.session.remove()  # リクエストコンテキスト終了時にセッションを閉じる

#------------------------------------------------以上はセットアップ----------------------------------------------------------


#どのページでもGETが基本で、絶対に受けないといけない。

#全てのルートからのルーティング　　flask 画像　表示staticフォルダーで表示
#ハッシュ化も要るかも。
#エンドポイント名と関数名が一致は必須事項。一応カスタムはできる。
#ログインしてからチェックポイントのテストをしないと正常に動かない。
#全てのもので選択肢に答えないとアクティブにさせない操作がいる。
#先に出ているエラーを直そう。
#更新でデータが挿入されてしまうかも。
#ユーザーのアカウント名表示は要るかも。
#なんか正解バグしてる
#SURVEY_CHOICEを設定しない問題を作っておけば選択肢のない問題が作れて、見出しになって２階層になるのでは？？
#これ管理画面もかな、ログインテーブルのフラグ操作チェックポイントのフラグ操作とアンケートとクイズ一覧を見る。
#アンケートとクイズの質問も管理画面から見れた方がいいかなあ。べた付パスワードで。
#ゴール画面が質素、かなぁ。。
#スタンプテーブルのダウンロード
#スタンプ管理でSTAMPテーブルの検索と表示数をページネーションする。
#クイズ管理にアンケート管理とページネーション、同じ機能を追加する。
#小数点以下をクイズで正しく表示できるようにする。あと、オリジナルグラフの検索、フィルター機能、始めは〇で色が変わるとかだといいなぁ。
#べた付パスワード
#現地にいる証を押すもの。QRコードをランダムで変えないといけない。Berealとか。どのような人がやるのか。
#これまでの事を知り、傾向を知って、自分たちが０から作るのではなく、ここの価値を変えて提供する。
#デジタルをやる人は、アナログの良いこと、原始的ないいことを現在までの進化として、ターゲットはどんな人がやっているのか。今のと何が違うのか。
#ストーリーとして語れるようにする。
#根本的に人の所在を判定するのを確認する価値
# #価値のチェンジを可能にする。
# QRコードを動的に動かしたり、ユーザーごとにリンクを変えられなけば
#経路が欲しい。スポットの近くに何があるか。遅いとこ違う線にする。フロントエンドで右側を図にする。大元のメニュー、カーサーにあるような。検索を左に。自分に分かる、
#２年後の自分にもわかるような。最大値を出せるのはいいこと。
#エラー検知で、ユーザーがリグインできなかったときに通知を飛ばして対応する。答えが分からないのでエラーを出したユーザーを確認する機能。
#ログイン管理の直下にエラーが出たユーザーを確認する。いつエラーが出たか。相手にエラー解消を。
#テストプレイで耐えるか。
#ちょっと画像いじるか。
#テーブル初期化機能…まあ基本要らんな。
#ゴール地点にQRコードを置いておく。STAMPを確認してSTAMPを取得したのにできなかった報告ボタンは,,,正直ムズイ。位置情報の他、確認クイズとかだけど、そこはめんどいな・・・
#アンケートと訪問記録が保存されました。
#正解です！、、、この二つはflash受けるようにしなきゃな。。。


#1.8特定のフラグで出たエラーを検知して、まだログインできなかった場合はこちらを押してください。で再度エラー確認。すべてのポイントで。
#管理者側からユーザー側に返す、ログインでは初期のフラッシュメッセージから上書きしていく形だからフラッシュメッセージでそれは可能。
#対応するエラーはアカウントがあっていたのにログインできない状態、ゴールアンケートに答えられない状態の事に絞る。
#リストでエラーが出た、またはボタンを押しているユーザーを助ける。ボタンを押したら、数秒待って再度QRコードを読み込んでくださいと表示する。
#1.7操作したいのはユーザーのログインステータスとSTAMPの二つ。STAMPの場合、特にクイズのレスポンスを見る必要がある。全てのクイズに答えていたかを確認し、STAMP追加の処置を取る。
#実際にエラー対応したユーザーと内容と時間を保存できるテーブルを管理画面のアンケート管理の上あたりに作るか。
#1.6管理画面の一定時間、自動リロードがあればいいなぁ。やりすぎたら機能が使えないので、止めるボタンを作るか動的にするか、どこかの機能までを自動で行いたいものだな。
#1.5肝心のスポット紹介、軽めのやつと長めのやつがいるわ。
#軽めのlogin.htmlはこのコードの中でやって、長めはスタンプカードから出し渋ることで実現しよう。
#スタンプカードの詳細ボタンを作り、ルーティングからチェックポイントIDでハンドリングして、HTMLのハンドリングでもする。
#２．１で〇をデフォルトで表示しようか。
#２には、獲得しているスタンプの地点とクイズレスポンスのIDが一致しているかどうか。
#２．２と２．３に関してはコピペ。
#２．５も少しルート追加して処理を受け継がせる必要があるが、まあ少し時間はかかるな。一番はエラー処理だ。
#２．６スタンプ獲得ページ、かなぁ。まあ要らんよなあ。。stamp_added'
#1.9is_usedのフラグを少し変えて弾くようにして、こちらで払い出しテーブルを作る。要らんな。
#1.7と1.8が必要なかったら、もう２の最終盤くらいの位置づけになるね。
#GETでリロードした際に、全員その条件で検索する！
#複数Sqlite3と、DBのセッション終了をする。
#アップデートと削除は書き込み。

#======================
#最新のスタンプのみのクイズ不一致エラーの機能になってしまっているのでスタンプの情報が一つしかないものは特定できず、最新のもの以外で特定可能な機能になった。
#テーブルの変更なしだとこれが限界だ。
#========================



#このはい、いいえを答えたらそのフラグをテーブルに時間と共に保存！
#エラー対応テーブルもあるよ。


# 変更点uchida
    # hash化
    # /admin　link
    # admin関連のroute hash
    # 


# 変更点uchida
checkpoint_hash_dic = {'ajrwkhlkafsddfd': 1,
                       'syflwdehkejhrsd': 2, 
                       'hgosmcbgdirmagf': 3, 
                       'hocnhsmtgdobmjg': 4, 
                       'bginchrfmhodhlk': 5, 
                       'nhkbhditmfobhhj': 6, 
                       'gkfcnshvmfjhpdj': 7, 
                       'afsjfnvidngmcjx': 8, 
                       'hhkncfouvmiwoxz': 9,
                       'hsadhfuoewhfowo': 10,
                       'njrghoiernvhewo': 11,
                       'vbgfksghdjfjdkg': 12,
                       'bhgfkdehdikvgfh': 13, #管理画面
                       'vgkfeawigeaoggk': 14,#ゴール地点
                       'sflasajdfoiahks': 15, 
                       'dsasdfasdgxccva': 16, 
                       'ahgjdjegndsrths': 17, 
                       'kiurdshfgfhjesr': 18,
                       'ryukdmghdnsfdae': 19,
                       'naeyrhnghmgjtye': 20,
                       'ryuitukydsawqsg': 21,
                       'dsafgahtndaasdf': 22, 
                       'dsghsrhn5racfdg': 23, 
                       'ahrsaewehrsbaab': 24, 
                       'adfghakljmgegfx': 25,
                       'rategaehrj6hnra': 26,
                       'sadghrjemnsneag': 27,
                       'sagehjdnsegaarg': 28,
                       'adsfasljadsfjow': 29, 
                       'safdahjsfjgcstg': 30, 
                       'afgdhfsjkf4hxys': 31, 
                       'utyliugddsrreaz': 32,
                       'warteytsurydknc': 33,
                       '45srxcgssxfhjmh': 34,
                       'ystdk7cgndtkbnx': 35,
                       'se4rdcjtkvhfniu': 36, 
                       'lf8trdxgxnymtcx': 37, 
                       'zgdhfxfjkfl7fyc': 38, 
                       'vcmhbvtjhulygfd': 39,
                       '4erxcgkbnvczdhj': 40,
                       'ghmdfhsjsdxfaah': 41,
                       'kufdtrhdfghkycf': 42,
                       'seryrkvbnvcwzex': 43, 
                       'rdturikfcgfxezz': 44, 
                       'wzexklikjnmvcxx': 45, 
                       'dfjgkfvgcxgrxdh': 46,
                       'mnvvmdtrxdfhzha': 47,
                       'waesrgvkhjbnvxd': 48,
                       'hjkvhlbcnvxexdz': 49,
                       'bnvtredseryhgah': 50, 
                       'gfjdrxtfhvcudcr': 51, 
                       'iuslhkdafnauilw': 52, 
                       'pulisjagghfnwui': 53,
                       'laiuhkjnfmassdf': 54,
                       'liajkfhfadsfhkz': 55,
                       'ladhhtafodipgzp': 56,
                       'gulaeirhsjkgpaw': 57, 
                       'ouilaluehzhlfia': 58, 
                       'ouasilfhfazsfuz': 59, 
                       'pawehfmjxzhiuyw': 60,
                       'osfyauipwzhsdfy': 61,
                       'woituxzjlwemaop': 62,
                       'paurexuffgaelek': 63,
                       'puesljxkzufieow': 64, 
                       'ouidaaolwszjfue': 65, 
                       'pfaiuwezsozixld': 66,
                       'zseurlezsjdfoww': 67,
                       'fdsatgaetgfjydt': 68,  
                       }
hash_keys = list(checkpoint_hash_dic.keys())
print("len(hash_keys):", len(hash_keys))
print("=== DEBUG ===")
print("len(hash_keys):", len(hash_keys))
print("hash_keys:", hash_keys)
print(len(hash_keys))


@app.route("/")
def index():
    keys = globals().get("hash_keys") or []
    if isinstance(keys, (list, tuple)) and keys:
        first_key = keys[0]
        # ← ここを唯一・正しい引数名に
        return redirect(url_for("handle_checkpoint", checkpoint_id_hash=first_key))
    # キーがない場合に 500 にならないよう安全に返す
    return ("Entry route is not ready. Try /handle_checkpoint/<checkpoint_id_hash>.", 404)


# 変更点uchida
# 短大-幼児教育学科ブースのアンケートが感情になる
# 短大-調理コースブース以下アンケート未実施
# メイン会場ブースアンケートがゴールアンケートとなっている
@app.route('/admin')
def hello():
    output=f'''
<h1>Hello World</h1>
<ul>
<li><a href="/handle_checkpoint/{hash_keys[0]}">スタートログイン</a></li>
<li><a href="/handle_checkpoint/{hash_keys[1]}">経営学部ブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[2]}">国際観光学部ブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[3]}">経済学部ブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[4]}">教育学部ブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[5]}">芸術学部ブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[6]}">データサイエンス学部ブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[7]}">芸術学部ブース</a></li> 
<li><a href="/handle_checkpoint/{hash_keys[8]}">短大-幼児教育学科ブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[9]}">短大-調理コースブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[10]}">短大-製菓コースブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[11]}">短大-栄養学科ブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[12]}">短大-生活デザイン学科ブース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[13]}">10/18 大学を知ろう</a></li>
<li><a href="/handle_checkpoint/{hash_keys[14]}">10/18 経営学部食ビジネスコース</a></li>
<li><a href="/handle_checkpoint/{hash_keys[15]}">10/18 学生トーク1</a></li>
<li><a href="/handle_checkpoint/{hash_keys[16]}">10/18 フットサル部</a></li>
<li><a href="/handle_checkpoint/{hash_keys[17]}">10/18 学生トーク2</a></li>
<li><a href="/handle_checkpoint/{hash_keys[18]}">10/18 eスポーツ</a></li>
<li><a href="/handle_checkpoint/{hash_keys[19]}">10/18 学生トーク3</a></li>
<li><a href="/handle_checkpoint/{hash_keys[20]}">10/18 ストリートダンスサークル</a></li> 
<li><a href="/handle_checkpoint/{hash_keys[21]}">10/18 将来構想について</a></li>
<li><a href="/handle_checkpoint/{hash_keys[22]}">10/18 チアダンス部</a></li>
<li><a href="/handle_checkpoint/{hash_keys[23]}">10/18 学生トーク4</a></li>
<li><a href="/handle_checkpoint/{hash_keys[24]}">10/18 芸術学部有志</a></li>
<li><a href="/handle_checkpoint/{hash_keys[25]}">10/18 入試制度について</a></li>
<li><a href="/handle_checkpoint/{hash_keys[26]}">10/18 データサイエンス学部学生起業</a></li>
<li><a href="/handle_checkpoint/{hash_keys[27]}">10/18 大学を知ろう</a></li>
<li><a href="/handle_checkpoint/{hash_keys[28]}">10/18 吹奏楽部</a></li>
<li><a href="/handle_checkpoint/{hash_keys[29]}">10/18 学生トーク1</a></li>
<li><a href="/handle_checkpoint/{hash_keys[30]}">10/18 せいけいデジタルサークル</a></li>
<li><a href="/handle_checkpoint/{hash_keys[31]}">10/18 学生トーク2</a></li>
<li><a href="/handle_checkpoint/{hash_keys[32]}">10/18 芸術学部有志</a></li>
<li><a href="/handle_checkpoint/{hash_keys[33]}">10/18 学生トーク3</a></li> 
<li><a href="/handle_checkpoint/{hash_keys[34]}">10/18 k-pop</a></li>
<li><a href="/handle_checkpoint/{hash_keys[35]}">10/18 将来構想について</a></li>
<li><a href="/handle_checkpoint/{hash_keys[36]}">10/18 コーラス部</a></li>
<li><a href="/handle_checkpoint/{hash_keys[37]}">10/18 学生トーク4</a></li>
<li><a href="/handle_checkpoint/{hash_keys[38]}">10/18 チアダンス部</a></li>
<li><a href="/handle_checkpoint/{hash_keys[39]}">10/18 入試制度について</a></li>
<li><a href="/handle_checkpoint/{hash_keys[40]}">10/19 大学を知ろう</a></li>
<li><a href="/handle_checkpoint/{hash_keys[41]}">10/19 軽音楽部</a></li>
<li><a href="/handle_checkpoint/{hash_keys[42]}">10/19 学生トーク1</a></li>
<li><a href="/handle_checkpoint/{hash_keys[43]}">10/19 ギター</a></li>
<li><a href="/handle_checkpoint/{hash_keys[44]}">10/19 学生トーク2</a></li>
<li><a href="/handle_checkpoint/{hash_keys[45]}">10/19 サッカー部</a></li>
<li><a href="/handle_checkpoint/{hash_keys[46]}">10/19 学生トーク3</a></li> 
<li><a href="/handle_checkpoint/{hash_keys[47]}">10/19 アニメ製作サークル</a></li>
<li><a href="/handle_checkpoint/{hash_keys[48]}">10/19 将来構想について</a></li>
<li><a href="/handle_checkpoint/{hash_keys[49]}">10/19 ストリートダンス</a></li>
<li><a href="/handle_checkpoint/{hash_keys[50]}">10/19 学生トーク4</a></li>
<li><a href="/handle_checkpoint/{hash_keys[51]}">10/19 チアダンス部</a></li>
<li><a href="/handle_checkpoint/{hash_keys[52]}">10/19 入試制度について</a></li>
<li><a href="/handle_checkpoint/{hash_keys[53]}">10/19 データサイエンス学部学生起業</a></li>
<li><a href="/handle_checkpoint/{hash_keys[54]}">10/19 大学を知ろう</a></li>
<li><a href="/handle_checkpoint/{hash_keys[55]}">10/19 芸術学部有志</a></li>
<li><a href="/handle_checkpoint/{hash_keys[56]}">10/19 学生トーク1</a></li>
<li><a href="/handle_checkpoint/{hash_keys[57]}">10/19 アニメ制作サークル</a></li>
<li><a href="/handle_checkpoint/{hash_keys[58]}">10/19 学生トーク2</a></li>
<li><a href="/handle_checkpoint/{hash_keys[59]}">10/19 準硬式野球部</a></li> 
<li><a href="/handle_checkpoint/{hash_keys[60]}">10/19 学生トーク3</a></li>
<li><a href="/handle_checkpoint/{hash_keys[61]}">10/19 チアダンス部</a></li>
<li><a href="/handle_checkpoint/{hash_keys[62]}">10/19 将来構想について</a></li>
<li><a href="/handle_checkpoint/{hash_keys[63]}">10/19 せいけいデジタルサークル</a></li>
<li><a href="/handle_checkpoint/{hash_keys[64]}">10/19 学生トーク4</a></li>
<li><a href="/handle_checkpoint/{hash_keys[65]}">10/19 お琴サークル</a></li>
<li><a href="/handle_checkpoint/{hash_keys[66]}">10/19 入試制度について</a></li>
<li><a href="/{hash_keys[13]}">管理画面</a></li>
</ul>
'''
    return output


def save_mismatch_error(user_id, account, mismatched_checkpoints):
    """エラー情報をセッションに保存する改善版"""
    if 'mismatch_errors' not in session:
        session['mismatch_errors'] = []

    # セッション内の現在のエラー情報を取得
    current_errors = session['mismatch_errors']
    
    # 既存のエラー情報を探す
    existing_error = None
    for error in current_errors:
        if error['user_id'] == user_id:
            existing_error = error
            break
    
    if existing_error:
        # 既存のチェックポイント情報を分割してリストにする
        existing_checkpoints = set(cp.strip() for cp in existing_error['mismatched_checkpoints'].split(','))
        # 新しいチェックポイントを追加
        existing_checkpoints.add(mismatched_checkpoints.strip())
        # 更新された情報を保存
        existing_error['mismatched_checkpoints'] = ', '.join(sorted(existing_checkpoints))
    else:
        # 新しいエラー情報を追加
        current_errors.append({
            'user_id': user_id,
            'account': account,
            'mismatched_checkpoints': mismatched_checkpoints
        })
    
    # セッションを明示的に更新
    session.modified = True

def remove_resolved_checkpoint(user_id, checkpoint_name):
    """解決されたチェックポイントをエラーリストから削除"""
    if 'mismatch_errors' not in session:
        return
    
    current_errors = session['mismatch_errors']
    for error in current_errors:
        if error['user_id'] == user_id:
            checkpoints = [cp.strip() for cp in error['mismatched_checkpoints'].split(',')]
            if checkpoint_name in checkpoints:
                checkpoints.remove(checkpoint_name)
                if checkpoints:  # まだ他のエラーが残っている場合
                    error['mismatched_checkpoints'] = ', '.join(checkpoints)
                else:  # すべてのエラーが解決された場合
                    current_errors.remove(error)
            break
    
    session['mismatch_errors'] = current_errors
    session.modified = True


# 管理画面
# 管理画面のメインページ
@app.route(f'/{hash_keys[13]}')
def admin_panel():
    #ログイン管理
    # ページネーションのパラメータを取得
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 1ページあたりの表示数
    search_query = request.args.get('search', '')

    # ユーザー検索クエリの構築
    user_query = Login.query
    if search_query:
        user_query = user_query.filter(Login.account.like(f'%{search_query}%'))
    
    # ログイン管理のページネーション適用
    users_pagination = user_query.order_by(Login.id).paginate(
        page=page, 
        per_page=per_page,
        error_out=False
    )

    # スタンプ管理のページネーションと検索
    stamp_page = request.args.get('stamp_page', 1, type=int)
    stamp_per_page = 10
    stamp_search = request.args.get('stamp_search', '')

    # スタンプ検索クエリの構築
    stamp_query = db.session.query(
        Stamp,
        Login.account.label('user_account'),
        Checkpoint.name.label('checkpoint_name'),
        Checkpoint.checkpoint_type
    ).join(
        Login, Stamp.login_id == Login.id
    ).join(
        Checkpoint, Stamp.checkpoint_id == Checkpoint.id
    )

    # 検索条件を適用
    if stamp_search:
        stamp_query = stamp_query.filter(
            Login.account.like(f'%{stamp_search}%')
        )

    # スタンプ管理のページネーション適用
    stamps_pagination = stamp_query.order_by(
        Stamp.created_at.desc()
    ).paginate(
        page=stamp_page,
        per_page=stamp_per_page,
        error_out=False
    )

    # スタンプデータの取得を追加
    #stamps = stamp_query.order_by(Stamp.created_at.desc()).limit(200).all()

    # スタンプデータを整形
    formatted_stamps = [
        {
            'id': stamp.id,
            'user_account': user_account,
            'checkpoint_name': checkpoint_name,
            'checkpoint_type': checkpoint_type,
            'created_at': stamp.created_at
        }
        for stamp, user_account, checkpoint_name, checkpoint_type in stamps_pagination.items
    ]

    # チェックポイントデータの取得
    checkpoints = Checkpoint.query.order_by(Checkpoint.checkpoint_order).all()
    
    # アンケートデータの取得
    surveys = db.session.query(
        Survey, 
        Checkpoint.name.label('checkpoint_name')
    ).join(
        Checkpoint
    ).order_by(
        Survey.checkpoint_id, 
        Survey.survey_order
    ).all()

    # アンケート検索クエリの構築
    survey_query = db.session.query(
        Survey, 
        Checkpoint.name.label('checkpoint_name')
    ).join(
        Checkpoint
    )

    # アンケート管理のページネーションと検索
    survey_page = request.args.get('survey_page', 1, type=int)
    survey_per_page = 10
    survey_search = request.args.get('survey_search', '')

    if survey_search:
        survey_query = survey_query.filter(
            db.or_(
                Survey.question.like(f'%{survey_search}%'),
                Checkpoint.name.like(f'%{survey_search}%')
            )
        )

    # ページネーション適用
    surveys_pagination = survey_query.order_by(
        Survey.checkpoint_id, 
        Survey.survey_order
    ).paginate(
        page=survey_page,
        per_page=survey_per_page,
        error_out=False
    )

    # アンケート選択肢の取得
    survey_choices = {}
    for survey, _ in surveys:
        choices = Survey_Choice.query.filter_by(survey_id=survey.id).all()
        survey_choices[survey.id] = choices
    
    # クイズデータの取得
    quizzes = db.session.query(
        Quiz,
        Checkpoint.name.label('checkpoint_name')
    ).join(
        Checkpoint
    ).order_by(
        Quiz.checkpoint_id,
        Quiz.quiz_order
    ).all()
    
    # クイズ管理のページネーションと検索
    quiz_page = request.args.get('quiz_page', 1, type=int)
    quiz_per_page = 10
    quiz_search = request.args.get('quiz_search', '')

    # クイズ検索クエリの構築
    quiz_query = db.session.query(
        Quiz,
        Checkpoint.name.label('checkpoint_name')
    ).join(
        Checkpoint
    )

    if quiz_search:
        quiz_query = quiz_query.filter(
            db.or_(
                Quiz.content.like(f'%{quiz_search}%'),
                Checkpoint.name.like(f'%{quiz_search}%')
            )
        )

    # ページネーション適用
    quizzes_pagination = quiz_query.order_by(
        Quiz.checkpoint_id,
        Quiz.quiz_order
    ).paginate(
        page=quiz_page,
        per_page=quiz_per_page,
        error_out=False
    )

    # クイズレスポンスのページネーションと検索
    quiz_response_page = request.args.get('quiz_response_page', 1, type=int)
    quiz_response_per_page = 10
    quiz_response_search = request.args.get('quiz_response_search', '')

    # クイズレスポンス検索クエリの構築
    quiz_response_query = db.session.query(
        Quiz_Response,
        Login.account.label('user_account'),
        Quiz.content.label('quiz_content'),
        Checkpoint.name.label('checkpoint_name')
    ).join(
        Login, Quiz_Response.login_id == Login.id
    ).join(
        Quiz, Quiz_Response.quiz_id == Quiz.id
    ).join(
        Checkpoint, Quiz.checkpoint_id == Checkpoint.id
    )

    if quiz_response_search:
        quiz_response_query = quiz_response_query.filter(
            db.or_(
                Login.account.like(f'%{quiz_response_search}%'),
                Quiz.content.like(f'%{quiz_response_search}%'),
                Checkpoint.name.like(f'%{quiz_response_search}%')
            )
        )

    quiz_responses_pagination = quiz_response_query.order_by(
        Quiz_Response.created_at.desc()
    ).paginate(
        page=quiz_response_page,
        per_page=quiz_response_per_page,
        error_out=False
    )

    # アンケートレスポンスのページネーションと検索
    survey_response_page = request.args.get('survey_response_page', 1, type=int)
    survey_response_per_page = 10
    survey_response_search = request.args.get('survey_response_search', '')

    # アンケートレスポンス検索クエリの構築
    survey_response_query = db.session.query(
        Survey_Response,
        Login.account.label('user_account'),
        Survey.question.label('survey_question'),
        Checkpoint.name.label('checkpoint_name')
    ).join(
        Login, Survey_Response.login_id == Login.id
    ).join(
        Survey, Survey_Response.survey_id == Survey.id
    ).join(
        Checkpoint, Survey.checkpoint_id == Checkpoint.id
    )

    if survey_response_search:
        survey_response_query = survey_response_query.filter(
            db.or_(
                Login.account.like(f'%{survey_response_search}%'),
                Survey.question.like(f'%{survey_response_search}%'),
                Checkpoint.name.like(f'%{survey_response_search}%')
            )
        )

    survey_responses_pagination = survey_response_query.order_by(
        Survey_Response.created_at.desc()
    ).paginate(
        page=survey_response_page,
        per_page=survey_response_per_page,
        error_out=False
    )

# スタンプを獲得したがクイズに回答していないユーザーを検出
    stamp_without_quiz_users = (
        db.session.query(
            Login.id.label('user_id'),
            Login.account, 
            Checkpoint.name.label('mismatched_checkpoints')
        )
        .select_from(Login)
        .join(Stamp, Login.id == Stamp.login_id)
        .join(Checkpoint, Stamp.checkpoint_id == Checkpoint.id)
        .outerjoin(Quiz, Checkpoint.id == Quiz.checkpoint_id)
        .outerjoin(Quiz_Response, and_(Login.id == Quiz_Response.login_id, Quiz.id == Quiz_Response.quiz_id))
        .filter(
            Quiz_Response.id.is_(None),
            Checkpoint.checkpoint_type == 'normal'  # normalタイプのチェックポイントのみ
        )
        .group_by(Login.id, Login.account, Checkpoint.id)
        .all()
    )
    print(stamp_without_quiz_users)

    # クイズ不一致エラーが発生した際に、エラー情報を保存する
    # クイズ不一致エラーが発生した際に、エラー情報を保存する
    #def save_mismatch_error(user_id, account, mismatched_checkpoints):


    # クイズレスポンスとスタンプの不一致を検出
    mismatch_users = (
        db.session.query(
            Login.id.label('user_id'),
            Login.account,
            Checkpoint.name.label('mismatched_checkpoints')
        )
        .select_from(Login)
        .join(Quiz_Response, Login.id == Quiz_Response.login_id)
        .join(Quiz, Quiz_Response.quiz_id == Quiz.id)
        .join(Checkpoint, Quiz.checkpoint_id == Checkpoint.id)
        .outerjoin(Stamp, and_(Login.id == Stamp.login_id, Checkpoint.id == Stamp.checkpoint_id))
        .filter(Stamp.id.is_(None), Quiz_Response.is_corrected == True)
        .group_by(Login.id, Login.account, Checkpoint.id)
        .all()
    )

    # 検出された不一致情報をセッション変数に保存
    for user in mismatch_users:
        save_mismatch_error(user.user_id, user.account, user.mismatched_checkpoints)

    # エラー対応スタンプのデータを取得
    error_stamp_page = request.args.get('error_stamp_page', 1, type=int)
    error_stamp_search = request.args.get('error_stamp_search', '')

    # セッション変数からエラー情報を取得
    error_stamp_data = session.get('mismatch_errors', [])

    # error_stamp_dataを渡して呼び出し
    error_stamps_pagination = get_error_resolution_stamps(
        page=error_stamp_page,
        search_query=error_stamp_search,
        mismatch_data=error_stamp_data  # error_stamp_dataを渡す
    )

    return render_template(
        'admin/panel.html',
        users_pagination=users_pagination,
        checkpoints=checkpoints,
        surveys_pagination=surveys_pagination,  # surveysをsurveys_paginationに変更
        survey_choices=survey_choices,
        quizzes=quizzes,
        admin_hash=hash_keys[13],
        search_query=search_query,
        stamps=formatted_stamps,
        stamps_pagination=stamps_pagination,
        survey_search=survey_search,
        quizzes_pagination=quizzes_pagination,
        quiz_search=quiz_search,  # 検索クエリを渡す
        quiz_responses_pagination=quiz_responses_pagination,
        survey_responses_pagination=survey_responses_pagination,
        quiz_response_search=quiz_response_search,
        survey_response_search=survey_response_search,
        mismatch_users=mismatch_users,
        stamp_without_quiz_users=stamp_without_quiz_users,
        error_stamps_pagination=error_stamps_pagination,
        error_stamp_search=error_stamp_search
    )

# クイズ追加のAPI
@app.route(f'/{hash_keys[13]}/add_quiz', methods=['POST'])
def add_quiz():
    try:
        checkpoint_id = request.form.get('checkpoint_id')
        quiz_order = request.form.get('quiz_order')
        content = request.form.get('content')
        answer_1 = request.form.get('answer_1')
        answer_2 = request.form.get('answer_2')
        answer_3 = request.form.get('answer_3')
        correct_option = request.form.get('correct')

        if not all([checkpoint_id, quiz_order, content, answer_1, answer_2, answer_3, correct_option]):
            return jsonify({'error': 'Missing required fields'}), 400

        # 選択された正解オプションに基づいて実際の正解文字列を設定
        correct_answers = {
            'answer_1': answer_1,
            'answer_2': answer_2,
            'answer_3': answer_3
        }
        correct = correct_answers.get(correct_option)

        if not correct:
            return jsonify({'error': 'Invalid correct answer selection'}), 400

        new_quiz = Quiz(
            checkpoint_id=checkpoint_id,
            quiz_order=float(quiz_order),
            content=content,
            answer_1=answer_1,
            answer_2=answer_2,
            answer_3=answer_3,
            correct=correct
        )
        
        db.session.add(new_quiz)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Quiz added successfully',
            'quiz_id': new_quiz.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# クイズ削除のAPI
@app.route(f'/{hash_keys[13]}/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    try:
        # まず対象のクイズが存在するか確認
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # トランザクションの開始
        db.session.begin_nested()  # セーブポイントを作成
        
        try:
            # 関連する回答を削除
            deleted_responses = Quiz_Response.query.filter_by(quiz_id=quiz_id).delete()
            
            # クイズを削除
            db.session.delete(quiz)
            
            # トランザクションをコミット
            db.session.commit()
            
            # ログ出力を追加
            print(f"Quiz {quiz_id} and {deleted_responses} responses deleted successfully")

            return jsonify({
                'success': True,
                'message': 'クイズと関連する回答が正常に削除されました',
                'deletedResponses': deleted_responses
            })

        except Exception as e:
            # 内部のトランザクションをロールバック
            db.session.rollback()
            raise e

    except Exception as e:
        # 外部のトランザクションをロールバック
        db.session.rollback()
        print(f"Error deleting quiz {quiz_id}: {str(e)}")  # より詳細なログ
        return jsonify({
            'success': False,
            'error': 'クイズの削除中にエラーが発生しました',
            'details': str(e)
        }), 500

# ログインフラグの更新API
@app.route(f'/{hash_keys[13]}/update_login', methods=['POST'])
def update_login_flag():
    login_id = request.form.get('login_id')
    flag_name = request.form.get('flag')
    
    if not login_id or not flag_name:
        return jsonify({'error': 'Missing parameters'}), 400
        
    user = Login.query.get_or_404(login_id)
    
    flags = ['is_used', 'is_loggedin', 'is_agree', 'is_ended']
    if flag_name not in flags:
        return jsonify({'error': 'Invalid flag name'}), 400
        
    setattr(user, flag_name, not getattr(user, flag_name))
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_value': getattr(user, flag_name)
    })

# チェックポイントタイプの更新API
@app.route(f'/{hash_keys[13]}/update_checkpoint', methods=['POST'])
def update_checkpoint_type():
    checkpoint_id = request.form.get('checkpoint_id')
    new_type = request.form.get('type')
    
    if not checkpoint_id or not new_type:
        return jsonify({'error': 'Missing parameters'}), 400
        
    checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
    
    if new_type not in ['normal', 'start', 'goal']:
        return jsonify({'error': 'Invalid checkpoint type'}), 400
        
    checkpoint.checkpoint_type = new_type
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_type': new_type
    })

# アンケート追加のAPIを修正
@app.route(f'/{hash_keys[13]}/add_survey', methods=['POST'])
def add_survey():
    try:
        checkpoint_id = request.form.get('checkpoint_id')
        question = request.form.get('question')
        survey_order = request.form.get('survey_order')
        has_choices = request.form.get('has_choices') == 'true'  # 選択肢の有無を確認
        
        if not all([checkpoint_id, question, survey_order]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # 新しいアンケートを作成
        new_survey = Survey(
            checkpoint_id=checkpoint_id,
            question=question,
            survey_order=float(survey_order)
        )
        db.session.add(new_survey)
        db.session.flush()  # IDを取得するためにflush
        
        # 選択肢がある場合のみ処理
        if has_choices:
            choices = request.form.getlist('choices[]')
            values = request.form.getlist('values[]')
            
            if len(choices) != len(values):
                return jsonify({'error': 'Choices and values must match'}), 400
                
            for choice, value in zip(choices, values):
                if choice.strip():  # 空の選択肢は無視
                    new_choice = Survey_Choice(
                        survey_id=new_survey.id,
                        survey_choice=choice,
                        value=int(value)
                    )
                    db.session.add(new_choice)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Survey added successfully',
            'survey_id': new_survey.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# アンケート削除のAPI
@app.route(f'/{hash_keys[13]}/delete_survey/<int:survey_id>', methods=['POST'])
def delete_survey(survey_id):
    try:
        # まず関連する回答を削除
        Survey_Response.query.filter_by(survey_id=survey_id).delete()
        
        # 関連する選択肢を削除
        Survey_Choice.query.filter_by(survey_id=survey_id).delete()
        
        # アンケート自体を削除
        survey = Survey.query.get_or_404(survey_id)
        db.session.delete(survey)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Survey deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

# スタンプ管理のための追加ルート

# ユーザー検索API
@app.route(f'/{hash_keys[13]}/search_users', methods=['GET'])
def search_users():
    search_query = request.args.get('query', '')
    if not search_query:
        return jsonify({'users': []})
        
    try:
        users = Login.query.filter(
            Login.account.like(f'%{search_query}%')
        ).limit(10).all()  # 最大10件まで表示
        
        users_data = [{
            'id': user.id,
            'account': user.account,
            'is_used': user.is_used,
            'is_loggedin': user.is_loggedin,
            'is_ended': user.is_ended
        } for user in users]
        
        return jsonify({'users': users_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# スタンプ記録の取得API
@app.route(f'/{hash_keys[13]}/get_stamps', methods=['GET'])
def get_stamps():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    try:
        stamps = db.session.query(
            Stamp,
            Login.account.label('user_account'),
            Checkpoint.name.label('checkpoint_name')
        ).join(
            Login, Stamp.login_id == Login.id
        ).join(
            Checkpoint, Stamp.checkpoint_id == Checkpoint.id
        ).filter(
            Stamp.login_id == user_id
        ).order_by(
            Stamp.created_at.desc()
        ).all()
        
        stamps_data = [{
            'id': stamp.Stamp.id,
            'user_account': stamp.user_account,
            'checkpoint_name': stamp.checkpoint_name,
            'created_at': stamp.Stamp.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for stamp in stamps]
        
        return jsonify({'stamps': stamps_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# スタンプ追加API
@app.route(f'/{hash_keys[13]}/add_stamp', methods=['POST'])
def add_stamp():
    try:
        login_id = request.form.get('login_id')
        checkpoint_id = request.form.get('checkpoint_id')
        
        if not all([login_id, checkpoint_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # 既存のスタンプをチェック
        existing_stamp = Stamp.query.filter_by(
            login_id=login_id,
            checkpoint_id=checkpoint_id
        ).first()
        
        if existing_stamp:
            return jsonify({'error': 'Stamp already exists'}), 400
        
        new_stamp = Stamp(
            login_id=login_id,
            checkpoint_id=checkpoint_id,
        #    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
        )
        
        db.session.add(new_stamp)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stamp added successfully',
            'stamp_id': new_stamp.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# スタンプ削除API
@app.route(f'/{hash_keys[13]}/delete_stamp/<int:stamp_id>', methods=['POST'])
def delete_stamp(stamp_id):
    try:
        stamp = Stamp.query.get_or_404(stamp_id)
        db.session.delete(stamp)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stamp deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
# app.pyに追加する関数
@app.route(f'/{hash_keys[13]}/error_resolution_stamps')
def get_error_resolution_stamps(page=1, search_query='', mismatch_data=None): 
    per_page = 10
  
    # 渡されたmismatch_dataを使用
    error_stamps_base = mismatch_data if mismatch_data is not None else []

    # 検索とページネーション用にリスト処理
    filtered_records = error_stamps_base
    if search_query:
        filtered_records = [
            record for record in error_stamps_base
            if search_query.lower() in record['account'].lower() or 
               search_query.lower() in record['mismatched_checkpoints'].lower()
        ]

    # 手動でページネーションを実装
    total = len(filtered_records)
    start = (page - 1) * per_page
    end = start + per_page
    items = filtered_records[start:end]

    class CustomPagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total

        @property
        def pages(self):
            return (self.total + self.per_page - 1) // self.per_page

        @property
        def has_prev(self):
            return self.page > 1

        @property
        def has_next(self):
            return self.page < self.pages

        @property
        def prev_num(self):
            return self.page - 1

        @property
        def next_num(self):
            return self.page + 1

        def iter_pages(self):
            return range(1, self.pages + 1)

    return CustomPagination(
        items=items,
        page=page,
        per_page=per_page,
        total=total
    )

# CSVエクスポート用の関数を追加
@app.route(f'/{hash_keys[13]}/export/<table_name>')
def export_csv(table_name):
    try:
        si = StringIO()
        writer = csv.writer(si)
        
        if table_name == 'stamps':
            # スタンプデータのエクスポート
            stamps = db.session.query(
                Stamp,
                Login.account.label('user_account'),
                Checkpoint.name.label('checkpoint_name'),
                Checkpoint.checkpoint_type
            ).join(
                Login, Stamp.login_id == Login.id
            ).join(
                Checkpoint, Stamp.checkpoint_id == Checkpoint.id
            ).order_by(
                Stamp.login_id,
                Checkpoint.checkpoint_order,
                Stamp.created_at
            ).all()
            
            writer.writerow([
                'スタンプID',
                'ユーザーID',
                'アカウント名',
                'チェックポイントID',
                'チェックポイント名',
                'チェックポイントタイプ',
                '取得日時'
            ])
            
            for stamp, user_account, checkpoint_name, checkpoint_type in stamps:
                writer.writerow([
                    stamp.id,
                    stamp.login_id,
                    user_account,
                    stamp.checkpoint_id,
                    checkpoint_name,
                    checkpoint_type,
                    stamp.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            filename = "stamps.csv"
            
        elif table_name == 'users':
            # ユーザーデータのエクスポート
            users = Login.query.all()
            writer.writerow(['ID', 'アカウント', '使用状態', 'ログイン状態', '同意状態', '終了状態', '発行日時'])
            for user in users:
                writer.writerow([
                    user.id,
                    user.account,
                    user.is_used,
                    user.is_loggedin,
                    user.is_agree,
                    user.is_ended,
                    user.issued_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            filename = "users.csv"
            
        elif table_name == 'checkpoints':
            # チェックポイントデータのエクスポート
            checkpoints = Checkpoint.query.order_by(Checkpoint.checkpoint_order).all()
            writer.writerow(['ID', '順序', '名前', '説明', 'タイプ'])
            for cp in checkpoints:
                writer.writerow([
                    cp.id,
                    cp.checkpoint_order,
                    cp.name,
                    cp.description,
                    cp.checkpoint_type
                ])
            filename = "checkpoints.csv"
            
        elif table_name == 'surveys':
            # アンケートデータのエクスポート
            surveys = db.session.query(
                Survey,
                Checkpoint.name.label('checkpoint_name')
            ).join(Checkpoint).order_by(Survey.checkpoint_id, Survey.survey_order).all()
            
            writer.writerow(['ID', 'チェックポイント', '質問', '順序', '選択肢'])
            for survey, checkpoint_name in surveys:
                # 選択肢を取得
                choices = Survey_Choice.query.filter_by(survey_id=survey.id).all()
                choices_str = '; '.join([f"{c.survey_choice}(値:{c.value})" for c in choices])
                
                writer.writerow([
                    survey.id,
                    checkpoint_name,
                    survey.question,
                    survey.survey_order,
                    choices_str
                ])
            filename = "surveys.csv"
            
        elif table_name == 'quizzes':
            # クイズデータのエクスポート
            quizzes = db.session.query(
                Quiz,
                Checkpoint.name.label('checkpoint_name')
            ).join(Checkpoint).order_by(Quiz.checkpoint_id, Quiz.quiz_order).all()
            
            writer.writerow(['ID', 'チェックポイント', '順序', '問題', '選択肢1', '選択肢2', '選択肢3', '正解'])
            for quiz, checkpoint_name in quizzes:
                writer.writerow([
                    quiz.id,
                    checkpoint_name,
                    quiz.quiz_order,
                    quiz.content,
                    quiz.answer_1,
                    quiz.answer_2,
                    quiz.answer_3,
                    quiz.correct
                ])
            filename = "quizzes.csv"

        elif table_name == 'quiz_responses':
            responses = db.session.query(
                Quiz_Response,
                Login.account.label('user_account'),
                Quiz.content.label('quiz_content'),
                Checkpoint.name.label('checkpoint_name')
            ).join(
                Login, Quiz_Response.login_id == Login.id
            ).join(
                Quiz, Quiz_Response.quiz_id == Quiz.id
            ).join(
                Checkpoint, Quiz.checkpoint_id == Checkpoint.id
            ).order_by(Quiz_Response.created_at.desc()).all()
            
            si = StringIO()
            writer = csv.writer(si)
            writer.writerow([
                'レスポンスID',
                'ユーザー',
                'チェックポイント',
                '問題',
                '選択した回答',
                '正誤',
                '回答日時'
            ])
            
            for response, user_account, quiz_content, checkpoint_name in responses:
                writer.writerow([
                    response.id,
                    user_account,
                    checkpoint_name,
                    quiz_content,
                    response.answer_selected,
                    '正解' if response.is_corrected else '不正解',
                    response.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            filename = "quiz_responses.csv"

        elif table_name == 'survey_responses':
            responses = db.session.query(
                Survey_Response,
                Login.account.label('user_account'),
                Survey.question.label('survey_question'),
                Checkpoint.name.label('checkpoint_name')
            ).join(
                Login, Survey_Response.login_id == Login.id
            ).join(
                Survey, Survey_Response.survey_id == Survey.id
            ).join(
                Checkpoint, Survey.checkpoint_id == Checkpoint.id
            ).order_by(Survey_Response.created_at.desc()).all()
            
            si = StringIO()
            writer = csv.writer(si)
            writer.writerow([
                'レスポンスID',
                'ユーザー',
                'チェックポイント',
                '質問',
                '回答値',
                '回答日時'
            ])
            
            for response, user_account, survey_question, checkpoint_name in responses:
                writer.writerow([
                    response.id,
                    user_account,
                    checkpoint_name,
                    survey_question,
                    response.value,
                    response.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            filename = "survey_responses.csv"
        
        elif table_name == 'mismatch_users':
        # クイズレスポンスとスタンプの不一致ユーザーのエクスポート
            # クイズレスポンスとスタンプの不一致を検出
                # クイズレスポンスとスタンプの不一致を検出
            mismatch_users = (
                db.session.query(
                    Login.id.label('user_id'), 
                    Login.account, 
                    Checkpoint.name.label('mismatched_checkpoints')
                )
                .select_from(Login)
                .join(Quiz_Response, Login.id == Quiz_Response.login_id)
                .join(Quiz, Quiz_Response.quiz_id == Quiz.id)
                .join(Checkpoint, Quiz.checkpoint_id == Checkpoint.id)
                .outerjoin(Stamp, and_(Login.id == Stamp.login_id, Checkpoint.id == Stamp.checkpoint_id))
                .filter(Stamp.id.is_(None), Quiz_Response.is_corrected == True)
                .group_by(Login.id, Login.account, Checkpoint.id)
                .all()
            )

            writer.writerow(['ユーザーID', 'アカウント', '不一致のチェックポイント'])
            for user in mismatch_users:
                writer.writerow([
                    user.user_id,
                    user.account,
                    user.mismatched_checkpoints
                ])
            filename = "mismatch_users.csv"

        elif table_name == 'stamp_without_quiz_users':

            # スタンプを獲得したがクイズに回答していないユーザーを検出
            stamp_without_quiz_users = (
            db.session.query(
                Login.id.label('user_id'),
                Login.account, 
                Checkpoint.name.label('mismatched_checkpoints')
            )
            .select_from(Login)
            .join(Stamp, Login.id == Stamp.login_id)
            .join(Checkpoint, Stamp.checkpoint_id == Checkpoint.id)
            .outerjoin(Quiz, Checkpoint.id == Quiz.checkpoint_id)
            .outerjoin(Quiz_Response, and_(Login.id == Quiz_Response.login_id, Quiz.id == Quiz_Response.quiz_id))
            .filter(Quiz_Response.id.is_(None))
            .group_by(Login.id, Login.account, Checkpoint.id)
            .all()
        )
            writer.writerow(['ユーザーID', 'アカウント', 'クイズ未回答のチェックポイント'])
            for user in stamp_without_quiz_users:
                writer.writerow([
                    user.user_id,
                    user.account,
                    user.mismatched_checkpoints
                ])
            filename = "stamp_without_quiz_users.csv"

        elif table_name == 'error_history':
            # セッションからエラー履歴データを取得
            error_data = session.get('mismatch_errors', [])
            
            # ヘッダーの書き込み
            writer.writerow([
                'ユーザーID',
                'アカウント',
                '不一致のチェックポイント'
            ])
            
            # データの書き込み
            for error in error_data:
                writer.writerow([
                    error['user_id'],
                    error['account'],
                    error['mismatched_checkpoints']
                ])
            
            filename = "error_history.csv"

        else:
            return 'Invalid table name', 400

        # StringIOの内容を取得してUTF-8でエンコード
        output = si.getvalue().encode('utf-8-sig')  # BOM付きUTF-8でエンコード
        
        # レスポンスの作成
        response = make_response(output)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        
        return response
        
    except Exception as e:
        print(f"Error during CSV export: {str(e)}")
        return str(e), 500



@app.route(f'/{hash_keys[13]}/statistics', methods=['GET'])
def stamp_statistics():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search', '')
    stats_filter = request.args.get('stats_filter', 'has_stamps')
    sort_order = request.args.get('sort_order', 'latest_first')

    # ユーザー統計を取得（フィルター設定を維持）
    users_pagination = get_user_statistics(
        page=page,
        per_page=per_page,
        search_query=search_query,
        stats_filter=stats_filter,
        sort_order=sort_order
    )

    # 進行状況マップデータの取得（同じフィルター設定を使用）
    progress_map_data = get_stamp_progress_data(
        page=page,
        per_page=per_page,
        search_query=search_query,
        stats_filter=stats_filter,
        sort_order=sort_order
    )

    # 全体の統計情報
    total_stats = {
        'total_stamps': db.session.query(db.func.count(Stamp.id)).scalar() or 0,
        'total_users': db.session.query(db.func.count(db.distinct(Stamp.login_id))).scalar() or 0,
        'completion_count': db.session.query(db.func.count(db.distinct(Login.id)))
            .filter(Login.is_ended == True).scalar() or 0
    }

    # チェックポイント統計
    checkpoint_stats = db.session.query(
        Checkpoint.name,
        Checkpoint.checkpoint_type,
        db.func.count(Stamp.id).label('visit_count')
    ).outerjoin(
        Stamp
    ).group_by(
        Checkpoint.id,
        Checkpoint.name,
        Checkpoint.checkpoint_type
    ).order_by(
        Checkpoint.checkpoint_order
    ).all()

    # 時間帯統計
    time_stats = db.session.query(
        db.func.strftime('%H', Stamp.created_at).label('hour'),
        db.func.count(Stamp.id).label('stamp_count'),
        db.func.count(db.distinct(Stamp.login_id)).label('unique_users')
    ).filter(Stamp.created_at.isnot(None))\
    .group_by('hour')\
    .order_by('hour')\
    .all()

    # 時間帯データの整形
    hours_data = {str(i).zfill(2): {'stamps': 0, 'users': 0} for i in range(24)}
    for stat in time_stats:
        if stat.hour:
            hours_data[stat.hour] = {
                'stamps': stat.stamp_count,
                'users': stat.unique_users
            }

    if app.debug:
        print("\n=== Debug Information ===")
        #print(f"User Stats Query: {user_stats}")
        print(f"Total Users: {users_pagination.total}")
        print(f"Current Page Items: {len(users_pagination.items)}")
        for user in users_pagination.items:
            print(f"User: {user.account}, Stamps: {user.total_stamps}, "
                  f"First: {user.first_stamp}, Last: {user.last_stamp}")

    return render_template(
        'admin/statistics.html',
        users_pagination=users_pagination,
        checkpoint_stats=checkpoint_stats,
        hours_data=hours_data,
        progress_map_data=progress_map_data,
        search_query=search_query,
        stats_filter=stats_filter,
        sort_order=sort_order,
        admin_hash=hash_keys[13],
        total_stats=total_stats,
        current_page=page,
        debug=app.debug
    )

# 統計情報を取得する関数を修正
def get_stamp_progress_data(page=1, per_page=10, search_query='', stats_filter='has_stamps', sort_order='latest_first'):
    # ユーザー統計のクエリを構築
    user_stats = get_user_statistics(
        page=page,
        per_page=per_page,
        search_query=search_query,
        stats_filter=stats_filter,
        sort_order=sort_order
    )
    
    # 現在のページのユーザーを順序を保持して取得
    current_users = [(user.id, user.account) for user in user_stats.items]
    
    # チェックポイントの取得（ゴール地点を除外）
    checkpoints = db.session.query(Checkpoint)\
        .filter(Checkpoint.checkpoint_type != 'goal')\
        .order_by(Checkpoint.checkpoint_order).all()
    checkpoint_names = [cp.name for cp in checkpoints]

    # スタンプデータを取得
    stamp_data = []
    for user_id, account in current_users:
        user_stamps = db.session.query(
            Login.account,
            Checkpoint.name,
            Stamp.created_at
        ).join(
            Stamp, Login.id == Stamp.login_id
        ).join(
            Checkpoint, Stamp.checkpoint_id == Checkpoint.id
        ).filter(
            Login.id == user_id,
            Checkpoint.checkpoint_type != 'goal'
        ).order_by(
            Stamp.created_at.asc() if sort_order == 'oldest_first' else Stamp.created_at.desc()
        ).all()
        
        stamp_data.extend(user_stamps)
    
    # プログレスマップ用のデータを構築
    progress_data = [{
        'x': result.account,
        'y': result.name,
        'timestamp': result.created_at.strftime('%H:%M')
    } for result in stamp_data]

    if app.debug:
        print("\n=== Progress Map Debug Information ===")
        print(f"Total Users in Current Page: {len(current_users)}")
        print(f"User Order: {[account for _, account in current_users]}")
        print("\nStamp Data:")
        for user_id, account in current_users:
            print(f"\nUser: {account}")
            user_stamps = [stamp for stamp in stamp_data if stamp.account == account]
            for stamp in user_stamps:
                print(f"  Checkpoint: {stamp.name}, Time: {stamp.created_at}")
        print("\nProgress Data Points:")
        for point in progress_data:
            print(f"User: {point['x']}, Checkpoint: {point['y']}, Time: {point['timestamp']}")
        print("=====================================\n")

    return {
        'progress_data': progress_data,
        'checkpoint_names': checkpoint_names,
        'user_order': [account for _, account in current_users],
        'total_pages': user_stats.pages,
        'current_page': page
    }

    # ... 残りのコードは同じ ...

# ユーザー統計用の関数
def get_user_statistics(page=1, per_page=10, search_query='', stats_filter='has_stamps', sort_order='latest_first'):
    # ベースクエリの構築
    user_stats = db.session.query(
        Login.id,
        Login.account,
        db.func.count(Stamp.id).label('total_stamps'),
        db.func.min(Stamp.created_at).label('first_stamp'),
        db.func.max(Stamp.created_at).label('last_stamp'),
        (db.func.julianday('now') - db.func.julianday(db.func.max(Stamp.created_at))) * 24 * 60 * 60
    ).join(
        Stamp, Login.id == Stamp.login_id
    ).group_by(
        Login.id,
        Login.account
    )

    # 検索クエリの適用
    if search_query:
        user_stats = user_stats.filter(Login.account.like(f'%{search_query}%'))

    # フィルタータイプの適用
    if stats_filter == 'completed_users':
        goal_exists = db.session.query(Stamp).filter(
            db.and_(
                Stamp.login_id == Login.id,
                Stamp.checkpoint_id == 13
            )
        ).exists()
        
        user_stats = user_stats.having(
            db.and_(
                db.func.count(db.distinct(Stamp.checkpoint_id)) == 13,
                db.session.query(goal_exists).scalar_subquery()
            )
        )
    elif stats_filter == 'has_stamps':
        user_stats = user_stats.having(
            db.and_(
                db.func.count(Stamp.id) >= 1,
                db.func.count(Stamp.id) <= 11
            )
        )
    elif stats_filter == 'stamps_1_to_2':
        user_stats = user_stats.having(
            db.and_(
                db.func.count(Stamp.id) >= 1,
                db.func.count(Stamp.id) <= 2
            )
        )
    elif stats_filter.startswith('stamps_'):
        try:
            num_stamps = int(stats_filter.split('_')[1])
            user_stats = user_stats.having(db.func.count(Stamp.id) == num_stamps)
        except (ValueError, IndexError):
            print("Invalid stamp filter format")

    # ソート順の適用（first_stampを基準にする）
    if sort_order == 'latest_first':
        user_stats = user_stats.order_by(db.func.min(Stamp.created_at).desc())
    else:  # oldest_first
        user_stats = user_stats.order_by(db.func.min(Stamp.created_at).asc())

    return user_stats.paginate(page=page, per_page=per_page, error_out=False)

###################################################################################################################################################
####3つの共通処理
# 変更点uchida
@app.route('/handle_checkpoint/<string:checkpoint_id_hash>', methods=['GET', 'POST'])
def handle_checkpoint(checkpoint_id_hash):
    checkpoint_id = checkpoint_hash_dic[checkpoint_id_hash]
    # チェックポイントの存在確認
    checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
    
    if checkpoint_id == 1:
        return login(checkpoint)  # チェックポイントオブジェクトを渡す
    elif checkpoint_id == 14:
        return goal_login(checkpoint)
    elif 2 <= checkpoint_id <= 68:  #変更点　cp数に応じて変更
        return checkpoint_login(checkpoint)

    
    #return redirect(url_for('main_menu'))アンケートが設定されていない場合だが、今回の件ではそんな状況は起きないはずだ。

# スタートポイントのログイン画面のルート
def login(checkpoint):  # checkpoint_idの代わりにcheckpointオブジェクトを受け取る
    if request.method == 'POST':
        account = request.form['account']
        user = Login.query.filter_by(account=account).first()


        # アカウント存在チェック
        if not user:
            flash("アカウントが間違っています", 'error')
            return render_template('login.html', title="ログイン", checkpoint=checkpoint)

        # ユーザーIDをセッションに保存
        session['user_id'] = user.id

        # is_endedのチェック
        if user.is_ended:
            flash("もうスタンプラリーは終了しています", 'error')
            return render_template('login.html', title="ログイン", checkpoint=checkpoint)

        # is_loggedinのチェック
        if user.is_loggedin:
            return redirect(url_for('main_menu'))
#判定を抜けてきて、ここでアクティブになる。
        user.issued_at = datetime.now(pytz.timezone('Asia/Tokyo'))
        if not user.is_used:
            user.is_used = True
        db.session.commit()

        return redirect(url_for('agreement', login_id=user.id))

    # GETメソッドの場合、チェックポイント情報とともにログイン画面を表示
    return render_template('login.html', title="ログイン", checkpoint=checkpoint)

# チェックポイントのログイン画面のルート
def checkpoint_login(checkpoint):
    if request.method == 'POST':
        account = request.form['account']
        user = Login.query.filter_by(account=account).first()

        # アカウント存在チェック
        if not user:
            flash("アカウントが間違っています", 'error')
            return render_template('login.html', title="ログイン", checkpoint=checkpoint)

        # ユーザーIDをセッションに保存
        session['user_id'] = user.id
        
        if not user.is_used:#多重エラー対応。前のルーティングで突破してたらほぼいらない。
            flash('はじめにスタート地点にログインしてから、スタンプラリーを始めてください。', 'error')
            return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))

        if not user.is_agree:
            flash('スタートポイントでの同意を完了し、アンケートに答えてからチェックポイントにアクセスしてください。', 'error')
            return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0])) 

        if not user.is_loggedin:
            flash('はじめにスタート地点にログインしてから、スタンプラリーを始めてください。', 'error')
            return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))

        if user.is_ended:
            flash("もうスタンプラリーはゴールしています", 'error')
            return render_template('login.html', title="ログイン", checkpoint=checkpoint)
        
        # STAMPテーブル内で同じチェックポイントIDが存在するか確認
        existing_stamp = Stamp.query.filter_by(
            checkpoint_id=checkpoint.id,
            login_id=user.id
        ).first()
        
        if existing_stamp:
            flash("このチェックポイントはすでにスタンプを獲得済みです。スタンプ獲得済みのチェックポイントにはログインできません。", 'error')
            return render_template('login.html', title="ログイン", checkpoint=checkpoint)

        # チェックポイントの説明ページとして表示
        quizzes = Quiz.query.filter_by(checkpoint_id=checkpoint.id).order_by(Quiz.quiz_order).all()
        total_quizzes = len(quizzes)

        return render_template(
            'checkpoint.html', 
            checkpoint=checkpoint,
            user=user,
            total_quizzes=total_quizzes
        )

    # GETメソッドの場合、チェックポイント情報とともにログイン画面を表示
    return render_template('login.html', title="ログイン", checkpoint=checkpoint)

# ゴール画面のログイン画面のルート
def goal_login(checkpoint):
    if request.method == "POST":
        account = request.form["account"]
        user = Login.query.filter_by(account=account).first()

        if not user:
            flash("アカウントが間違っています", 'error')
            return render_template("login.html", title="ログイン", checkpoint=checkpoint)

        # ユーザーIDをセッションに保存
        session['user_id'] = user.id

        #user_id = session.get('user_id')

        # ゴール済みチェック時の修正
        if user.is_ended:
            flash("もうスタンプラリーはゴールしています", 'error')
            return redirect(url_for('ended'))  # 修正: render_template から redirect に変更

        if not user.is_used:
            flash('はじめにスタート地点にログインしてから、スタンプラリーを始めてください。', 'error')
            return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0])) 

        #user = Login.query.get_or_404(user_id)

        if not user.is_agree:
            flash('スタートポイントでの同意を完了し、アンケートに答えてからチェックポイントにアクセスしてください。', 'error')
            return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0])) 

        if not user.is_loggedin:
            flash('はじめにスタート地点にログインしてから、スタンプラリーを始めてください。', 'error')
            return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0])) 

        # ログイン状態確認
        if user.is_loggedin:
            return redirect(url_for("show_stamps", user_id=user.id))
            

        return render_template("login.html", title="ログイン", checkpoint=checkpoint)

    return render_template("login.html", title="ログイン", checkpoint=checkpoint)

        # ゴールチェック
@app.route("/ended")
def ended():
    # セッションチェック
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。再度ログインしてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))

            # ユーザー存在チェック
    user = Login.query.get_or_404(user_id)
    if not user.is_ended:
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))

    return render_template("ended.html", hash_keys=hash_keys, user=user)

# 変更点uchida
# チェックポイントの種類に応じたデフォルトメッセージを定義
DEFAULT_MESSAGES = {
    'start': {
        "title": "スタート時アンケート調査",
        "message": "スタートポイントのアンケートにご協力ください。"
    },
    'normal': {
        "title": "チェックポイント時アンケート調査",
        "message": "チェックポイントのアンケートにご協力ください。"
    },
    'goal': {
        "title": "ゴール時アンケート調査",
        "message": "ゴールのアンケートにご協力ください。"
    }
}
# 変更点uchida
CHECKPOINT_MESSAGES = {
    1: {
        "title": "大阪成蹊大学オープンキャンパススタンプラリー",
        "message": "本日は「大阪成蹊大学オープンキャンパススタンプラリー」にご参加いただき、ありがとうございます。<br>"
"「大阪成蹊大学オープンキャンパススタンプラリー」は大阪成蹊大学せいけいデジタルサークルが制作し、<br><br>"
"このアンケート調査は、おおさk成蹊大学オープンキャンパスをよりよく検討するための情報を収集することを目的に、本日、ご参加の皆さまを対象にして実施しております。<br>"
"ご回答は匿名でいただき、すべて統計的に処理いたしますので、ご回答いただいた皆様にご迷惑をおかけすることは絶対にございません。なお、ご回答の有無、ご回答内容によって不利益を被ることはございません。<br><br>"
"なお、スタンプラリー終了後にもアンケート調査がございます。ご協力のほど、よろしくお願いいたします。<br><br>"
"大阪成蹊大学"
    },
    2: {
        "title": "o",
        "message": "次のアンケートにお答えください。"
    },
    3: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    4: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    5: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    6: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    7: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    8: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    9: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    10: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    11: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    12: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    13: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    14: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    15: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    16: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    17: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    18: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    19: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    20: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    21: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    22: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    23: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    24: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    25: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    26: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    27: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    28: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    29: {
        "title": "o",
        "message": "次のアンケートにお答えください。"
    },
    30: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    31: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    32: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    33: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    34: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    35: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    36: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    37: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    38: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    39: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    40: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    41: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    42: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    43: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    44: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    45: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    46: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    47: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    48: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    49: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    50: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    51: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    52: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    53: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    54: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    55: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    56: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    57: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    58: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    59: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    60: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    61: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    62: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    63: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    64: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    65: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    66: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    67: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    },
    


    13: {
        "title": "チェックポイント時アンケート調査",
        "message": "次のアンケートにお答えください。"
    }
}

def get_checkpoint_info(checkpoint_id):
    """チェックポイントの情報を取得"""
    checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
    
    # チェックポイント固有のメッセージがあればそれを使用
    # なければチェックポイントタイプに応じたデフォルトメッセージを使用
    message_info = CHECKPOINT_MESSAGES.get(
        checkpoint_id,
        DEFAULT_MESSAGES.get(checkpoint.checkpoint_type)
    )
    
    return checkpoint, message_info
# 変更点uchida
# ３つのアンケート画面の表示と回答送信
@app.route('/handle_survey/<int:checkpoint_id>', methods=['GET', 'POST'])
def handle_survey(checkpoint_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。該当のチェックポイントで再度ログインしてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[checkpoint_id-1]))
# 変更点uchida
    if checkpoint_id == 1:
        return start_survey(checkpoint_id)
#　ゴールのIDで、有効化したかったらDBのゴール地点のIDを見て適当な数字を入れる。
    elif checkpoint_id == 14:
        return goal_survey(user_id, checkpoint_id)
    elif 2 <= checkpoint_id <= 67:
        return checkpoint_survey(checkpoint_id)
    else:
        flash('無効なチェックポイントIDです。', 'error')
        return redirect(url_for('view_stamps'))

def validate_survey_responses(user, questions, request_form):
    responses = []
    unanswered_questions = []
    form_data = {}

    # アカウントの5桁目が'A'かどうかをチェック
    is_type_a_user = len(user.account) >= 5 and user.account[4] == 'A'

    for question in questions:
        if question.survey_choices:
            selected_choice_id = request_form.get(f'question_{question.id}')  # request_formを使用
            if selected_choice_id:
                form_data[f'question_{question.id}'] = selected_choice_id
                responses.append(Survey_Response(
                    login_id=user.id,
                    survey_id=question.id,
                    value=selected_choice_id
                ))
            
            # 必須回答チェックの修正
            is_aop_question = '（AOP）' in question.question
            if is_type_a_user:
                # Aユーザーの場合、（AOP）マーカーがある質問は任意、それ以外は必須
                if not selected_choice_id and not is_aop_question:
                    unanswered_questions.append(question.question)
            else:
                # 通常ユーザーは従来通り（回答必須）の質問のみ必須
                if '（回答必須）' in question.question and not selected_choice_id:
                    unanswered_questions.append(question.question)

    return responses, unanswered_questions, form_data

# スタートポイントのアンケート画面
def start_survey(checkpoint_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。<br>スタートポイントで再度ログインしてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))

    user = Login.query.get_or_404(user_id)
    checkpoint, message_info = get_checkpoint_info(checkpoint_id)

    questions = Survey.query.filter_by(checkpoint_id=checkpoint_id)\
        .options(db.joinedload(Survey.survey_choices))\
        .order_by(Survey.survey_order).all()
    
    if request.method == 'POST':
        try:
            responses = []
            form_data = {}
            all_questions_answered = True

            # アカウントの5桁目が'A'かどうかをチェック
            is_type_a_user = len(user.account) >= 5 and user.account[4] == 'A'

            # すべての質問をチェック
            for question in questions:
                if question.survey_choices:
                    selected_choice_id = request.form.get(f'question_{question.id}')
                    if selected_choice_id:
                        form_data[f'question_{question.id}'] = selected_choice_id
                        responses.append(Survey_Response(
                            login_id=user.id,
                            survey_id=question.id,
                            value=selected_choice_id
                        ))
                    else:
                        is_aop_question = '（AOP）' in question.question
                        if is_type_a_user:
                            if not is_aop_question:
                                all_questions_answered = False
                                break
                        else:
                            if '（回答必須）' in question.question:
                                all_questions_answered = False
                                break

            # 必要な質問に全て回答済みの場合のみ処理を進める
            if all_questions_answered:
                # スタンプを追加
                new_stamp = Stamp(
                    checkpoint_id=checkpoint_id,
                    login_id=user.id
                )
                db.session.add(new_stamp)
                db.session.add_all(responses)
                user.is_loggedin = True
                db.session.commit()

                flash('スタートアンケートが完了しました！<br>ご協力ありがとうございます。', 'ended')
                return redirect(url_for('main_menu', user=user.account))

            # 未回答の質問がある場合は単にフォームを再表示
            return render_template(
                'survey.html',
                title=message_info["title"],
                initial_message=message_info["message"],
                checkpoint=checkpoint,
                questions=questions,
                form_data=form_data,
                user=user,
                is_type_a_user=is_type_a_user
            )

        except SQLAlchemyError:
            db.session.rollback()
            flash('エラーが発生しました。<br>もう一度お試しください。', 'error')
            return render_template(
                'survey.html',
                title=message_info["title"],
                initial_message=message_info["message"],
                checkpoint=checkpoint,
                questions=questions,
                form_data=form_data,
                user=user,
                is_type_a_user=is_type_a_user
            )

    # GETリクエストの場合
    return render_template(
        'survey.html',
        title=message_info["title"],
        initial_message=message_info["message"],
        checkpoint=checkpoint,
        questions=questions,
        user=user,
        form_data={},
        is_type_a_user=len(user.account) >= 5 and user.account[4] == 'A'
    )

# チェックポイントのアンケート画面
def checkpoint_survey(checkpoint_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。<br>該当のチェックポイントで再度ログインしてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[checkpoint_id-1]))
    
    user = Login.query.get_or_404(user_id)
    checkpoint, message_info = get_checkpoint_info(checkpoint_id)
    
    questions = Survey.query.filter_by(checkpoint_id=checkpoint_id)\
        .options(db.joinedload(Survey.survey_choices))\
        .order_by(Survey.survey_order).all()

    if request.method == 'POST':
        try:
            responses = []
            unanswered_questions = []

            # すべての質問をチェック
            for question in questions:
                if question.survey_choices:
                    selected_choice_id = request.form.get(f'question_{question.id}')
                    if not selected_choice_id:
                        unanswered_questions.append(question.question)
                    else:
                        responses.append(Survey_Response(
                            login_id=user.id,
                            survey_id=question.id,
                            value=selected_choice_id
                        ))

            # 未回答の質問がある場合
            if unanswered_questions:
                error_message = "以下の質問に回答してください：<br>" + "<br>".join([
                    f"・{q}" for q in unanswered_questions
                ])
                flash(error_message, 'error')
                return render_template(
                    'survey.html',
                    title=message_info["title"],
                    initial_message=message_info["message"],
                    checkpoint=checkpoint,
                    questions=questions,
                    user=user
                )
#スタンプ取得
            
            # 全ての質問に回答済みの場合
            db.session.add_all(responses)
            db.session.add(Stamp(
                checkpoint_id=checkpoint_id,
                login_id=user.id
            ))
            db.session.commit()
            flash(f'{checkpoint.name}のスタンプを獲得しました！<br><br>次のチェックポイントに向かいましょう！', 'success')
            return redirect(url_for('view_stamps', checkpoint_id=checkpoint_id,stamp_added=True))

        except SQLAlchemyError:
            db.session.rollback()
            flash('エラーが発生しました。<br>もう一度お試しください。', 'error')

    return render_template(
        'survey.html',
        title=message_info["title"],
        initial_message=message_info["message"],
        checkpoint=checkpoint,
        questions=questions,
        checkpoint_id=checkpoint_id,
        user=user
    )

# ゴールのアンケート画面
def goal_survey(user_id, checkpoint_id):
    if not user_id:
        user_id = session.get('user_id')
        if not user_id:
            flash('セッションが切れました。<br>ゴールポイントで再度ログインしてください。', 'error')
            return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[13]))

    user = Login.query.get_or_404(user_id)
    checkpoint, message_info = get_checkpoint_info(checkpoint_id)
    is_type_a_user = len(user.account) >= 5 and user.account[4] == 'A'

    questions = Survey.query.filter_by(checkpoint_id=checkpoint_id)\
        .options(db.joinedload(Survey.survey_choices))\
        .order_by(Survey.survey_order).all()

    if request.method == "POST":
        try:
            responses = []
            form_data = {}  
            all_questions_answered = True
            unanswered_required = []

            # すべての質問をチェック
            for question in questions:
                if question.survey_choices:  # 選択肢がある質問のみ処理
                    selected_choice_id = request.form.get(f'question_{question.id}')
                    form_data[f'question_{question.id}'] = selected_choice_id
                    
                    if selected_choice_id:
                        responses.append(Survey_Response(
                            login_id=user.id,
                            survey_id=question.id,
                            value=selected_choice_id
                        ))
                    else:
                        is_aop_question = '（AOP）' in question.question
                        if is_type_a_user:
                            # Aユーザーの場合、（AOP）がない選択式質問は必須
                            if not is_aop_question:
                                all_questions_answered = False
                                unanswered_required.append(question.question)
                        else:
                            # 通常ユーザーは（回答必須）の質問のみ必須
                            if '（回答必須）' in question.question:
                                all_questions_answered = False
                                unanswered_required.append(question.question)

            # 必須質問の未回答チェック
            if not all_questions_answered:
                error_message = "以下の質問に回答してください：<br>" + "<br>".join([
                    f"・{q}" for q in unanswered_required
                ])
                flash(error_message, 'error')
                return render_template(
                    'survey.html',
                    title=message_info["title"],
                    initial_message=message_info["message"],
                    checkpoint=checkpoint,
                    questions=questions,
                    form_data=form_data,
                    user=user,
                    is_type_a_user=is_type_a_user
                )

            # 全ての必須質問に回答済みの場合
            new_stamp = Stamp(
                checkpoint_id=checkpoint_id,
                login_id=user_id
            )
            db.session.add(new_stamp)
            db.session.add_all(responses)
            user.is_ended = True
            db.session.commit()

            return redirect(url_for("goal"))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('エラーが発生しました。<br>もう一度お試しください。', 'error')
            return render_template(
                'survey.html',
                title=message_info["title"],
                initial_message=message_info["message"],
                checkpoint=checkpoint,
                questions=questions,
                form_data=form_data,
                user=user,
                is_type_a_user=is_type_a_user
            )

    # GETリクエストの場合
    return render_template(
        'survey.html',
        title=message_info["title"],
        initial_message=message_info["message"],
        checkpoint=checkpoint,
        questions=questions,
        user=user,
        form_data={},
        is_type_a_user=is_type_a_user
    )

# メインメニュー画面
@app.route('/main_menu')
def main_menu():
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。スタートポイントで再度ログインしてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))
    user = Login.query.get_or_404(user_id)
    return render_template('main_menu.html', title="メインメニュー", user=user)

#スタンプラリーの参加方法ページ
@app.route('/participation_guide')
def participation_guide():
    return render_template('participation_guide.html', title="スタンプラリーの参加方法")

#スタンプラリーアプリの使い方ページ
@app.route('/app_usage')
def app_usage():
    return render_template('app_usage.html', title="スタンプラリーアプリの使い方")



####スタート画面:ビジネスロジック


#同意画面
@app.route('/agreement/<int:login_id>', methods=['GET', 'POST'])
def agreement(login_id):
    user = Login.query.get(login_id)
    if request.method == 'POST':
        user.is_agree = True
        db.session.commit()

        # スタンプの登録はここでは行わない
        if user.is_loggedin:
            return redirect(url_for('main_menu'))

        # アンケート画面にリダイレクト
        return redirect(url_for('handle_survey', checkpoint_id=1))

    return render_template('agreement.html', title="同意確認", user=user)

#ゲット済みのスタンプ確認ページ
@app.route('/view_stamps')
def view_stamps():
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。<br>スタートポイントで再度ログインしてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))
    
        # スタンプ取得時のメッセージを改行付きで表示
    #if request.args.get('stamp_added'):
    #    flash('新しいスタンプを獲得しました！<br>次のチェックポイントに向かいましょう。', 'success')

    user = Login.query.get_or_404(user_id)

    obtained_stamps = db.session.query(
        Stamp.checkpoint_id,
        db.func.max(Stamp.created_at).label('latest_stamp'),
        db.func.count(Stamp.id).label('visit_count')
    ).filter_by(login_id=user.id
    ).group_by(Stamp.checkpoint_id
    ).all()

    all_checkpoints = Checkpoint.query.order_by(Checkpoint.checkpoint_order).all()
    stamp_info = {
        stamp.checkpoint_id: {
            'latest_stamp': stamp.latest_stamp,
            'visit_count': stamp.visit_count
        } for stamp in obtained_stamps
    }

    checkpoint_data = []
    for checkpoint in all_checkpoints:
        stamp_data = stamp_info.get(checkpoint.id, {})
        checkpoint_data.append({
            'id': checkpoint.id,
            'name': checkpoint.name,
            'description': checkpoint.description.replace('\n', '<br>'),  # 改行を<br>タグに変換
            'type': checkpoint.checkpoint_type,
            'is_obtained': checkpoint.id in stamp_info,
            'latest_stamp': stamp_data.get('latest_stamp'),
            'visit_count': stamp_data.get('visit_count', 0)
        })

    return render_template(
        'view_stamps.html',
        title="獲得済みスタンプ",
        checkpoints=checkpoint_data,
        user=user
    )





####チェックポイント:画面ビジネスロジック


#チェックポイントの詳細の表示
def checkpoint(checkpoint_id):
   user_id = session.get('user_id')
   if not user_id:
       flash('セッションが切れました。再度ログインしてください。', 'error')
       return redirect(url_for('login'))

   user = Login.query.get_or_404(user_id)

   if not user.is_used:#多重エラー対応。前のルーティングで突破してたらほぼいらない。
       flash('はじめにスタート地点にログインしてから、スタンプラリーを始めてください。', 'error')
       return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0])) 

   if not user.is_loggedin:
       flash('はじめにスタート地点にログインしてから、スタンプラリーを始めてください。', 'error')
       return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))

   checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
   
   # GETリクエストの場合の処理
   quizzes = Quiz.query.filter_by(checkpoint_id=checkpoint_id).order_by(Quiz.quiz_order).all()
   total_quizzes = len(quizzes)

   return render_template(
       'checkpoint.html', 
       checkpoint=checkpoint,
       user=user,
       total_quizzes=total_quizzes
   )

#クイズ画面の表示と回答処理
@app.route('/quiz/<int:checkpoint_id>', methods=['GET', 'POST'])
def quiz(checkpoint_id):
   # セッションチェック
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。該当のチェックポイントで再度ログインしてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[checkpoint_id-1]))

    user = Login.query.get_or_404(user_id)

    # ユーザーの状態チェック
    if not user.is_used:#多重エラー対応。前のルーティングで突破してたらほぼいらない。
        flash('はじめにスタート地点にログインしてから、スタンプラリーを始めてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))

    if not user.is_loggedin:
        flash('はじめにスタート地点にログインしてから、スタンプラリーを始めてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))

    if user.is_ended:
        flash('もうスタンプラリーはゴールしています。', 'error')
        return redirect(url_for('ended'))

    # スタンプ取得チェック
    existing_stamp = Stamp.query.filter_by(
        checkpoint_id=checkpoint_id,
        login_id=user.id
    ).first()
   
    if existing_stamp:
        flash("もうこのチェックポイントのスタンプを獲得しています。", 'error')
        return redirect(url_for('view_stamps'))

    quiz_order = request.args.get('quiz_order', type=float)

    # プログレス情報とクイズの取得を一本化
    try:
        all_quizzes = Quiz.query.filter_by(checkpoint_id=checkpoint_id)\
            .order_by(Quiz.quiz_order)\
            .all()
        total_quizzes = len(all_quizzes)
        
        # 最初のアクセス時（quiz_orderなし）
        if quiz_order is None and total_quizzes > 0:
            first_quiz = all_quizzes[0]
            return redirect(url_for('quiz', 
                                  checkpoint_id=checkpoint_id, 
                                  quiz_order=float(first_quiz.quiz_order)))
        elif total_quizzes == 0:
            flash('このチェックポイントにはクイズが設定されていません。', 'error')
            return redirect(url_for('checkpoint', checkpoint_id=checkpoint_id))

        # current_quiz_numberの計算
        current_quiz_number = None
        if quiz_order is not None:
            for i, q in enumerate(all_quizzes, 1):
                if abs(float(q.quiz_order) - float(quiz_order)) < 0.0001:
                    current_quiz_number = i
                    break
        
        if current_quiz_number is None:
            current_quiz_number = 1

        # 現在のクイズを取得
        current_quiz = Quiz.query.filter_by(
            checkpoint_id=checkpoint_id,
            quiz_order=quiz_order
        ).first()

        if not current_quiz:
            return redirect(url_for('quiz', 
                                  checkpoint_id=checkpoint_id, 
                                  quiz_order=float(all_quizzes[0].quiz_order)))

    except Exception as e:
        print(f"Error in quiz processing: {e}")
        flash('クイズ情報の取得中にエラーが発生しました。', 'error')
        return redirect(url_for('checkpoint', checkpoint_id=checkpoint_id))

    # POST処理（回答送信）
    if request.method == 'POST':
        try:
            current_quiz = Quiz.query.filter_by(
                checkpoint_id=checkpoint_id,
                quiz_order=quiz_order
            ).first()

            if not current_quiz:
                flash('クイズが見つかりません。', 'error')
                return redirect(url_for('checkpoint', checkpoint_id=checkpoint_id))

            answer_selected = request.form.get('answer')
            if not answer_selected:
                flash("選択肢を選んでください。", 'error')
                return render_template(
                    'quiz.html',
                    quiz=current_quiz,
                    total_quizzes=total_quizzes,
                    current_quiz_number=current_quiz_number,
                    checkpoint_id=checkpoint_id
                )

            normalized_answer = answer_selected.strip()
            normalized_correct = current_quiz.correct.strip()
            is_correct = (normalized_answer == normalized_correct)

            # 回答を保存
            quiz_response = Quiz_Response(
                login_id=user.id,
                quiz_id=current_quiz.id,
                answer_selected=answer_selected,
                is_corrected=is_correct
            )
            db.session.add(quiz_response)
            db.session.commit()

            if is_correct:
                # 次のクイズを探す（1未満の順序に対応）
                next_quiz = Quiz.query.filter(
                    Quiz.checkpoint_id == checkpoint_id,
                    Quiz.quiz_order > float(quiz_order)
                ).order_by(Quiz.quiz_order).first()

                if next_quiz:
                    flash("正解です！", 'success')
                    return redirect(url_for('quiz',
                                          checkpoint_id=checkpoint_id,
                                          quiz_order=float(next_quiz.quiz_order)))
                else:
                    # 全クイズ完了
                    session['quiz_completed'] = True
                    flash("おめでとうございます！すべて正解しました", 'success')
                    return redirect(url_for('handle_survey', checkpoint_id=checkpoint_id))
            else:
                flash("不正解です。もう一度挑戦してください。", 'error')
                return render_template(
                    'quiz.html',
                    quiz=current_quiz,
                    total_quizzes=total_quizzes,
                    current_quiz_number=current_quiz_number,
                    checkpoint_id=checkpoint_id
                )

        except Exception as e:
            db.session.rollback()
            print(f"Error processing answer: {e}")
            flash('回答の処理中にエラーが発生しました。', 'error')
            return render_template(
                'quiz.html',
                quiz=current_quiz,
                total_quizzes=total_quizzes,
                current_quiz_number=current_quiz_number,
                checkpoint_id=checkpoint_id
            )

    # 現在のクイズを取得（GETリクエスト時）
    try:
        current_quiz = Quiz.query.filter_by(
            checkpoint_id=checkpoint_id,
            quiz_order=quiz_order
        ).first()
        
        if not current_quiz and total_quizzes > 0:
            return redirect(url_for('quiz', 
                                  checkpoint_id=checkpoint_id, 
                                  quiz_order=float(all_quizzes[0].quiz_order)))

    except Exception as e:
        print(f"Error querying quiz: {e}")
        flash('クイズの取得中にエラーが発生しました。', 'error')
        return redirect(url_for('checkpoint', checkpoint_id=checkpoint_id))

    # テンプレート表示
    return render_template(
        'quiz.html',
        quiz=current_quiz,
        total_quizzes=total_quizzes,
        current_quiz_number=current_quiz_number,
        checkpoint_id=checkpoint_id
    )



####ゴール画面:ビジネスロジック



# スタンプ一覧の表示
@app.route("/show_stamps/<int:user_id>")
def show_stamps(user_id):
    checkpoints = Checkpoint.query.order_by(Checkpoint.checkpoint_order).all()
    user_stamps = set(stamp.checkpoint_id for stamp in Stamp.query.filter_by(login_id=user_id).all())

    # 必要なチェックポイントのIDセットを修正 (2から12まで)
    required_checkpoint_ids = set(range(2, 12))  # 2から12までに修正
    
    collected_stamps = len(required_checkpoint_ids.intersection(user_stamps))
    total_required = len(required_checkpoint_ids)  # 6個になります

    goal_checkpoint = Checkpoint.query.filter_by(id=13).first()
    
    # ゴールアンケートのアクティブ化条件を厳密化
    active_survey = (collected_stamps >= total_required and 
                    goal_checkpoint and 
                    goal_checkpoint.id not in user_stamps and
                    all(cp_id in user_stamps for cp_id in required_checkpoint_ids))  # すべての必要なチェックポイントを確認

    survey_checkpoints = [goal_checkpoint] if active_survey and goal_checkpoint else []

    return render_template(
        "stamps.html",
        checkpoints=checkpoints,
        user_stamps=user_stamps,
        active_survey=active_survey,
        survey_checkpoints=survey_checkpoints,
        user_id=user_id,
        collected_stamps=collected_stamps,
        total_required=total_required
    )

# ゴール画面
@app.route("/goal")
def goal():
    return render_template("goal.html")

