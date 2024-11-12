from flask import Flask, request, render_template, flash, url_for, session, redirect
import sqlite3
from datetime import datetime
import pytz
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from init4 import db, initialize_db, Login, Checkpoint, Quiz, Quiz_Response, Stamp, Survey, Survey_Choice, Survey_Response 
from services.user_service import authenticate_user
#やることは、全部のビジネスロジックと最低限のHTMLでべた付でいい。

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
        output += '</ul><br><a href="/">Back</a>'
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
#これ管理画面もかな、ログインテーブルのフラグ操作チェックポイントのフラグ操作
#なんか正解バグしてる
#SURVEY_CHOICEを設定しない問題を作っておけば選択肢のない問題が作れて、見出しになって２階層になるのでは？？
@app.route('/')
def hello():
    output='''
<h1>Hello World</h1>
<ul>
<li><a href="/logins">ログイン情報</a></li>
<li><a href="/handle_checkpoint/1">スタートポイントログイン</a></li>
<li><a href="/handle_checkpoint/2">チェックポイント地点１ログイン</a></li>
<li><a href="/handle_checkpoint/3">チェックポイント地点２ログイン</a></li>
<li><a href="/handle_checkpoint/4">チェックポイント地点３ログイン</a></li>
<li><a href="/handle_checkpoint/5">チェックポイント地点４ログイン</a></li>
<li><a href="/handle_checkpoint/6">チェックポイント地点５ログイン</a></li>
<li><a href="/handle_checkpoint/7">チェックポイント地点６ログイン</a></li>
<li><a href="/handle_checkpoint/8">チェックポイント地点７ログイン</a></li>
<li><a href="/handle_checkpoint/9">ゴールポイントログイン</a></li>
</ul>
'''
    return output



####3つの共通処理

# ３つのチェックポイントのログイン画面のルート
@app.route('/handle_checkpoint/<int:checkpoint_id>', methods=['GET', 'POST'])
def handle_checkpoint(checkpoint_id):
    if checkpoint_id == 1:
        return login(checkpoint_id)  # IDが1の時はlogin関数を呼び出す
    elif 2 <= checkpoint_id <= 8:
        return checkpoint_login(checkpoint_id)  # IDが2から7の時はcheckpoint_login関数を呼び出す
    elif checkpoint_id == 9:
        return goal_login(checkpoint_id)

    
    # スタートポイントのログイン画面のルート
def login(checkpoint_id):
    if request.method == 'POST':
        account = request.form['account']
        user = Login.query.filter_by(account=account).first()

        # アカウント存在チェック
        if not user:
            flash("アカウントが間違っています", 'error')
            return render_template('login.html', title="ログイン")

        # is_endedのチェック
        if user.is_ended:
            flash("もうスタンプラリーはゴールしています", 'error')
            return render_template('login.html', title="ログイン")

        # is_loggedinのチェック
        if user.is_loggedin:
            return redirect(url_for('main_menu',user=user.account))

        user.issued_at = datetime.now(pytz.timezone('Asia/Tokyo'))
        if not user.is_used:
            user.is_used = True
        db.session.commit()

        # ユーザーIDをセッションに保存
        session['user_id'] = user.id

        return redirect(url_for('agreement', login_id=user.id))  # 同意画面にリダイレクト
    # GETメソッドの場合、チェックポイントIDを使用してログイン画面を表示
    return render_template('login.html', title="ログイン", checkpoint_id=checkpoint_id)

# チェックポイントのログイン画面のルート
def checkpoint_login(checkpoint_id):
    if request.method == 'POST':
        account = request.form['account']
        user = Login.query.filter_by(account=account).first()

        # アカウント存在チェック
        if not user:
            flash("アカウントが間違っています", 'error')
            return render_template('login.html', title="ログイン")

        # is_endedのチェック
        if user.is_ended:
            flash("もうスタンプラリーはゴールしています", 'error')
            return render_template('login.html', title="ログイン")
        
        # STAMPテーブル内で同じチェックポイントIDが存在するか確認
        existing_stamp = Stamp.query.filter_by(checkpoint_id=checkpoint_id, login_id=user.id).first()
        if existing_stamp:
            flash("もうスタンプを獲得しました。", 'error')
            return render_template('login.html', title="ログイン")
        
        # ユーザーIDをセッションに保存
        session['user_id'] = user.id
        # チェックポイント画面にリダイレクト
        return redirect(url_for('checkpoint', checkpoint_id=checkpoint_id, login_id=user.id))
    # GETメソッドの場合、チェックポイントIDを使用してログイン画面を表示
    return render_template('login.html', title="ログイン", checkpoint_id=checkpoint_id)

