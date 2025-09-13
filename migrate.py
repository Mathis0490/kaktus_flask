#!/usr/bin/env python3
# migrate_simple.py - Migration ohne QR-Code Abhängigkeit

from datetime import datetime
import sys
import os

# Importiere nur das Nötigste
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# App Setup (minimal)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kaktus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Minimale Modell-Definitionen
class Species(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(50))
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'))
    purchase_date = db.Column(db.Date)
    location = db.Column(db.String(200))
    substrate = db.Column(db.String(200))
    species = db.relationship('Species')

def generate_simple_batch_id(species_id, pot_number):
    """Einfache Batch-ID ohne externe Abhängigkeiten"""
    now = datetime.now()
    year_month = now.strftime('%y%m')
    
    species = Species.query.get(species_id)
    if species:
        species_code = ''.join(species.name.split()[:2])[:3].upper()
    else:
        species_code = 'UNK'
    
    pot_code = pot_number or 'XX'
    
    # Zähle existierende
    existing = Plant.query.filter(Plant.batch_id.like(f'{year_month}-{species_code}%')).count()
    sequence = str(existing + 1).zfill(3)
    
    return f"{year_month}-{species_code}-{pot_code}-{sequence}"

def migrate():
    with app.app_context():
        print("🔄 Starte Migration (Simple Version)...")
        
        # Backup
        import shutil
        if os.path.exists('kaktus.db'):
            backup_name = f"kaktus_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy('kaktus.db', backup_name)
            print(f"💾 Backup erstellt: {backup_name}")
        
        # Migration
        plants = Plant.query.filter_by(batch_id=None).all()
        
        if not plants:
            print("✅ Keine Migration nötig")
            return
        
        print(f"📦 Gefunden: {len(plants)} Pflanzen ohne Batch-ID")
        
        for i, plant in enumerate(plants, 1):
            plant.batch_id = generate_simple_batch_id(plant.species_id, f"M{plant.id}")
            print(f"  [{i}/{len(plants)}] ✓ ID {plant.id} → Batch {plant.batch_id}")
        
        db.session.commit()
        print(f"\n✅ Fertig! {len(plants)} Pflanzen migriert")

if __name__ == "__main__":
    migrate()
