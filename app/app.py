from flask import Flask, request, render_template, flash, url_for, session, redirect, jsonify
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
from sqlalchemy import or_
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
# アプリケーションのテーブルにアクセスした後にセッションを閉じるための teardown_appcontext ハンドラを追加
@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception:  # 例外が発生した場合の処理を追加
        print(f"エラーが発生しました: {exception}")  # エラーログを出力
    db.session.remove()  # リクエストコンテキスト終了時にセッションを閉じる

#------------------------------------------------以上はセットアップ----------------------------------------------------------

# テーブルを操作する関数の例
def get_all_logins():
    return db.session.query(Login).all()  
@app.route('/logins', methods=['GET'])
def show_logins():
    try:
        logins = get_all_logins()
        output = '<h1>ログイン情報</h1><ul>'
        for login in logins:
           output += f'<li>ID: {login.id}, アカウント: {login.account}</li>'
        output += '</ul><br><a href="/admin">Back</a>'
        return output
    except Exception as e:
        return f'<h1>エラーが発生しました</h1><p>{str(e)}</p>'

#def get_all_Checkpoint():
#    return db.session.query(Checkpoint).all()  

#def get_all_Quiz():
 #   return db.session.query(Quiz).all()  

#def get_all_Quiz_Response():
 #   return db.session.query(Quiz_Response).all()  

#def get_all_Stamp():
 #   return db.session.query(Stamp).all()  

#def get_all_Survey():
 #   return db.session.query(Survey).all()  

#def get_all_Survey_Choice():
 #   return db.session.query(Survey_Choice).all()  

#def get_all_Survey_Response():
 #   return db.session.query(Survey_Response).all() 
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

checkpoint_hash_dic = {'ajrwkhlkafsddfd': 1,
                       'syflwdehkejhrsd': 2, 
                       'hgosmcbgdirmagf': 3, 
                       'hocnhsmtgdobmjg': 4, 
                       'bginchrfmhodhlk': 5, 
                       'nhkbhditmfobhhj': 6, 
                       'gkfcnshvmfjhpdj': 7, 
                       'afsjfnvidngmcjx': 8, 
                       'hhkncfouvmiwoxz': 9,
                       'gdwahxojopmkcgd': 10,  
                       }
hash_keys = list(checkpoint_hash_dic.keys())

@app.route('/admin')
def hello():
    output=f'''
<h1>Hello World</h1>
<ul>
<li><a href="/logins">ログイン情報</a></li>
<li><a href="/handle_checkpoint/{hash_keys[0]}">スタートポイントログイン</a></li>
<li><a href="/handle_checkpoint/{hash_keys[1]}">チェックポイント地点１ログイン</a></li>
<li><a href="/handle_checkpoint/{hash_keys[2]}">チェックポイント地点２ログイン</a></li>
<li><a href="/handle_checkpoint/{hash_keys[3]}">チェックポイント地点３ログイン</a></li>
<li><a href="/handle_checkpoint/{hash_keys[4]}">チェックポイント地点４ログイン</a></li>
<li><a href="/handle_checkpoint/{hash_keys[5]}">チェックポイント地点５ログイン</a></li>
<li><a href="/handle_checkpoint/{hash_keys[6]}">チェックポイント地点６ログイン</a></li>
<li><a href="/handle_checkpoint/{hash_keys[7]}">チェックポイント地点７ログイン</a></li>
<li><a href="/handle_checkpoint/{hash_keys[8]}">ゴールポイントログイン</a></li>
<li><a href="/{hash_keys[9]}">管理画面</a></li>
</ul>
'''
    return output

# 管理画面
# 管理画面のメインページ
@app.route(f'/{hash_keys[9]}')
def admin_panel():
    # ページネーションのパラメータを取得
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 1ページあたりの表示数
    search_query = request.args.get('search', '')

    # ユーザー検索クエリの構築
    user_query = Login.query
    if search_query:
        user_query = user_query.filter(Login.account.like(f'%{search_query}%'))
    
    # ページネーション適用
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

    # ページネーション適用
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

    return render_template(
        'admin/panel.html',
        users_pagination=users_pagination,
        checkpoints=checkpoints,
        surveys_pagination=surveys_pagination,  # surveysをsurveys_paginationに変更
        survey_choices=survey_choices,
        quizzes=quizzes,
        admin_hash=hash_keys[9],
        search_query=search_query,
        stamps=formatted_stamps,
        stamps_pagination=stamps_pagination,
        survey_search=survey_search,
        quizzes_pagination=quizzes_pagination,
        quiz_search=quiz_search  # 検索クエリを渡す
    )

