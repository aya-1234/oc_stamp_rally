from flask import Flask,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Numeric
from datetime import datetime
import pytz
import pandas as pd
import os
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

    __table_args__ = (
        db.Index('idx_stamp_login_checkpoint', 'login_id', 'checkpoint_id'),
        db.Index('idx_stamp_created_at', 'created_at')
    )

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
            # 現在のファイルのディレクトリパスを取得
            current_dir = os.path.dirname(os.path.abspath(__file__))

            db.session.commit()
            surveys_df = pd.read_csv(os.path.join(current_dir, "description_data.csv"))
            surveys_df.to_sql('CHECKPOINT', con=db.engine, if_exists="append", index=False)

            db.session.commit()
            quizzez_df = pd.read_csv(os.path.join(current_dir, "actual_quiz.csv"))
            quizzez_df.to_sql('QUIZ', con=db.engine, if_exists="append", index=False)

            db.session.commit()
            surveys_df = pd.read_csv(os.path.join(current_dir, "actual_survey.csv"))
            surveys_df.to_sql('SURVEY', con=db.engine, if_exists="append", index=False)

            db.session.commit()
            survey_choices_df = pd.read_csv(os.path.join(current_dir, "actual_survey_choices.csv"))
            survey_choices_df.to_sql('SURVEY_CHOICE', con=db.engine, if_exists="append", index=False)

            db.session.commit()
            logins_df = pd.read_csv(os.path.join(current_dir, "actual_logins.csv"))

            # 現在の日時を取得
            current_time = datetime.now(pytz.timezone('Asia/Tokyo'))

            # issued_atカラムを追加し、現在の日時を設定
            logins_df['issued_at'] = current_time

            # データをデータベースに挿入
            logins_df.to_sql('LOGIN', con=db.engine, if_exists="append", index=False)

            db.session.commit()
            print("データベースの初期化とテストデータの追加が完了しました（またはスキップされました）。")
            return

