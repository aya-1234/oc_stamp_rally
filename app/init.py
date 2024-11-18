from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Numeric
from datetime import datetime
import pytz
import pandas as pd
#actual_loginsとかの名前にする。


db = SQLAlchemy()

class Checkpoint(db.Model):
    __tablename__ = 'CHECKPOINT'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    checkpoint_order = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(300), unique=True, nullable=False)
    checkpoint_type = db.Column(db.String(10), nullable=False)
    __table_args__ = (
        CheckConstraint("checkpoint_type IN ('normal', 'start', 'goal')", name='check_point_type'),
    )

class Login(db.Model):#Update処理で。
    __tablename__ = 'LOGIN'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    is_used = db.Column(db.Boolean, nullable=False,default=False)#デフォルト値をFalseにしないと
    account = db.Column(db.String(20), unique=True, nullable=False)
    is_loggedin = db.Column(db.Boolean, nullable=False)
    is_agree = db.Column(db.Boolean, nullable=False)
    is_ended = db.Column(db.Boolean, nullable=False)
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Tokyo')), nullable=False)#自動追加、自動採番のようなもの。

class Quiz(db.Model):#quiz_orderは３択ではないほうの大きなCPごとの３つの質問番号。１，２，３，１，２，３のように並べる。
    __tablename__ = 'QUIZ'#問題文べた付で正解かを判定する。
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    checkpoint_id = db.Column(db.Integer, db.ForeignKey('CHECKPOINT.id'), nullable=False)
    quiz_order = db.Column(Numeric(10, 2), unique=False, nullable=False)
    content = db.Column(db.String(120), nullable=False)
    correct = db.Column(db.String(50), nullable=False)
    answer_1 = db.Column(db.String(50), nullable=False)
    answer_2 = db.Column(db.String(50), nullable=False)
    answer_3 = db.Column(db.String(50), nullable=False)

class Quiz_Response(db.Model):
    __tablename__ = 'QUIZ_RESPONSE'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    login_id = db.Column(db.Integer, db.ForeignKey('LOGIN.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('QUIZ.id'), nullable=False)
    answer_selected = db.Column(db.String(50), unique=False, nullable=False)
    is_corrected = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Tokyo')), nullable=False)
    # Quizとのリレーションシップ
    quiz = db.relationship('Quiz', backref='responses', lazy=True)

class Stamp(db.Model):
    __tablename__ = 'STAMP'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    login_id = db.Column(db.Integer, db.ForeignKey('LOGIN.id'), nullable=False)
    checkpoint_id = db.Column(db.Integer, db.ForeignKey('CHECKPOINT.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Tokyo')), nullable=False)
    # Loginとのリレーションシップ
    login = db.relationship('Login', backref='stamps', lazy=True)

    # Checkpointとのリレーションシップ
    checkpoint = db.relationship('Checkpoint', backref='stamps', lazy=True)
    def __init__(self, login_id, checkpoint_id):
        self.login_id = login_id
        self.checkpoint_id = checkpoint_id

class Survey(db.Model):
    __tablename__ = 'SURVEY'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    checkpoint_id = db.Column(db.Integer, db.ForeignKey('CHECKPOINT.id'), nullable=False)
    question = db.Column(db.String(240), nullable=False)
    survey_order = db.Column(Numeric(10, 2), unique=True, nullable=False)
    # リレーションシップの定義
    survey_choices = db.relationship('Survey_Choice', back_populates='survey', lazy=True)

class Survey_Choice(db.Model):
    __tablename__ = 'SURVEY_CHOICE'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey('SURVEY.id'), nullable=False)
    survey_choice = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    # Surveyとのリレーションシップ
    survey = db.relationship('Survey', back_populates='survey_choices', lazy=True)

class Survey_Response(db.Model):
    __tablename__ = 'SURVEY_RESPONSE'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    login_id = db.Column(db.Integer, db.ForeignKey('LOGIN.id'), nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey('SURVEY.id'), nullable=False)
    value = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Tokyo')), nullable=False)
    # Surveyとのリレーションシップ
    survey = db.relationship('Survey', backref='responses', lazy=True)


