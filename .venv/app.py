from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import os
import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'


def add_watermark(image_path, text, font_size=20):
    img = Image.open(image_path).convert("RGBA")
    watermark = Image.new("RGBA", img.size)
    draw = ImageDraw.Draw(watermark)

    # Customize font (use a system font or provide a .ttf file)
    font = ImageFont.truetype("Arial.ttf", font_size)

    # Position the text (bottom-right corner)
    text_width, text_height = draw.textsize(text, font)
    x = img.width - text_width - 10
    y = img.height - text_height - 10

    # Draw watermark
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))  # White with transparency

    # Combine images
    watermarked = Image.alpha_composite(img, watermark)
    return watermarked.convert("RGB")  # Convert back to RGB for JPEG


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get uploaded file and text
        image = request.files['image']
        watermark_text = request.form['text']

        # Save the uploaded image
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(upload_path)

        # Add watermark
        output = add_watermark(upload_path, watermark_text)

        # Save watermarked image
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