import os
import uuid
from flask import Flask, render_template, request, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired
from PIL import Image, ImageDraw, ImageFont

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# OpenAIクライアントのインスタンスを作成
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# 抱負を画像として生成する関数
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

        return render_template('results.html', resolutions=resolutions, image_filename=filename)
    return render_template('index.html', form=form)

# 画像のダウンロード
@app.route('/download/<filename>')
def download_image(filename):
    return send_from_directory(os.path.join('static', 'images'), filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)