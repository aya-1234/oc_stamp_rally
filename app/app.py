from flask import Flask, request, render_template, flash, url_for, session, redirect, jsonify
import sqlite3
from datetime import datetime
import pytz
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from init import db, initialize_db, Login, Checkpoint, Quiz, Quiz_Response, Stamp, Survey, Survey_Choice, Survey_Response 
from services.user_service import authenticate_user
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_wtf import CSRFProtect
from functools import wraps
import os
from sqlalchemy import or_

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

checkpoint_hash_dic = {'ajrwkhlkafsddfd': 1,
                       'syflwdehkejhrsd1': 2, 
                       'syflwehkejwhrsd2': 3, 
                       'syflwehkejwhrsd3': 4, 
                       'syflwehkejwhrsd4': 5, 
                       'syflwehkejwhrsd5': 6, 
                       'syflwehkejwhrsd6': 7, 
                       'syflwehkejwhrsd7': 8, 
                       'syflwehkejwhrsd8': 9,
                       'syflwehkejwhrsd9': 10,  
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
    
    return render_template(
        'admin/panel.html',
        users_pagination=users_pagination,  # users から users_pagination に変更
        checkpoints=checkpoints,
        surveys=surveys,
        survey_choices=survey_choices,
        quizzes=quizzes,
        admin_hash=hash_keys[9],
        search_query=search_query
    )

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
        
        if not required_checkpoint_ids.issubset(obtained_stamps):
            missing_count = len(required_checkpoint_ids - obtained_stamps)
            flash(f"ゴールするには、あと{missing_count}つのチェックポイントを回る必要があります。", 'error')
            return render_template("login.html", title="ログイン", checkpoint=checkpoint)

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