#ゴール画面のログイン画面のルート
@app.route("/goal_login/<int:checkpoint_id>", methods=["GET", "POST"])
def goal_login(checkpoint_id):
    if request.method == "POST":
        account = request.form["account"]
        user = Login.query.filter_by(account=account).first()
        
        if not user:
            flash("アカウントが間違っています")
            return render_template("login.html", checkpoint_id=checkpoint_id)
        
        # ゴールチェック
        if user.is_ended:
            flash("もうスタンプラリーはゴールしています")
            return render_template("end.html")

        # ログイン状態確認
        if user.is_loggedin:
            return redirect(url_for("show_stamps",  user_id=user.id))
        # ユーザーIDをセッションに保存
        session['user_id'] = user.id

    return render_template("login.html", checkpoint_id=checkpoint_id)


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

    # 質問と選択肢を一度に取得（N+1問題の回避）
    questions = Survey.query.filter_by(checkpoint_id=checkpoint_id)\
        .options(db.joinedload(Survey.survey_choices))\
        .order_by(Survey.survey_order).all()
    
    if not questions:
        flash('アンケートが設定されていません。', 'error')
        return redirect(url_for('main_menu',user=user.account))
    
    if request.method == 'POST':
        try:
            responses = []
            all_selected = True

            for question in questions:
                selected_choice_id = request.form.get(f'question_{question.id}')
                
                # 選択肢が選ばれていない場合
                if not selected_choice_id:
                    all_selected = False
                    flash(f"質問「{question.question}」に対する選択肢を選んでください。", 'error')
                    break
                
                # 選択肢の妥当性を確認
                choice = Survey_Choice.query.filter_by(
                    id=selected_choice_id,
                    survey_id=question.id
                ).first()
                
                if not choice:
                    all_selected = False
                    flash('無効な選択肢が選択されました。', 'error')
                    break

                responses.append(Survey_Response(
                    login_id=user.id,
                    survey_id=question.id,
                    value=choice.value,
                    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                ))

            # すべての質問に対して選択肢が選ばれた場合
            if all_selected:
                # トランザクションとしてまとめて処理
                db.session.add_all(responses)
             #   db.session.add(Stamp(
              #      checkpoint_id=checkpoint_id,
               #     login_id=user.id,
                #    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                #))
                user.is_loggedin = True
                db.session.commit()

                flash('スタートアンケートが完了しました！', 'success')
                return redirect(url_for('main_menu',user=user.account))

        except SQLAlchemyError:
            db.session.rollback()
            flash('エラーが発生しました。もう一度お試しください。', 'error')

    # GETリクエストまたはPOSTでエラーの場合
    return render_template(
        'survey.html',
        title="スタート時アンケート調査",
        questions=questions
    )

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
                    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                ))

            # トランザクションとしてまとめて処理
            db.session.add_all(responses)
            db.session.add(Stamp(
                checkpoint_id=checkpoint_id,
                login_id=user.id,
                created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
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
        questions = Survey.query.filter_by(checkpoint_id=checkpoint_id).order_by(Survey.survey_order).all()
        responses = []
        all_answered = True

        for question in questions:
            selected_choice_id = request.form.get(f'question_{question.id}')
            if not selected_choice_id:
                flash(f"質問「{question.question}」に対する選択肢を選んでください。", 'error')
                all_answered = False
                break

            choice = Survey_Choice.query.get(selected_choice_id)
            if not choice or choice.survey_id != question.id:
                flash('無効な選択肢が選択されました。', 'error')
                all_answered = False
                break

            responses.append(Survey_Response(
                login_id=user_id,
                survey_id=question.id,
                value=choice.value,
                created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
            ))

        if all_answered:
            try:
                # スタンプを追加
                new_stamp = Stamp(
                    checkpoint_id=checkpoint_id,
                    login_id=user_id,
                    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
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
        new_stamp = Stamp(checkpoint_id=1, login_id=user.id, created_at=datetime.now(pytz.timezone('Asia/Tokyo')))
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
#    user_id = session.get('user_id')
 #   if not user_id:
  #      return redirect(url_for('login', checkpoint_id=checkpoint_id))

    checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
    return render_template('checkpoint.html', checkpoint=checkpoint)

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