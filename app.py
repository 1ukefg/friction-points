from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import folium
import pandas as pd
import csv
import os

app = Flask(__name__)

CSV_FILE = os.path.join('data', 'friction_points.csv')

def generate_map():
    if not os.path.exists(CSV_FILE):
        print("CSV file not found — skipping map generation.")
        return

    df = pd.read_csv(CSV_FILE)

    if df.empty:
        center = [51.5074, -0.1278]
    else:
        latest = df.iloc[-1]
        center = [float(latest['lat']), float(latest['lng'])]

    m = folium.Map(location=center, zoom_start=18)

    for _, row in df.iterrows():
        color = 'red' if int(row['severity']) >= 4 else 'orange' if int(row['severity']) == 3 else 'blue'

        image_html = ""
        if 'image' in row.keys() and pd.notna(row['image']) and row['image']:
            image_url = f"/static/uploads/{row['image']}"
            image_html = f"<br><img src='{image_url}' width='150' style='margin-top:5px;'>"

        popup = folium.Popup(f"""
            <b>{row['type'].title()}</b><br>
            {row['note']}{image_html}
        """, max_width=250)

        folium.Marker(
            location=[float(row['lat']), float(row['lng'])],
            popup=popup,
            icon=folium.Icon(color=color)
        ).add_to(m)

    m.save(os.path.join('static', 'map.html'))

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    type_ = request.form.get('type')
    severity = request.form.get('severity')
    note = request.form.get('note')

    if not (lat and lng and type_ and severity):
        return "Missing data", 400

    image_file = request.files.get('image')
    image_filename = ''
    if image_file and image_file.filename:
        image_filename = secure_filename(image_file.filename)
        os.makedirs('static/uploads', exist_ok=True)
        image_file.save(os.path.join('static/uploads', image_filename))

    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["lat", "lng", "type", "severity", "note", "image"])
        writer.writerow([lat, lng, type_, severity, note, image_filename])

    generate_map()
    return redirect('/map')

@app.route('/map')
def map_view():
    return render_template('map.html')

@app.route('/thanks')
def thanks():
    return "✅ Thanks for your submission!"

if __name__ == '__main__':
    app.run(debug=True)
