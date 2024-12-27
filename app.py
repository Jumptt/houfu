import os
import uuid
from flask import Flask, render_template, request, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired
from PIL import Image, ImageDraw, ImageFont
from flask_migrate import Migrate

# 追加のインポート
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
from flask import request, Response
import os


# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# OpenAIクライアントのインスタンスを作成
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# もし環境変数が設定されていない場合、エラーを出すことも検討してください
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEYが設定されていません。環境変数または設定ファイルを確認してください。")


# データベースの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usage_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# データベースのインスタンスを作成
db = SQLAlchemy(app)

# Flask-Migrateのインスタンスを作成
migrate = Migrate(app, db)
# データベースモデルの定義
class UsageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    hobbies = db.Column(db.String(200), nullable=False)
    occupation = db.Column(db.String(50), nullable=False)
    health_focus = db.Column(db.String(200), nullable=False)
    values = db.Column(db.String(200), nullable=False)
    resolutions = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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
    occupation = SelectField('職業', choices=[
        ('学生', '学生'),
        ('会社員', '会社員'),
        ('自営業', '自営業'),
        ('主婦・主夫', '主婦・主夫'),
        ('退職者', '退職者'),
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
    health_focus = SelectMultipleField('健康に関する関心事', choices=[
        ('フィットネス', 'フィットネス'),
        ('ダイエット', 'ダイエット'),
        ('メンタルヘルス', 'メンタルヘルス'),
        ('睡眠', '睡眠'),
        ('栄養', '栄養'),
        ('ストレス管理', 'ストレス管理'),
        ('その他', 'その他')
    ])
    values = SelectMultipleField('大切にしている価値観', choices=[
        ('家族', '家族'),
        ('友情', '友情'),
        ('キャリア', 'キャリア'),
        ('学習', '学習'),
        ('創造性', '創造性'),
        ('健康', '健康'),
        ('自由', '自由'),
        ('冒険', '冒険'),
        ('貢献', '貢献'),
        ('その他', 'その他')
    ])
    submit = SubmitField('抱負を生成')

# 抱負を画像として生成する関数（変更なし）
def generate_image(resolutions, filename):
    # 画像サイズと背景色の設定
    img_width = 800
    img_height = 1200
    background_color = (255, 250, 250)  # 背景色（薄いピンク）

    # 画像の作成
    image = Image.new('RGB', (img_width, img_height), background_color)
    draw = ImageDraw.Draw(image)

    # フォントの設定（フォントファイルのパスを適宜変更してください）
    font_path = os.path.join('fonts', 'NotoSansJP-VariableFont_wght.ttf')  # 日本語対応のフォントファイルを指定
    if not os.path.exists(font_path):
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, size=32)

    # タイトルの描画
    title = "🎍 あなたへの新年の抱負 🎍"
    text_color = (178, 34, 34)  # ダークレッド
    # テキストのバウンディングボックスを取得
    bbox = font.getbbox(title)
    w = bbox[2] - bbox[0]  # 幅
    h = bbox[3] - bbox[1]  # 高さ
    draw.text(((img_width - w) / 2, 50), title, fill=text_color, font=font)

    # 抱負の描画
    font = ImageFont.truetype(font_path, size=24)
    y_text = 150
    for res in resolutions:
        res = res.strip("0123456789. ")
        draw.text((50, y_text), f"- {res}", fill=(0, 0, 0), font=font)
        y_text += 40  # 行間

    # 画像の保存
    image_path = os.path.join('static', 'images', filename)
    image.save(image_path)

# 管理者認証の関数（前回の内容から追加）
def check_auth(username, password):
    """管理者のユーザー名とパスワードを確認"""
    return username == 'admin' and password == 'your_password'

def authenticate():
    """認証が必要な場合のレスポンスを返す"""
    resp = Response('管理者ページにアクセスするには認証が必要です。\n再度認証情報を入力してください。', 401)
    resp.headers['WWW-Authenticate'] = 'Basic realm="Login Required"'
    return resp

def requires_auth(f):
    """特定のルートに認証を要求するデコレータ"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ルーティング
@app.route('/', methods=['GET', 'POST'])
def index():
    form = ProfileForm()
    if form.validate_on_submit():
        # プロフィール情報の取得
        age = form.age.data
        gender = form.gender.data
        occupation = form.occupation.data
        hobbies = ', '.join(form.hobbies.data) if form.hobbies.data else '特になし'
        health_focus = ', '.join(form.health_focus.data) if form.health_focus.data else '特になし'
        values = ', '.join(form.values.data) if form.values.data else '特になし'

        # OpenAI APIへのリクエスト
        prompt = f"""あなたは{age}の{gender}で、職業は{occupation}です。
趣味は{hobbies}。
健康に関する関心事は{health_focus}。
あなたが大切にしている価値観は{values}。
以上の情報をもとに、新年の抱負を10個提案してください。
抱負だけを通し番号と共に返し、他の出力は一切しないでください。"""

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

        # 画像を生成
        filename = f"resolutions_{uuid.uuid4().hex}.png"
        generate_image(resolutions, filename)

        # 利用履歴をデータベースに保存
        new_record = UsageHistory(
            age=age,
            gender=gender,
            occupation=occupation,
            hobbies=hobbies,
            health_focus=health_focus,
            values=values,
            resolutions='\n'.join(resolutions)
        )
        db.session.add(new_record)
        db.session.commit()

        return render_template('results.html', resolutions=resolutions, image_filename=filename)
    return render_template('index.html', form=form)

# 画像のダウンロード
@app.route('/download/<filename>')
def download_image(filename):
    return send_from_directory(os.path.join('static', 'images'), filename, as_attachment=True)

# 利用履歴の表示（管理者用）
@app.route('/admin/usage_history')
@requires_auth
def view_usage_history():
    records = UsageHistory.query.order_by(UsageHistory.timestamp.desc()).all()
    return render_template('usage_history.html', records=records)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)