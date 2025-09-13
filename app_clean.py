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

class Plant(db.Model):
    __tablename__ = 'plant'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(50), unique=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    parent_batch_id = db.Column(db.String(50))
    
    # Status und Tracking
    status = db.Column(db.String(50), default='active')
    stage = db.Column(db.String(50), default='seedling')
    
    # Ursprung
    origin_type = db.Column(db.String(50), default='unknown')
    origin_date = db.Column(db.Date)
    purchase_date = db.Column(db.Date, nullable=False)  # Behalten für Kompatibilität
    sowing_id = db.Column(db.Integer, db.ForeignKey('sowing.id'))
    
    # Physische Eigenschaften
    pot_size = db.Column(db.String(20), default='10cm')
    pot_number = db.Column(db.String(20))
    location = db.Column(db.String(200))
    substrate = db.Column(db.String(200))
    
    # Pflege
    last_watered = db.Column(db.Date)
    last_fertilized = db.Column(db.Date)
    last_repotted = db.Column(db.Date)
    
    # Notizen
    notes = db.Column(db.Text)
    health_status = db.Column(db.String(50), default='healthy')
    
    # Zeitstempel
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehungen
    species = db.relationship('Species', backref='plants')

    @property
    def plant_uid(self):
        """Für Kompatibilität mit alter HTML"""
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
    def qr_code(self):
        """Generiert QR-Code Base64 String"""
        try:
            import qrcode
            from io import BytesIO
            import base64
            
            if not self.batch_id:
                return None
                
            qr = qrcode.QRCode(version=1, box_size=4, border=1)
            qr.add_data(self.batch_id)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
        except:
            return None

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

# ==================== KOPIERE HIER ALLE DEINE ROUTEN ====================
# @app.route('/') etc...

# Am Ende:
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
