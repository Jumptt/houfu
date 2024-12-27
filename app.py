import os
from flask import Flask, render_template, request
import openai
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired
from openai import OpenAI

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# OpenAI APIキーの設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# フォームの定義
class ProfileForm(FlaskForm):
    age = SelectField('年齢', choices=[
        ('10代', '10代'), 
        ('20代', '20代'), 
        ('30代', '30代'), 
        ('40代', '40代'), 
        ('50代', '50代'), 
        ('60代', '60代'), 
        ('70歳以上', '70歳以上')
    ], validators=[DataRequired()])
    gender = SelectField('性別', choices=[
        ('男性', '男性'), 
        ('女性', '女性'), 
        ('その他', 'その他')
    ], validators=[DataRequired()])
    hobbies = SelectMultipleField('趣味', choices=[
        ('読書', '読書'), 
        ('スポーツ', 'スポーツ'), 
        ('旅行', '旅行'), 
        ('音楽', '音楽'), 
        ('料理', '料理'), 
        ('映画鑑賞', '映画鑑賞'),
        ('ゲーム', 'ゲーム'),
        ('アート', 'アート'),
        ('テクノロジー', 'テクノロジー'),
        ('その他', 'その他')
    ])
    submit = SubmitField('抱負を生成')

# ルーティング
@app.route('/', methods=['GET', 'POST'])
def index():
    form = ProfileForm()
    if form.validate_on_submit():
        # プロフィール情報の取得
        age = form.age.data
        gender = form.gender.data
        hobbies = ', '.join(form.hobbies.data) if form.hobbies.data else '特になし'

        # OpenAI APIへのリクエスト
        prompt = f"あなたは{age}の{gender}です。趣味は{hobbies}。新年の抱負を10個提案してください。抱負だけを通し番号と共に返し、他の出力は一切しないでください。"
        # OpenAIクライアントのインスタンスを作成
        client = OpenAI(api_key=openai.api_key)

        # チャット補完を作成
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.7,
        )

        # 抱負の取得と加工
        resolutions = response.choices[0].message.content.strip().split('\n')
        resolutions = [res.strip('- ').strip() for res in resolutions if res]

        return render_template('results.html', resolutions=resolutions)
    return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)