from flask import Flask, render_template, jsonify, request, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import csv
from io import StringIO, BytesIO
import zipfile

# Flask App erstellen
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kaktus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'kaktus-secret-2024'

# Erweiterungen
db = SQLAlchemy(app)
CORS(app)

# ==================== MODELLE ====================

class Species(db.Model):
    __tablename__ = 'species'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    substrate = db.Column(db.String(200))
    temperature = db.Column(db.String(100))
    germination_time = db.Column(db.String(100))
    care_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Sowing(db.Model):
    __tablename__ = 'sowing'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    sowing_date = db.Column(db.Date, nullable=False)
    seed_count = db.Column(db.Integer, nullable=False)
    pot_number = db.Column(db.String(50), nullable=False)
    germinated = db.Column(db.Boolean, default=False)
    germination_date = db.Column(db.Date)
    germinated_count = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    species = db.relationship('Species', backref='sowings')
    
    @property
    def species_name(self):
        return self.species.name if self.species else "Unbekannt"
    
    @property
    def days_since_sowing(self):
        return (datetime.now().date() - self.sowing_date).days

class Plant(db.Model):
    __tablename__ = 'plant'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(50))
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    parent_batch_id = db.Column(db.String(50))
    status = db.Column(db.String(50), default='active')
    stage = db.Column(db.String(50), default='seedling')
    origin_type = db.Column(db.String(50), default='unknown')
    origin_date = db.Column(db.Date)
    purchase_date = db.Column(db.Date, nullable=False)
    sowing_id = db.Column(db.Integer, db.ForeignKey('sowing.id'))
    pot_size = db.Column(db.String(20), default='10cm')
    pot_number = db.Column(db.String(20))
    location = db.Column(db.String(200))
    substrate = db.Column(db.String(200))
    last_watered = db.Column(db.Date)
    last_fertilized = db.Column(db.Date)
    last_repotted = db.Column(db.Date)
    notes = db.Column(db.Text)
    health_status = db.Column(db.String(50), default='healthy')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    species = db.relationship('Species', backref='plants')

    @property
    def plant_uid(self):
        return self.batch_id or f"P{self.id}"
    
    @property
    def species_name(self):
        return self.species.name if self.species else "Unbekannt"
    
    @property
    def days_since_watering(self):
        if self.last_watered:
            return (datetime.now().date() - self.last_watered).days
        return None
    
    @property
    def age_days(self):
        if self.origin_date:
            return (datetime.now().date() - self.origin_date).days
        elif self.purchase_date:
            return (datetime.now().date() - self.purchase_date).days
        return 0

class DiaryEntry(db.Model):
    __tablename__ = 'diary_entry'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'))
    note = db.Column(db.Text, nullable=False)
    entry_type = db.Column(db.String(50), default='general')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    species = db.relationship('Species', backref='diary_entries')
    
    @property
    def species_name(self):
        return self.species.name if self.species else "Allgemein"

# ==================== HILFSFUNKTIONEN ====================

def generate_batch_id(species_id, pot_number=None):
    """Generiert eindeutige Chargennummer"""
    now = datetime.now()
    year_month = now.strftime('%y%m')
    
    species = Species.query.get(species_id)
    if species:
        species_code = ''.join(species.name.split()[:2])[:3].upper()
    else:
        species_code = 'UNK'
    
    pot_code = pot_number or 'XX'
    existing = Plant.query.filter(Plant.batch_id.like(f'{year_month}-{species_code}%')).count()
    sequence = str(existing + 1).zfill(3)
    
    return f"{year_month}-{species_code}-{pot_code}-{sequence}"

# ==================== ROUTEN ====================