# クイズ追加のAPI
@app.route(f'/{hash_keys[9]}/add_quiz', methods=['POST'])
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
@app.route(f'/{hash_keys[9]}/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # 関連する回答も削除
        Quiz_Response.query.filter_by(quiz_id=quiz_id).delete()
        
        # クイズを削除
        db.session.delete(quiz)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Quiz deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting quiz: {str(e)}")  # サーバーログに記録
        return jsonify({
            'success': False,
            'error': 'クイズの削除中にエラーが発生しました'
        }), 500

# ログインフラグの更新API
@app.route(f'/{hash_keys[9]}/update_login', methods=['POST'])
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
@app.route(f'/{hash_keys[9]}/update_checkpoint', methods=['POST'])
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
@app.route(f'/{hash_keys[9]}/add_survey', methods=['POST'])
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
@app.route(f'/{hash_keys[9]}/delete_survey/<int:survey_id>', methods=['POST'])
def delete_survey(survey_id):
    try:
        survey = Survey.query.get_or_404(survey_id)
        
        # 関連する選択肢を削除
        Survey_Choice.query.filter_by(survey_id=survey_id).delete()
        
        # アンケートを削除
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
@app.route(f'/{hash_keys[9]}/search_users', methods=['GET'])
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
@app.route(f'/{hash_keys[9]}/get_stamps', methods=['GET'])
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
@app.route(f'/{hash_keys[9]}/add_stamp', methods=['POST'])
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
@app.route(f'/{hash_keys[9]}/delete_stamp/<int:stamp_id>', methods=['POST'])
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

# CSVエクスポート用の関数を追加
@app.route(f'/{hash_keys[9]}/export/<table_name>')
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

# 統計情報を取得する関数を修正
def get_stamp_progress_data(page=1, per_page=10):
    # アクティブユーザー（3つのフラグが立っているユーザー）のスタンプ情報を取得
    active_stamps = db.session.query(
        Stamp.login_id,
        Login.account,
        Checkpoint.name.label('checkpoint_name'),
        Stamp.checkpoint_id,
        Stamp.created_at
    ).join(
        Login, Stamp.login_id == Login.id
    ).join(
        Checkpoint, Stamp.checkpoint_id == Checkpoint.id
    ).filter(
        Login.is_loggedin == True,
        Login.is_used == True,
        Login.is_agree == True
    ).order_by(
        Stamp.login_id,
        Stamp.created_at
    ).all()

    # チェックポイント名の一覧を取得（Y軸用）
    checkpoints = db.session.query(
        Checkpoint.id,
        Checkpoint.name
    ).order_by(
        Checkpoint.checkpoint_order
    ).all()
    
    checkpoint_names = [cp.name for cp in checkpoints]
    checkpoint_ids = {cp.id: idx for idx, cp in enumerate(checkpoints)}

    # ユーザーごとのデータを整理
    user_progress = defaultdict(lambda: {
        'account': '',
        'stamps': set(),
        'timestamps': {}
    })

    for stamp in active_stamps:
        user_progress[stamp.login_id]['account'] = stamp.account
        user_progress[stamp.login_id]['stamps'].add(stamp.checkpoint_id)
        user_progress[stamp.login_id]['timestamps'][stamp.checkpoint_id] = stamp.created_at.strftime('%H:%M')

    # ページネーション用にデータを準備
    user_list = list(user_progress.items())
    total_users = len(user_list)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_users = user_list[start_idx:end_idx]

    # グラフ用のデータを生成
    progress_data = []
    for user_id, data in paginated_users:
        for checkpoint_id in data['stamps']:
            progress_data.append({
                'x': data['account'],
                'y': checkpoint_names[checkpoint_ids[checkpoint_id]],
                'timestamp': data['timestamps'][checkpoint_id]
            })

    return {
        'progress_data': progress_data,
        'checkpoint_names': checkpoint_names,
        'total_users': total_users,
        'total_pages': (total_users + per_page - 1) // per_page
    }

@app.route(f'/{hash_keys[9]}/statistics')
def stamp_statistics():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search', '')

    # 1. ユーザー統計（ページネーション対応）
    user_query = db.session.query(
        Login.account,
        db.func.count(Stamp.id).label('total_stamps'),
        db.func.min(Stamp.created_at).label('first_stamp'),
        db.func.max(Stamp.created_at).label('last_stamp')
    ).outerjoin(
        Stamp
    ).group_by(Login.id)

    if search_query:
        user_query = user_query.filter(Login.account.like(f'%{search_query}%'))

    users_pagination = user_query.paginate(page=page, per_page=per_page, error_out=False)

    # 2. チェックポイント統計
    checkpoint_stats = db.session.query(
        Checkpoint.name,
        Checkpoint.checkpoint_type,
        db.func.count(Stamp.id).label('visit_count')
    ).outerjoin(
        Stamp
    ).group_by(
        Checkpoint.id
    ).order_by(
        Checkpoint.checkpoint_order
    ).all()

    # 3. 時間帯統計
    time_stats = db.session.query(
        db.func.strftime('%H', Stamp.created_at).label('hour'),
        db.func.count(Stamp.id).label('stamp_count'),
        db.func.count(db.distinct(Stamp.login_id)).label('unique_users')
    ).group_by(
        'hour'
    ).order_by(
        'hour'
    ).all()

    # 4. 進行状況マップ用データ
    active_stamps = db.session.query(
        Stamp.login_id,
        Login.account,
        Checkpoint.name.label('checkpoint_name'),
        Stamp.checkpoint_id,
        Stamp.created_at
    ).join(
        Login, Stamp.login_id == Login.id
    ).join(
        Checkpoint, Stamp.checkpoint_id == Checkpoint.id
    ).filter(
        Login.is_loggedin == True,
        Login.is_used == True,
        Login.is_agree == True
    ).order_by(
        Stamp.login_id,
        Stamp.created_at
    ).all()

    # チェックポイント名の一覧を取得（Y軸用）
    checkpoints = db.session.query(
        Checkpoint.id,
        Checkpoint.name
    ).order_by(
        Checkpoint.checkpoint_order
    ).all()
    
    checkpoint_names = [cp.name for cp in checkpoints]
    checkpoint_ids = {cp.id: idx for idx, cp in enumerate(checkpoints)}

    # ユーザーごとのデータを整理
    user_progress = defaultdict(lambda: {
        'account': '',
        'stamps': set(),
        'timestamps': {}
    })

    for stamp in active_stamps:
        user_progress[stamp.login_id]['account'] = stamp.account
        user_progress[stamp.login_id]['stamps'].add(stamp.checkpoint_id)
        user_progress[stamp.login_id]['timestamps'][stamp.checkpoint_id] = stamp.created_at.strftime('%H:%M')

    # ページネーション用にデータを準備
    user_list = list(user_progress.items())
    total_users = len(user_list)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_users = user_list[start_idx:end_idx]

    # グラフ用のデータを生成
    progress_data = []
    for user_id, data in paginated_users:
        for checkpoint_id in data['stamps']:
            progress_data.append({
                'x': data['account'],
                'y': checkpoint_names[checkpoint_ids[checkpoint_id]],
                'timestamp': data['timestamps'][checkpoint_id]
            })

    # 5. 全体の統計情報
    total_stats = {
        'total_stamps': db.session.query(db.func.count(Stamp.id)).scalar() or 0,
        'total_users': db.session.query(db.func.count(db.distinct(Stamp.login_id))).scalar() or 0,
        'completion_count': db.session.query(db.func.count(db.distinct(Login.id)))
            .filter(Login.is_ended == True).scalar() or 0
    }

    # 時間帯データの整形
    hours_data = {str(i).zfill(2): {'stamps': 0, 'users': 0} for i in range(24)}
    for stat in time_stats:
        hours_data[stat.hour] = {
            'stamps': stat.stamp_count,
            'users': stat.unique_users
        }

    # 進行状況マップのデータをまとめる
    progress_map_data = {
        'progress_data': progress_data,
        'checkpoint_names': checkpoint_names,
        'total_users': total_users,
        'total_pages': (total_users + per_page - 1) // per_page
    }

    return render_template(
        'admin/statistics.html',
        users_pagination=users_pagination,
        checkpoint_stats=checkpoint_stats,
        hours_data=hours_data,
        progress_map_data=progress_map_data,
        search_query=search_query,
        admin_hash=hash_keys[9],
        total_stats=total_stats,
        current_page=page
    )


####3つの共通処理



@app.route('/handle_checkpoint/<string:checkpoint_id_hash>', methods=['GET', 'POST'])
def handle_checkpoint(checkpoint_id_hash):
    checkpoint_id = checkpoint_hash_dic[checkpoint_id_hash]
    # チェックポイントの存在確認
    checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
    
    if checkpoint_id == 1:
        return login(checkpoint)  # チェックポイントオブジェクトを渡す
    elif 2 <= checkpoint_id <= 8:
        return checkpoint_login(checkpoint)
    elif checkpoint_id == 9:
        return goal_login(checkpoint)
    
    return redirect(url_for('main_menu'))

# スタートポイントのログイン画面のルート
def login(checkpoint):  # checkpoint_idの代わりにcheckpointオブジェクトを受け取る
    if request.method == 'POST':
        account = request.form['account']
        user = Login.query.filter_by(account=account).first()

        # アカウント存在チェック
        if not user:
            flash("アカウントが間違っています", 'error')
            return render_template('login.html', title="ログイン", checkpoint=checkpoint)

        # is_endedのチェック
        if user.is_ended:
            flash("もうスタンプラリーはゴールしています", 'error')
            return render_template('login.html', title="ログイン", checkpoint=checkpoint)

        # is_loggedinのチェック
        if user.is_loggedin:
            return redirect(url_for('main_menu',user=user.account))

        user.issued_at = datetime.now(pytz.timezone('Asia/Tokyo'))
        if not user.is_used:
            user.is_used = True
        db.session.commit()

        # ユーザーIDをセッションに保存
        session['user_id'] = user.id

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

        # is_endedのチェック
        if user.is_ended:
            flash("もうスタンプラリーはゴールしています", 'error')
            return render_template('login.html', title="ログイン", checkpoint=checkpoint)
        
        # STAMPテーブル内で同じチェックポイントIDが存在するか確認
        existing_stamp = Stamp.query.filter_by(
            checkpoint_id=checkpoint.id,
            login_id=user.id
        ).first()
        
        if existing_stamp:
            flash("もうスタンプを獲得しました。", 'error')
            return render_template('login.html', title="ログイン", checkpoint=checkpoint)
        
        # ユーザーIDをセッションに保存
        session['user_id'] = user.id
        # チェックポイント画面にリダイレクト
        return redirect(url_for('checkpoint', checkpoint_id=checkpoint.id, login_id=user.id))

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
        
        # ゴールチェック
        if user.is_ended:
            flash("もうスタンプラリーはゴールしています", 'error')
            return render_template("end.html")

        # 必要なチェックポイント（ID: 2-7）の確認
        required_checkpoint_ids = set(range(2, 8))
        obtained_stamps = {stamp.checkpoint_id for stamp in Stamp.query.filter_by(login_id=user.id).all()}
        
        #if not required_checkpoint_ids.issubset(obtained_stamps):
        #    missing_count = len(required_checkpoint_ids - obtained_stamps)
        #    flash(f"ゴールするには、あと{missing_count}つのチェックポイントを回る必要があります。", 'error')
        #    return render_template("login.html", title="ログイン", checkpoint=checkpoint)

        # ログイン状態確認
        if user.is_loggedin:
            return redirect(url_for("show_stamps", user_id=user.id))
            
        # ユーザーIDをセッションに保存
        session['user_id'] = user.id
        return render_template("login.html", title="ログイン", checkpoint=checkpoint)

    return render_template("login.html", title="ログイン", checkpoint=checkpoint)


# ３つのアンケート画面の表示と回答送信
@app.route('/handle_survey/<int:checkpoint_id>', methods=['GET', 'POST'])
def handle_survey(checkpoint_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。再度ログインしてください。', 'error')
        return redirect(url_for('login'))

    if checkpoint_id == 1:
        return survey(checkpoint_id)  # IDが1の時
    elif 2 <= checkpoint_id <= 8:
        return checkpoint_survey(checkpoint_id)  # IDが2から8の時
    elif checkpoint_id == 9:
        return goal_survey(user_id, checkpoint_id)  # user_idも渡すように修正
    else:
        flash('無効なチェックポイントIDです。', 'error')
        return redirect(url_for('view_stamps'))
    
# スタートポイントのアンケート画面のルート
def survey(checkpoint_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。再度ログインしてください。', 'error')
        return redirect(url_for('login'))

    user = Login.query.get_or_404(user_id)

    # 質問と選択肢を一度に取得
    questions = Survey.query.filter_by(checkpoint_id=checkpoint_id)\
        .options(db.joinedload(Survey.survey_choices))\
        .order_by(Survey.survey_order).all()
    
    #if not questions:
    #    flash('アンケートが設定されていません。', 'error')
    #    return redirect(url_for('main_menu', user=user.account))
    
    if request.method == 'POST':
        try:
            responses = []
            proceed = True

            for question in questions:
                # 選択肢の存在する質問に対してのみ処理を行う
                if question.survey_choices:
                    selected_choice_id = request.form.get(f'question_{question.id}')
                    
                    if not selected_choice_id:
                        proceed = False
                        flash(f"質問「{question.question}」に対する選択肢を選んでください。", 'error')
                        break
                    
                    choice = Survey_Choice.query.filter_by(
                        id=selected_choice_id,
                        survey_id=question.id
                    ).first()
                    
                    if not choice:
                        proceed = False
                        flash('無効な選択肢が選択されました。', 'error')
                        break

                    responses.append(Survey_Response(
                        login_id=user.id,
                        survey_id=question.id,
                        value=choice.value,
                    #    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                    ))

            if proceed:
                db.session.add_all(responses)
                user.is_loggedin = True
                db.session.commit()

                flash('スタートアンケートが完了しました！', 'success')
                return redirect(url_for('main_menu', user=user.account))

        except SQLAlchemyError:
            db.session.rollback()
            flash('エラーが発生しました。もう一度お試しください。', 'error')

    return render_template(
        'survey.html',
        title="スタート時アンケート調査",
        questions=questions
    )


# チェックポイントのアンケート画面のルート
def checkpoint_survey(checkpoint_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。再度ログインしてください。', 'error')
        return redirect(url_for('login'))
    
    user = Login.query.get_or_404(user_id)
    
    # 質問と選択肢を一度に取得（N+1問題の回避）
    questions = Survey.query.filter_by(checkpoint_id=checkpoint_id)\
        .options(db.joinedload(Survey.survey_choices))\
        .order_by(Survey.survey_order).all()
    
    if not questions:
        flash('このチェックポイントにはアンケートが設定されていません。', 'error')
        return redirect(url_for('view_stamps', checkpoint_id=checkpoint_id))

    if request.method == 'POST':
        try:
            responses = []
            for question in questions:
                selected_value = request.form.get(f'question_{question.id}')
                if not selected_value:
                    flash(f"質問「{question.question}」に対する選択肢を選んでください。", 'error')
                    return render_template('survey.html', 
                                        title="チェックポイント時アンケート調査", 
                                        questions=questions)

                # 選択肢の妥当性を確認
                choice = Survey_Choice.query.filter_by(
                    id=selected_value,
                    survey_id=question.id
                ).first()
                
                if not choice:
                    flash('無効な選択肢が選択されました。', 'error')
                    return render_template('survey.html', 
                                        title="チェックポイント時アンケート調査", 
                                        questions=questions)

                responses.append(Survey_Response(
                    login_id=user.id,
                    survey_id=question.id,
                    value=choice.value,
                #    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                ))

            # トランザクションとしてまとめて処理
            db.session.add_all(responses)
            db.session.add(Stamp(
                checkpoint_id=checkpoint_id,
                login_id=user.id,
            #    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
            ))
            db.session.commit()
            
            flash('アンケートと訪問記録が保存されました。', 'success')
            return redirect(url_for('view_stamps', checkpoint_id=checkpoint_id))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('エラーが発生しました。もう一度お試しください。', 'error')
            return render_template('survey.html', 
                                title="チェックポイント時アンケート調査", 
                                questions=questions)

    return render_template('survey.html', 
                         title="チェックポイント時アンケート調査", 
                         questions=questions)


# ゴールポイントのアンケート画面
@app.route("/goal_survey/<int:user_id>/<int:checkpoint_id>", methods=["GET", "POST"])
def goal_survey(user_id, checkpoint_id):
    if not user_id:
        user_id = session.get('user_id')
        if not user_id:
            flash('セッションが切れました。再度ログインしてください。', 'error')
            return redirect(url_for('login'))

    user = Login.query.get_or_404(user_id)

    if request.method == "POST":
        questions = Survey.query.filter_by(checkpoint_id=checkpoint_id)\
            .options(db.joinedload(Survey.survey_choices))\
            .order_by(Survey.survey_order).all()
        
        responses = []
        proceed = True

        for question in questions:
            # 選択肢が存在する質問のみ処理
            if question.survey_choices:
                selected_choice_id = request.form.get(f'question_{question.id}')
                if not selected_choice_id:
                    flash(f"質問「{question.question}」に対する選択肢を選んでください。", 'error')
                    proceed = False
                    break

                choice = Survey_Choice.query.get(selected_choice_id)
                if not choice or choice.survey_id != question.id:
                    flash('無効な選択肢が選択されました。', 'error')
                    proceed = False
                    break

                responses.append(Survey_Response(
                    login_id=user_id,
                    survey_id=question.id,
                    value=choice.value,
                #    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                ))

        if proceed:
            try:
                # スタンプを追加
                new_stamp = Stamp(
                    checkpoint_id=checkpoint_id,
                    login_id=user_id,
                #    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                )
                db.session.add(new_stamp)
                
                # 回答を追加
                db.session.add_all(responses)
                
                # ユーザーのステータスを更新
                user.is_ended = True
                
                db.session.commit()
                flash('ゴールアンケートが完了しました！', 'success')
                return redirect(url_for("goal"))
            except SQLAlchemyError:
                db.session.rollback()
                flash('エラーが発生しました。もう一度お試しください。', 'error')

    # GETリクエストまたはPOSTでエラーの場合
    questions = Survey.query.filter_by(checkpoint_id=checkpoint_id)\
        .options(db.joinedload(Survey.survey_choices))\
        .order_by(Survey.survey_order).all()
    
    if not questions:
        flash('アンケートが設定されていません。', 'error')
        return redirect(url_for('main_menu'))
    
    return render_template(
        "survey.html",
        title="ゴール時アンケート調査",
        questions=questions
    )

# メインメニュー画面
@app.route('/main_menu')
def main_menu():
    # セッションからユーザーIDを取得
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。再度ログインしてください。', 'error')
        return redirect(url_for('login'))

    # ユーザー情報を取得
    user = Login.query.get_or_404(user_id)
    
    return render_template('main_menu.html', 
                         title="メインメニュー",
                         user=user)  # userオブジェクトをテンプレートに渡す

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

        # STAMPテーブルに新しいレコードを挿入
        new_stamp = Stamp(checkpoint_id=1, login_id=user.id) #created_at=datetime.now(pytz.timezone('Asia/Tokyo')))
        db.session.add(new_stamp)
        db.session.commit()

        # アンケート画面にリダイレクト
        return redirect(url_for('handle_survey', checkpoint_id=new_stamp.checkpoint_id))  # 新しく作成したスタンプのcheckpoint_idを使用 # ここで適切なcheckpoint_idを指定

    return render_template('agreement.html', title="同意確認", user=user)

#ゲット済みのスタンプ確認ページ
@app.route('/view_stamps')
def view_stamps():
    user_id = session.get('user_id')
    if not user_id:
        flash('セッションが切れました。再度ログインしてください。', 'error')
        return redirect(url_for('login'))

    user = Login.query.get_or_404(user_id)

    # 取得済みのスタンプと全チェックポイントの情報を取得
    # created_atで降順にソートして最新の取得情報を取得できるようにする
    obtained_stamps = db.session.query(
        Stamp.checkpoint_id,
        db.func.max(Stamp.created_at).label('latest_stamp'),
        db.func.count(Stamp.id).label('visit_count')
    ).filter_by(login_id=user.id
    ).group_by(Stamp.checkpoint_id
    ).all()

    # チェックポイント情報を取得（order_by checkpoint_orderで順序を保証）
    all_checkpoints = Checkpoint.query.order_by(Checkpoint.checkpoint_order).all()

    # 取得済みスタンプの情報をディクショナリに変換
    stamp_info = {
        stamp.checkpoint_id: {
            'latest_stamp': stamp.latest_stamp,
            'visit_count': stamp.visit_count
        } for stamp in obtained_stamps
    }

    # 全チェックポイントと取得状況をまとめる
    checkpoint_data = []
    for checkpoint in all_checkpoints:
        stamp_data = stamp_info.get(checkpoint.id, {})
        checkpoint_data.append({
            'id': checkpoint.id,
            'name': checkpoint.name,
            'description': checkpoint.description,
            'type': checkpoint.checkpoint_type,
            'is_obtained': checkpoint.id in stamp_info,
            'latest_stamp': stamp_data.get('latest_stamp'),
            'visit_count': stamp_data.get('visit_count', 0)
        })

    return render_template(
        'view_stamps.html',
        title="ゲット済みのスタンプ",
        checkpoints=checkpoint_data,
        user=user
    )





####チェックポイント:画面ビジネスロジック


#チェックポイントの詳細の表示
@app.route('/checkpoint/<int:checkpoint_id>')
def checkpoint(checkpoint_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('このページを見るにはログインが必要です。', 'error')
        return redirect(url_for('login'))

    # ユーザーの取得と確認
    user = Login.query.get_or_404(user_id)
    if not user.is_loggedin:
        flash('スタートポイントでのアンケートを完了してからチェックポイントにアクセスしてください。', 'error')
        return redirect(url_for('handle_checkpoint', checkpoint_id_hash=hash_keys[0]))  # スタートポイント（ID:1）のログイン画面へリダイレクト

    checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
    return render_template(
        'checkpoint.html', 
        checkpoint=checkpoint,
        user=user
    )

#クイズ画面の表示と回答処理
@app.route('/quiz/<int:checkpoint_id>', methods=['GET', 'POST'])
def quiz(checkpoint_id):
    user_id = session.get('user_id')  # セッションからユーザーIDを取得

    user = Login.query.get(user_id)  # ユーザーを取得
    quiz_order = request.args.get('quiz_order', default=1, type=int)
    quiz = Quiz.query.filter_by(checkpoint_id=checkpoint_id, quiz_order=quiz_order).first()

    if request.method == 'POST':
        answer_selected = request.form['answer']
        if not answer_selected:  # 選択肢が選ばれていない場合
            flash("選択肢を選んでください。", 'error')
            return render_template('quiz.html', quiz=quiz)  # 同じページを再表示
        is_correct = (answer_selected == quiz.correct)

        # Quiz_Response テーブルに回答結果を記録
        quiz_response = Quiz_Response(
            login_id=user.id, 
            quiz_id=quiz.id,
            answer_selected=answer_selected,
            is_corrected=is_correct
        )
        db.session.add(quiz_response)
        db.session.commit()
        
        if is_correct:
            flash("正解です")
            # 次のクイズへの遷移（順次 quiz_order を更新する処理を追加した）
            next_quiz = Quiz.query.filter_by(checkpoint_id=checkpoint_id, quiz_order=quiz_order + 1).first()
            if next_quiz:
                return redirect(url_for('quiz', checkpoint_id=checkpoint_id, quiz_order=quiz_order + 1))
            else:
                flash("全てのクイズが終了しました。")
                return redirect(url_for('handle_survey', checkpoint_id=checkpoint_id))  # チェックポイントのアンケートに遷移
    
    return render_template('quiz.html', quiz=quiz)



####ゴール画面:ビジネスロジック



# スタンプ一覧の表示
@app.route("/stamps/<int:user_id>")
def show_stamps(user_id):
    # チェックポイントとユーザーのスタンプ情報を取得
    checkpoints = Checkpoint.query.order_by(Checkpoint.checkpoint_order).all()
    user_stamps = set(stamp.checkpoint_id for stamp in Stamp.query.filter_by(login_id=user_id).all())

    # 必要なチェックポイント（ID: 2-7）のIDセット
    required_checkpoint_ids = set(range(2, 8))  # 2から7まで
    
    # 収集済みの必要なチェックポイントの数を計算
    collected_stamps = len(required_checkpoint_ids.intersection(user_stamps))
    total_required = len(required_checkpoint_ids)  # 必要なチェックポイント数（6個）

    # ゴールチェックポイント（ID: 9）を取得
    goal_checkpoint = Checkpoint.query.filter_by(id=9).first()
    
    # アンケートボタンのアクティブ化条件：
    # 1. ID 2-7のチェックポイントをすべて収集している
    # 2. まだゴール（ID: 9）のスタンプを取得していない
    active_survey = (collected_stamps >= total_required and 
                    goal_checkpoint and 
                    goal_checkpoint.id not in user_stamps)

    # ゴールのアンケート用チェックポイント
    survey_checkpoints = [goal_checkpoint] if active_survey and goal_checkpoint else []

    # テンプレートにデータを渡す
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