# テストデータを追加する関数
def initialize_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all() 

        if db.session.query(Checkpoint).count() == 0:
            # テストデータの作成
            test_checkpoints = [
                Checkpoint(checkpoint_order=1, name="スタート地点", description="この地点からスタンプラリーが始まります。", checkpoint_type="start"),
                Checkpoint(checkpoint_order=2, name="地点1番", description="ここは地点１番です。", checkpoint_type="normal"),
                Checkpoint(checkpoint_order=3, name="地点2番", description="ここは地点２番です。", checkpoint_type="normal"),
                Checkpoint(checkpoint_order=4, name="地点3番", description="ここは地点３番です。", checkpoint_type="normal"),
                Checkpoint(checkpoint_order=5, name="地点4番", description="ここは地点4番です。", checkpoint_type="normal"),
                Checkpoint(checkpoint_order=6, name="地点5番", description="ここは地点5番です。", checkpoint_type="normal"),
                Checkpoint(checkpoint_order=7, name="地点6番", description="ここは地点6番です。", checkpoint_type="normal"),
            #    Checkpoint(checkpoint_order=8, name="地点7番", description="ここは地点7番です。", checkpoint_type="normal"),
                Checkpoint(checkpoint_order=8, name="ゴール地点", description="ここがゴールです。", checkpoint_type="goal")
            ]
            db.session.add_all(test_checkpoints)
            db.session.flush() 

           # test_logins = [#account名は全角にした方がいい。
        #    Login(is_used=False, account="test_user1", is_loggedin=False, is_agree=False, is_ended=False),
         #       Login(is_used=False, account="test_user2", is_loggedin=False, is_agree=False, is_ended=False),
          #      Login(is_used=False, account="test_user3", is_loggedin=False, is_agree=False, is_ended=False),
           #     Login(is_used=False, account="test_user4", is_loggedin=False, is_agree=False, is_ended=False),
            #    Login(is_used=False, account="test_user5", is_loggedin=False, is_agree=False, is_ended=False),
            #    Login(is_used=False, account="test_user6", is_loggedin=False, is_agree=False, is_ended=False),
            #    Login(is_used=False, account="test_user7", is_loggedin=False, is_agree=False, is_ended=False),
            #    Login(is_used=False, account="test_user8", is_loggedin=False, is_agree=False, is_ended=False),
            #    Login(is_used=False, account="test_user9", is_loggedin=False, is_agree=False, is_ended=False),
            #    Login(is_used=False, account="test_user10", is_loggedin=False, is_agree=False, is_ended=False),
            #    Login(is_used=False, account="test_user11", is_loggedin=False, is_agree=False, is_ended=False)
            #]
            #db.session.add_all(test_logins)
            db.session.flush() 

            db.session.commit()
            quizzez_df=pd.read_csv("app/test_quiz.csv")
            quizzez_df.to_sql('QUIZ',con=db.engine,if_exists="append",index=False)

            db.session.commit()
            surveys_df=pd.read_csv("app/test_survey.csv")
            surveys_df.to_sql('SURVEY',con=db.engine,if_exists="append",index=False)

            db.session.commit()
            survey_choices_df=pd.read_csv("app/test_survey_choices.csv")
            survey_choices_df.to_sql('SURVEY_CHOICE',con=db.engine,if_exists="append",index=False)

            db.session.commit()
            logins_df = pd.read_csv("app/test_logins.csv")

            # 現在の日時を取得
            current_time = datetime.now(pytz.timezone('Asia/Tokyo'))

            # issued_atカラムを追加し、現在の日時を設定
            logins_df['issued_at'] = current_time

            # データをデータベースに挿入
            logins_df.to_sql('LOGIN', con=db.engine, if_exists="append", index=False)

            #test_quizzes = [
            #    Quiz(checkpoint_id=test_checkpoints[1].id, quiz_order=1.0, content="テスト問題1", correct="選択肢1", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[1].id, quiz_order=2.0, content="テスト問題2", correct="選択肢2", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[1].id, quiz_order=3.0, content="テスト問題3", correct="選択肢3", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[2].id, quiz_order=1.0, content="テスト問題1", correct="選択肢1", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[2].id, quiz_order=2.0, content="テスト問題2", correct="選択肢2", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[2].id, quiz_order=3.0, content="テスト問題3", correct="選択肢3", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[3].id, quiz_order=1.0, content="テスト問題1", correct="選択肢1", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[3].id, quiz_order=2.0, content="テスト問題2", correct="選択肢2", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[3].id, quiz_order=3.0, content="テスト問題3", correct="選択肢3", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[4].id, quiz_order=1.0, content="テスト問題1", correct="選択肢1", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[4].id, quiz_order=2.0, content="テスト問題2", correct="選択肢2", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[4].id, quiz_order=3.0, content="テスト問題3", correct="選択肢3", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[5].id, quiz_order=1.0, content="テスト問題1", correct="選択肢1", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[5].id, quiz_order=2.0, content="テスト問題2", correct="選択肢2", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[5].id, quiz_order=3.0, content="テスト問題3", correct="選択肢3", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[6].id, quiz_order=1.0, content="テスト問題1", correct="選択肢1", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[6].id, quiz_order=2.0, content="テスト問題2", correct="選択肢2", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[6].id, quiz_order=3.0, content="テスト問題3", correct="選択肢3", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[7].id, quiz_order=1.0, content="テスト問題1", correct="選択肢1", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[7].id, quiz_order=2.0, content="テスト問題2", correct="選択肢2", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3"),
            #    Quiz(checkpoint_id=test_checkpoints[7].id, quiz_order=3.0, content="テスト問題3", correct="選択肢3", answer_1="選択肢1", answer_2="選択肢2", answer_3="選択肢3")
           # ]
           # db.session.add_all(test_quizzes)
           # db.session.flush()

           # test_surveys = [
           #      Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問1", survey_order=1.0),
           #      Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問2", survey_order=2.0),
           #      Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問3", survey_order=3.0),
           #      Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問4", survey_order=4.0),
           #      Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問5", survey_order=5.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問6", survey_order=6.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問7", survey_order=7.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_1", survey_order=8.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_2", survey_order=9.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_3", survey_order=10.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_4", survey_order=11.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_5", survey_order=12.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_6", survey_order=13.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_7", survey_order=14.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_8", survey_order=15.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_9", survey_order=16.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_10", survey_order=17.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_11", survey_order=18.0),
           #     Survey(checkpoint_id=test_checkpoints[0].id, question="テストアンケートの質問8_12", survey_order=19.0),
           #     Survey(checkpoint_id=test_checkpoints[1].id, question="テストアンケートの質問_地点1番", survey_order=20.0),
           #     Survey(checkpoint_id=test_checkpoints[2].id, question="テストアンケートの質問_地点2番", survey_order=21.0),
           #     Survey(checkpoint_id=test_checkpoints[3].id, question="テストアンケートの質問_地点3番", survey_order=22.0),
           #     Survey(checkpoint_id=test_checkpoints[4].id, question="テストアンケートの質問_地点4番", survey_order=23.0),
           #     Survey(checkpoint_id=test_checkpoints[5].id, question="テストアンケートの質問_地点5番", survey_order=24.0),
           #     Survey(checkpoint_id=test_checkpoints[6].id, question="テストアンケートの質問_地点6番", survey_order=25.0), 
           #     Survey(checkpoint_id=test_checkpoints[7].id, question="テストアンケートの質問_地点7番", survey_order=26.0),                 
           #     Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問1", survey_order=27.0),
           #     Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問2", survey_order=28.0),
           #     Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問3", survey_order=29.0),
           #     Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問4", survey_order=30.0),
           #     Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問5", survey_order=31.0)
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問6", survey_order=32.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_1", survey_order=33.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_2", survey_order=34.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_3", survey_order=35.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_4", survey_order=36.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_5", survey_order=37.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_6", survey_order=38.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_7", survey_order=39.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_8", survey_order=40.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_9", survey_order=41.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_10", survey_order=42.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_11", survey_order=43.0),
             #   Survey(checkpoint_id=test_checkpoints[8].id, question="ゴールテストアンケートの質問7_12", survey_order=44.0)
           # ]
            #db.session.add_all(test_surveys)
            #db.session.flush()  

           # test_survey_choices = [
            #    Survey_Choice(survey_id=test_surveys[0].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[0].id, survey_choice="選択肢2", value=2),
               # Survey_Choice(survey_id=test_surveys[1].id, survey_choice="選択肢1", value=1),
               # Survey_Choice(survey_id=test_surveys[1].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[2].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[2].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[3].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[3].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[4].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[4].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[5].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[5].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[6].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[6].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[7].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[7].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[8].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[8].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[9].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[9].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[10].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[10].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[11].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[11].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[12].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[12].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[13].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[13].id, survey_choice="選択肢2", value=2),
             #   Survey_Choice(survey_id=test_surveys[14].id, survey_choice="選択肢1", value=1),
              #  Survey_Choice(survey_id=test_surveys[14].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[15].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[15].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[16].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[16].id, survey_choice="選択肢2", value=2)
            #   Survey_Choice(survey_id=test_surveys[17].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[17].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[18].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[18].id, survey_choice="選択肢2", value=2), 
            #    Survey_Choice(survey_id=test_surveys[19].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[19].id, survey_choice="選択肢2", value=2)
            #    Survey_Choice(survey_id=test_surveys[26].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[26].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[27].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[27].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[28].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[28].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[29].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[29].id, survey_choice="選択肢2", value=2),
            #    Survey_Choice(survey_id=test_surveys[30].id, survey_choice="選択肢1", value=1),
            #    Survey_Choice(survey_id=test_surveys[30].id, survey_choice="選択肢2", value=2)     
            #]
            #db.session.add_all(test_survey_choices)
            #db.session.flush()  

            test_stamps = [
                Stamp(1, checkpoint_id=test_checkpoints[0].id),
                Stamp(2, checkpoint_id=test_checkpoints[0].id),
                Stamp(2, checkpoint_id=test_checkpoints[1].id),
                Stamp(2, checkpoint_id=test_checkpoints[2].id),
                Stamp(2, checkpoint_id=test_checkpoints[3].id),
                Stamp(2, checkpoint_id=test_checkpoints[4].id),
                Stamp(2, checkpoint_id=test_checkpoints[5].id),
                Stamp(2, checkpoint_id=test_checkpoints[6].id),
            #    Stamp(2, checkpoint_id=test_checkpoints[7].id)
            ]
            db.session.add_all(test_stamps)
            db.session.flush()  

            db.session.commit()
            print("データベースの初期化とテストデータの追加が完了しました（またはスキップされました）。")
            return