@app.route('/')
def index():
    """Hauptseite - liefert HTML"""
    # Erstelle ein einfaches HTML wenn static/index.html nicht existiert
    if os.path.exists('static/index.html'):
        return app.send_static_file('index.html')
    else:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Kaktus System</title></head>
        <body>
            <h1>🌵 Kaktus System läuft!</h1>
            <p>API Endpoints:</p>
            <ul>
                <li><a href="/api/species">/api/species</a></li>
                <li><a href="/api/sowings">/api/sowings</a></li>
                <li><a href="/api/plants">/api/plants</a></li>
                <li><a href="/api/diary">/api/diary</a></li>
                <li><a href="/api/dashboard-stats">/api/dashboard-stats</a></li>
            </ul>
        </body>
        </html>
        """

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'online', 'timestamp': datetime.now().isoformat()})

@app.route('/api/species', methods=['GET', 'POST'])
def handle_species():
    if request.method == 'GET':
        species = Species.query.all()
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'substrate': s.substrate,
            'temperature': s.temperature,
            'germination_time': s.germination_time,
            'care_notes': s.care_notes
        } for s in species])
    
    elif request.method == 'POST':
        data = request.json
        species = Species(
            name=data['name'],
            substrate=data.get('substrate', 'Mineralisch'),
            temperature=data.get('temperature', '20-25°C'),
            germination_time=data.get('germination_time', '1-4 Wochen'),
            care_notes=data.get('care_notes', '')
        )
        db.session.add(species)
        db.session.commit()
        return jsonify({'id': species.id, 'status': 'created'})

@app.route('/api/sowings', methods=['GET', 'POST'])
def handle_sowings():
    if request.method == 'GET':
        sowings = Sowing.query.all()
        return jsonify([{
            'id': s.id,
            'species': s.species_id,
            'species_name': s.species_name,
            'sowing_date': s.sowing_date.isoformat(),
            'seed_count': s.seed_count,
            'pot_number': s.pot_number,
            'germinated': s.germinated,
            'germination_date': s.germination_date.isoformat() if s.germination_date else None,
            'germinated_count': s.germinated_count,
            'days_since_sowing': s.days_since_sowing,
            'notes': s.notes
        } for s in sowings])
    
    elif request.method == 'POST':
        data = request.json
        sowing = Sowing(
            species_id=data['species'],
            sowing_date=datetime.strptime(data['sowing_date'], '%Y-%m-%d').date(),
            seed_count=int(data['seed_count']),
            pot_number=data['pot_number'],
            notes=data.get('notes', '')
        )
        db.session.add(sowing)
        db.session.commit()
        return jsonify({'id': sowing.id, 'status': 'created'})

@app.route('/api/plants', methods=['GET', 'POST'])
def handle_plants():
    if request.method == 'GET':
        plants = Plant.query.all()
        result = []
        for p in plants:
            try:
                import qrcode
                from io import BytesIO
                import base64
                
                if p.batch_id:
                    qr = qrcode.QRCode(version=1, box_size=4, border=1)
                    qr.add_data(p.batch_id)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    img_str = base64.b64encode(buffer.getvalue()).decode()
                    qr_code = f"data:image/png;base64,{img_str}"
                else:
                    qr_code = None
            except:
                qr_code = None
            
            result.append({
                'id': p.id,
                'batch_id': p.batch_id,
                'plant_uid': p.plant_uid,
                'species': p.species_id,
                'species_name': p.species_name,
                'purchase_date': p.purchase_date.isoformat() if p.purchase_date else None,
                'location': p.location,
                'substrate': p.substrate,
                'notes': p.notes,
                'last_watered': p.last_watered.isoformat() if p.last_watered else None,
                'last_fertilized': p.last_fertilized.isoformat() if p.last_fertilized else None,
                'days_since_watering': p.days_since_watering,
                'status': p.status,
                'stage': p.stage,
                'pot_size': p.pot_size,
                'pot_number': p.pot_number,
                'parent_batch_id': p.parent_batch_id,
                'age_days': p.age_days,
                'qr_code': qr_code
            })
        
        return jsonify(result)
    
    elif request.method == 'POST':
        data = request.json
        
        # Generiere Batch-ID wenn nicht vorhanden
        batch_id = generate_batch_id(data['species'], data.get('pot_number'))
        
        plant = Plant(
            batch_id=batch_id,
            species_id=data['species'],
            purchase_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),
            origin_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),
            location=data.get('location', ''),
            substrate=data.get('substrate', 'Mineralisch'),
            notes=data.get('notes', ''),
            pot_number=data.get('pot_number', ''),
            pot_size=data.get('pot_size', '10cm'),
            status='active',
            stage='adult'
        )
        db.session.add(plant)
        db.session.commit()
        return jsonify({'id': plant.id, 'batch_id': plant.batch_id, 'status': 'created'})

@app.route('/api/plants/<int:plant_id>', methods=['DELETE', 'PATCH'])
def manage_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    
    if request.method == 'DELETE':
        db.session.delete(plant)
        db.session.commit()
        return jsonify({'status': 'deleted'})
    
    elif request.method == 'PATCH':
        data = request.json
        if 'last_watered' in data:
            plant.last_watered = datetime.now().date()
        if 'last_fertilized' in data:
            plant.last_fertilized = datetime.now().date()
        db.session.commit()
        return jsonify({'status': 'updated'})

@app.route('/api/diary', methods=['GET', 'POST'])
def handle_diary():
    if request.method == 'GET':
        entries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
        return jsonify([{
            'id': e.id,
            'date': e.date.isoformat(),
            'species': e.species_id,
            'species_name': e.species_name,
            'note': e.note,
            'entry_type': e.entry_type
        } for e in entries])
    
    elif request.method == 'POST':
        data = request.json
        entry = DiaryEntry(
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            species_id=data.get('species') or None,
            note=data['note'],
            entry_type=data.get('entry_type', 'general')
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({'id': entry.id, 'status': 'created'})

@app.route('/api/sowings/<int:sowing_id>/germinate', methods=['POST'])
def update_germination(sowing_id):
    data = request.json
    sowing = Sowing.query.get_or_404(sowing_id)
    sowing.germinated = True
    sowing.germination_date = datetime.strptime(data['germination_date'], '%Y-%m-%d').date()
    sowing.germinated_count = int(data['germinated_count'])
    db.session.commit()
    return jsonify({'status': 'updated'})

@app.route('/api/dashboard-stats')
def dashboard_stats():
    stats = {
        'overview': {
            'total_species': Species.query.count(),
            'total_sowings': Sowing.query.count(),
            'total_plants': Plant.query.count(),
            'total_diary_entries': DiaryEntry.query.count(),
        }
    }
    return jsonify(stats)

@app.route('/api/export/all')
def export_all():
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Species CSV
        species_csv = StringIO()
        writer = csv.writer(species_csv)
        writer.writerow(['Name', 'Substrat', 'Temperatur', 'Keimdauer'])
        for s in Species.query.all():
            writer.writerow([s.name, s.substrate, s.temperature, s.germination_time])
        zip_file.writestr('arten.csv', species_csv.getvalue().encode('utf-8-sig'))
    
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'kaktus_export_{datetime.now().strftime("%Y%m%d")}.zip'
    )

# NEU: Transfer von Aussaat zu Pflanze
@app.route('/api/sowings/<int:sowing_id>/transfer', methods=['POST'])
def transfer_to_plant_with_batch(sowing_id):
    sowing = Sowing.query.get_or_404(sowing_id)
    data = request.json
    
    batch_id = generate_batch_id(sowing.species_id, sowing.pot_number)
    
    plant = Plant(
        batch_id=batch_id,
        species_id=sowing.species_id,
        origin_type='seed',
        origin_date=sowing.germination_date or sowing.sowing_date,
        purchase_date=sowing.germination_date or sowing.sowing_date,
        sowing_id=sowing_id,
        stage='seedling',
        pot_number=sowing.pot_number,
        pot_size='5cm',
        location=data.get('location', 'Anzucht'),
        substrate='Mineralisch (Anzucht)',
        notes=f"Aus Aussaat vom {sowing.sowing_date}. {sowing.germinated_count}/{sowing.seed_count} gekeimt.",
        status='active'
    )
    
    db.session.add(plant)
    
    sowing.germinated = True
    sowing.germination_date = datetime.strptime(data['germination_date'], '%Y-%m-%d').date()
    sowing.germinated_count = int(data['germinated_count'])
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'batch_id': batch_id,
        'plant_id': plant.id
    })

if __name__ == '__main__':
    # Static Ordner erstellen
    if not os.path.exists('static'):
        os.makedirs('static')
    
    with app.app_context():
        db.create_all()
    
    app.run(host='0.0.0.0', port=5001, debug=True)
