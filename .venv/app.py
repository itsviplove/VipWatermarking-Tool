from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
import os
import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_watermark(image_path, text, font_size=20, color="#FFFFFF", position="bottom-right", opacity=0.5):
    img = Image.open(image_path).convert("RGBA")
    watermark = Image.new("RGBA", img.size)
    draw = ImageDraw.Draw(watermark)

    # Convert hex color to RGB and add opacity
    rgb = tuple(int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    rgba = rgb + (int(255 * opacity),)

    # Load font (replace "arial.ttf" with your font path if needed)
    try:
        font = ImageFont.truetype("Arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text position
    text_width, text_height = draw.textsize(text, font=font)
    positions = {
        "top-left": (10, 10),
        "top-right": (img.width - text_width - 10, 10),
        "center": ((img.width - text_width) // 2, (img.height - text_height) // 2),
        "bottom-left": (10, img.height - text_height - 10),
        "bottom-right": (img.width - text_width - 10, img.height - text_height - 10)
    }
    x, y = positions.get(position, positions["bottom-right"])

    # Draw watermark
    draw.text((x, y), text, font=font, fill=rgba)

    # Combine images
    watermarked = Image.alpha_composite(img, watermark)
    return watermarked.convert("RGB")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Validate file
        if 'image' not in request.files:
            return redirect(request.url)
        image = request.files['image']
        if image.filename == '' or not allowed_file(image.filename):
            return "Invalid file! Only PNG/JPG/JPEG allowed.", 400

        # Sanitize filename
        filename = secure_filename(image.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save file
        image.save(upload_path)

        # Process watermark
        watermark_text = request.form['text']
        font_size = int(request.form.get('font_size', 20))
        color = request.form.get('color', '#FFFFFF')
        position = request.form.get('position', 'bottom-right')
        opacity = float(request.form.get('opacity', 0.5))

        # Generate watermarked image
        output = add_watermark(upload_path, watermark_text, font_size, color, position, opacity)

        # Save output
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        output_filename = f"watermarked_{timestamp}.jpg"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        output.save(output_path)

        return render_template('index.html', result=output_filename)

    return render_template('index.html')


@app.route('/download/<filename>')
def download(filename):
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], filename),
        as_attachment=True
    )


if __name__ == '__main__':
    app.run(debug=True)