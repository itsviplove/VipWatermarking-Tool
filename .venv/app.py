from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
import base64
import io
import os
import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_watermark(img, text, font_size=20, color="#FFFFFF", position="bottom-right", opacity=0.5):
    img = Image.open(io.BytesIO(img)).convert("RGBA")
    watermark = Image.new("RGBA", img.size)
    draw = ImageDraw.Draw(watermark)

    # Convert hex color to RGB and add opacity
    rgb = tuple(int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    rgba = rgb + (int(255 * opacity),)

    try:
        font = ImageFont.truetype("Arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    text_width, text_height = draw.textsize(text, font=font)
    positions = {
        "top-left": (10, 10),
        "top-right": (img.width - text_width - 10, 10),
        "center": ((img.width - text_width) // 2, (img.height - text_height) // 2),
        "bottom-left": (10, img.height - text_height - 10),
        "bottom-right": (img.width - text_width - 10, img.height - text_height - 10)
    }
    x, y = positions.get(position, positions["bottom-right"])

    draw.text((x, y), text, font=font, fill=rgba)
    watermarked = Image.alpha_composite(img, watermark)
    return watermarked.convert("RGB")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/preview', methods=['POST'])
def preview():
    try:
        # Get data from AJAX request
        image_data = request.form['image'].split(',')[1]
        text = request.form['text']
        font_size = int(request.form['font_size'])
        color = request.form['color']
        position = request.form['position']
        opacity = float(request.form['opacity'])

        # Decode base64 image
        img_bytes = base64.b64decode(image_data)

        # Process watermark
        output = add_watermark(img_bytes, text, font_size, color, position, opacity)

        # Convert to base64 for preview
        buffered = io.BytesIO()
        output.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({'preview': f"data:image/jpeg;base64,{img_str}"})

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/download', methods=['POST'])
def download():
    try:
        # Get data from request
        image_data = request.form['image'].split(',')[1]
        text = request.form['text']
        font_size = int(request.form['font_size'])
        color = request.form['color']
        position = request.form['position']
        opacity = float(request.form['opacity'])

        # Process image
        img_bytes = base64.b64decode(image_data)
        output = add_watermark(img_bytes, text, font_size, color, position, opacity)

        # Create downloadable file
        buffered = io.BytesIO()
        output.save(buffered, format="JPEG")
        buffered.seek(0)

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return send_file(
            buffered,
            as_attachment=True,
            download_name=f"watermarked_{timestamp}.jpg",
            mimetype="image/jpeg"
        )

    except Exception as e:
        return str(e), 400


if __name__ == '__main__':
    app.run(debug=True)