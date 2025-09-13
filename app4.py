from flask import Flask, render_template, jsonify, request, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import shutil
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
    """Kakteen-Arten"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    substrate = db.Column(db.String(200))
    temperature = db.Column(db.String(100))
    germination_time = db.Column(db.String(100))
    care_notes = db.Column(db.Text)
    temperature_min = db.Column(db.Integer, default=15)
    temperature_max = db.Column(db.Integer, default=30)
    watering_summer = db.Column(db.String(200), default='Mäßig, wenn Substrat trocken')
    watering_winter = db.Column(db.String(200), default='Sehr sparsam bis gar nicht')
    light_requirements = db.Column(db.String(200), default='Hell, aber keine pralle Mittagssonne')
    special_care = db.Column(db.Text)
    user_created = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Beziehungen
    sowings = db.relationship('Sowing', backref='species', lazy=True, cascade='all, delete-orphan')
    plants = db.relationship('Plant', backref='species', lazy=True, cascade='all, delete-orphan')

class Sowing(db.Model):
    """Aussaat-Tracking"""
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
    
    @property
    def germination_rate(self):
        if self.seed_count > 0 and self.germinated:
            return round((self.germinated_count / self.seed_count) * 100, 1)
        return 0
    
    @property
    def days_since_sowing(self):
        return (datetime.now().date() - self.sowing_date).days
    
    @property
    def days_until_germination(self):
        if self.germination_date and self.sowing_date:
            return (self.germination_date - self.sowing_date).days
        return None

class Plant(db.Model):
    """Pflanzenbestand"""
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200))
    substrate = db.Column(db.String(200))
    notes = db.Column(db.Text)
    last_watered = db.Column(db.Date)
    last_fertilized = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def days_in_collection(self):
        return (datetime.now().date() - self.purchase_date).days
    
    @property
    def days_since_watering(self):
        if self.last_watered:
            return (datetime.now().date() - self.last_watered).days
        return None

class DiaryEntry(db.Model):
    """Tagebucheinträge"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'))
    species = db.relationship('Species', backref='diary_entries')
    note = db.Column(db.Text, nullable=False)
    entry_type = db.Column(db.String(50), default='general')  # general, watering, fertilizing, repotting
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== ROUTEN ====================

@app.route('/')
def index():
    """Hauptseite"""
    return app.send_static_file('index.html')

@app.route('/api/health')
def health_check():
    """Health-Check für Sync-Status"""
    return jsonify({
        'status': 'online',
        'server': 'Flask Kaktus-Center',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/species', methods=['GET', 'POST'])
def handle_species():
    """Arten verwalten"""
    if request.method == 'GET':
        species = Species.query.all()
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'substrate': s.substrate,
            'temperature': s.temperature,
            'germination_time': s.germination_time,
            'care_notes': s.care_notes,
            'temperature_min': s.temperature_min,
            'temperature_max': s.temperature_max,
            'watering_summer': s.watering_summer,
            'watering_winter': s.watering_winter,
            'light_requirements': s.light_requirements,
            'special_care': s.special_care,
            'user_created': s.user_created
        } for s in species])
    
    elif request.method == 'POST':
        data = request.json
        # Prüfen ob Art schon existiert
        existing = Species.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': 'Art existiert bereits'}), 400
        
        species = Species(
            name=data['name'],
            substrate=data.get('substrate', 'Mineralisch'),
            temperature=data.get('temperature', '20-25°C'),
            germination_time=data.get('germination_time', '1-4 Wochen'),
            care_notes=data.get('care_notes', ''),
            temperature_min=data.get('temperature_min', 20),
            temperature_max=data.get('temperature_max', 25),
            watering_summer=data.get('watering_summer', 'Mäßig, wenn Substrat trocken'),
            watering_winter=data.get('watering_winter', 'Sehr sparsam bis gar nicht'),
            light_requirements=data.get('light_requirements', 'Hell, aber keine pralle Mittagssonne'),
            special_care=data.get('special_care', ''),
            user_created=True
        )
        db.session.add(species)
        db.session.commit()
        return jsonify({'id': species.id, 'status': 'created'})

@app.route('/api/species/<int:species_id>', methods=['DELETE'])
def delete_species(species_id):
    """Art löschen (nur user_created)"""
    species = Species.query.get_or_404(species_id)
    if not species.user_created:
        return jsonify({'error': 'Standard-Arten können nicht gelöscht werden'}), 403
    
    db.session.delete(species)
    db.session.commit()
    return jsonify({'status': 'deleted'})

@app.route('/api/sowings', methods=['GET', 'POST'])
def handle_sowings():
    """Aussaaten verwalten"""
    if request.method == 'GET':
        sowings = Sowing.query.all()
        return jsonify([{
            'id': s.id,
            'species': s.species_id,
            'species_name': s.species.name,
            'sowing_date': s.sowing_date.isoformat(),
            'seed_count': s.seed_count,
            'pot_number': s.pot_number,
            'germinated': s.germinated,
            'germination_date': s.germination_date.isoformat() if s.germination_date else None,
            'germinated_count': s.germinated_count,
            'germination_rate': s.germination_rate,
            'days_since_sowing': s.days_since_sowing,
            'days_until_germination': s.days_until_germination,
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

@app.route('/api/sowings/<int:sowing_id>', methods=['DELETE'])
def delete_sowing(sowing_id):
    """Aussaat löschen"""
    sowing = Sowing.query.get_or_404(sowing_id)
    db.session.delete(sowing)
    db.session.commit()
    return jsonify({'status': 'deleted'})

@app.route('/api/plants', methods=['GET', 'POST'])
def handle_plants():
    """Pflanzen verwalten"""
    if request.method == 'GET':
        plants = Plant.query.all()
        return jsonify([{
            'id': p.id,
            'species': p.species_id,
            'species_name': p.species.name,
            'purchase_date': p.purchase_date.isoformat(),
            'location': p.location,
            'substrate': p.substrate,
            'notes': p.notes,
            'days_in_collection': p.days_in_collection,
            'last_watered': p.last_watered.isoformat() if p.last_watered else None,
            'last_fertilized': p.last_fertilized.isoformat() if p.last_fertilized else None,
            'days_since_watering': p.days_since_watering
        } for p in plants])
    
    elif request.method == 'POST':
        data = request.json
        plant = Plant(
            species_id=data['species'],
            purchase_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),
            location=data['location'],
            substrate=data['substrate'],
            notes=data.get('notes', '')
        )
        db.session.add(plant)
        db.session.commit()
        return jsonify({'id': plant.id, 'status': 'created'})

@app.route('/api/plants/<int:plant_id>', methods=['DELETE', 'PATCH'])
def manage_plant(plant_id):
    """Pflanze löschen oder aktualisieren"""
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
    """Tagebuch verwalten"""
    if request.method == 'GET':
        entries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
        return jsonify([{
            'id': e.id,
            'date': e.date.isoformat(),
            'species': e.species_id,
            'species_name': e.species.name if e.species else 'Allgemein',
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

@app.route('/api/diary/<int:entry_id>', methods=['DELETE'])
def delete_diary_entry(entry_id):
    """Tagebucheintrag löschen"""
    entry = DiaryEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'status': 'deleted'})

@app.route('/api/sowings/<int:sowing_id>/germinate', methods=['POST'])
def update_germination(sowing_id):
    """Keimung aktualisieren"""
    data = request.json
    sowing = Sowing.query.get_or_404(sowing_id)
    sowing.germinated = True
    sowing.germination_date = datetime.strptime(data['germination_date'], '%Y-%m-%d').date()
    sowing.germinated_count = int(data['germinated_count'])
    db.session.commit()
    return jsonify({'status': 'updated'})

@app.route('/api/care-schedule')
def care_schedule():
    """Pflegeplan für alle Pflanzen"""
    schedule = {
        'daily': [],
        'weekly': [],
        'monthly': [],
        'seasonal': []
    }
    
    # Tägliche Aufgaben
    for sowing in Sowing.query.filter(Sowing.germinated == False).all():
        days = sowing.days_since_sowing
        if days <= 14:
            schedule['daily'].append({
                'type': 'check',
                'priority': 'high',
                'task': f'Keimung prüfen: {sowing.species.name} (Topf {sowing.pot_number})',
                'details': f'Ausgesät vor {days} Tagen. Erwartete Keimdauer: {sowing.species.germination_time}'
            })
    
    # Wöchentliche Aufgaben
    for plant in Plant.query.all():
        if plant.days_since_watering and plant.days_since_watering >= 7:
            schedule['weekly'].append({
                'type': 'watering',
                'priority': 'medium',
                'task': f'Gießen prüfen: {plant.species.name} ({plant.location})',
                'details': f'Zuletzt vor {plant.days_since_watering} Tagen gegossen'
            })
    
    # Monatliche Aufgaben
    for plant in Plant.query.all():
        if plant.last_fertilized:
            days_since = (datetime.now().date() - plant.last_fertilized).days
            if days_since >= 30:
                schedule['monthly'].append({
                    'type': 'fertilizing',
                    'priority': 'low',
                    'task': f'Düngen: {plant.species.name} ({plant.location})',
                    'details': f'Zuletzt vor {days_since} Tagen gedüngt'
                })
        else:
            schedule['monthly'].append({
                'type': 'fertilizing',
                'priority': 'low',
                'task': f'Düngen: {plant.species.name} ({plant.location})',
                'details': 'Noch nie gedüngt'
            })
    
    # Saisonale Aufgaben
    current_month = datetime.now().month
    if current_month in [10, 11]:  # Oktober/November
        schedule['seasonal'].append({
            'type': 'season',
            'priority': 'high',
            'task': 'Winterruhe vorbereiten',
            'details': 'Gießen reduzieren, kühleren Standort suchen'
        })
    elif current_month in [3, 4]:  # März/April
        schedule['seasonal'].append({
            'type': 'season',
            'priority': 'high',
            'task': 'Wachstumsperiode beginnen',
            'details': 'Gießen langsam steigern, umtopfen wenn nötig'
        })
    
    return jsonify(schedule)

@app.route('/api/dashboard-stats')
def dashboard_stats():
    """Dashboard-Statistiken"""
    now = datetime.now()
    month_ago = now - timedelta(days=30)
    
    # Pflegeerinnerungen
    care_alerts = []
    germinated_sowings = Sowing.query.filter(Sowing.germinated == True).all()
    
    for sowing in germinated_sowings:
        if sowing.germination_date:
            days = (now.date() - sowing.germination_date).days
            if days == 14:
                care_alerts.append({
                    'type': 'info',
                    'message': f'{sowing.species.name} (Topf {sowing.pot_number}): 2 Wochen alt - Abhärtung vorbereiten'
                })
            elif days == 42:
                care_alerts.append({
                    'type': 'warning', 
                    'message': f'{sowing.species.name} (Topf {sowing.pot_number}): 6 Wochen alt - Deckel entfernen'
                })
            elif days == 70:
                care_alerts.append({
                    'type': 'success',
                    'message': f'{sowing.species.name} (Topf {sowing.pot_number}): 10 Wochen alt - Erste Düngung möglich'
                })
    
    stats = {
        'overview': {
            'total_species': Species.query.count(),
            'total_sowings': Sowing.query.count(),
            'total_plants': Plant.query.count(),
            'total_diary_entries': DiaryEntry.query.count(),
        },
        'recent': {
            'sowings_this_month': Sowing.query.filter(Sowing.sowing_date >= month_ago.date()).count(),
            'germinations_this_month': Sowing.query.filter(
                Sowing.germination_date >= month_ago.date()
            ).count(),
        },
        'care_alerts': care_alerts
    }
    return jsonify(stats)

@app.route('/api/export/all')
def export_all():
    """Alle Daten als ZIP mit CSVs exportieren"""
    # ZIP-Datei im Speicher erstellen
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Arten exportieren
        species_csv = StringIO()
        writer = csv.writer(species_csv)
        writer.writerow(['Name', 'Substrat', 'Temperatur', 'Keimdauer', 'Pflegehinweise', 
                        'Gießen Sommer', 'Gießen Winter', 'Lichtbedarf'])
        for s in Species.query.all():
            writer.writerow([s.name, s.substrate, s.temperature, s.germination_time, 
                           s.care_notes, s.watering_summer, s.watering_winter, s.light_requirements])
        zip_file.writestr('arten.csv', species_csv.getvalue().encode('utf-8-sig'))
        
        # Aussaaten exportieren
        sowings_csv = StringIO()
        writer = csv.writer(sowings_csv)
        writer.writerow(['Art', 'Aussaat-Datum', 'Topf Nr.', 'Anzahl Samen', 'Gekeimt', 
                        'Keim-Datum', 'Anzahl gekeimt', 'Keimrate %', 'Tage bis Keimung'])
        for s in Sowing.query.all():
            writer.writerow([
                s.species.name, s.sowing_date, s.pot_number, s.seed_count,
                'Ja' if s.germinated else 'Nein', s.germination_date or '', 
                s.germinated_count, s.germination_rate,
                s.days_until_germination or ''
            ])
        zip_file.writestr('aussaaten.csv', sowings_csv.getvalue().encode('utf-8-sig'))
        
        # Pflanzen exportieren
        plants_csv = StringIO()
        writer = csv.writer(plants_csv)
        writer.writerow(['Art', 'Kaufdatum', 'Standort', 'Substrat', 'Tage im Bestand', 
                        'Zuletzt gegossen', 'Zuletzt gedüngt'])
        for p in Plant.query.all():
            writer.writerow([
                p.species.name, p.purchase_date, p.location, p.substrate,
                p.days_in_collection, p.last_watered or 'Nie', p.last_fertilized or 'Nie'
            ])
        zip_file.writestr('pflanzenbestand.csv', plants_csv.getvalue().encode('utf-8-sig'))
        
        # Tagebuch exportieren
        diary_csv = StringIO()
        writer = csv.writer(diary_csv)
        writer.writerow(['Datum', 'Art', 'Typ', 'Notiz'])
        for e in DiaryEntry.query.all():
            writer.writerow([
                e.date, e.species.name if e.species else 'Allgemein',
                e.entry_type, e.note
            ])
        zip_file.writestr('tagebuch.csv', diary_csv.getvalue().encode('utf-8-sig'))
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'kaktus_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    )

# ==================== INITIALISIERUNG ====================

def init_db():
    """Datenbank initialisieren mit allen 36 Arten"""
    with app.app_context():
        # Tabellen erstellen
        db.create_all()
        
        # Prüfen ob schon Arten existieren
        if Species.query.count() == 0:
            print("🌱 Lade alle Kakteen-Arten...")
            
            # Vollständige Artenliste mit erweiterten Pflegeinfos
            all_species = {
                'Ancistrocactus pallidus': {
                    'substrate': 'Mineralisch, kiesig',
                    'temperature': '20-28°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Gute Drainage, kühle Überwinterung bei 5-10°C.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Mäßig, alle 2 Wochen',
                    'watering_winter': 'Trocken halten',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Frosthart bis -7°C'
                },
                'Ariocarpus Mischung': {
                    'substrate': 'Rein mineralisch, kalkhaltig',
                    'temperature': '20-30°C',
                    'germination_time': '1-4 Wochen',
                    'care_notes': 'Sehr langsam wachsend, extrem fäulnisempfindlich, tiefe Töpfe.',
                    'temperature_min': 20,
                    'temperature_max': 30,
                    'watering_summer': 'Sehr sparsam, nur bei Schrumpfung',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Hell, leichte Schattierung',
                    'special_care': 'Nie von oben gießen! Rübenwurzel bildet sich.'
                },
                'Astrophytum asterias': {
                    'substrate': 'Rein mineralisch',
                    'temperature': '20-28°C',
                    'germination_time': '3-14 Tage',
                    'care_notes': 'Sehr schnelle und unkomplizierte Keimer. Superkabuto spaltet genetisch auf.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Regelmäßig, aber mäßig',
                    'watering_winter': 'Fast trocken',
                    'light_requirements': 'Hell, keine pralle Sonne',
                    'special_care': 'Kalkliebend, gelegentlich Eierschalen ins Substrat'
                },
                'Blossfeldia carrizalensis & cyathiformis': {
                    'substrate': 'Rein mineralisch, sauer (z.B. mit Kieselgur)',
                    'temperature': '20-25°C',
                    'germination_time': 'Wochen-Monate',
                    'care_notes': 'Staubfeine Samen, nicht abdecken. Halbschattig. Extrem langsam.',
                    'temperature_min': 20,
                    'temperature_max': 25,
                    'watering_summer': 'Nebeln statt gießen',
                    'watering_winter': 'Leicht feucht',
                    'light_requirements': 'Halbschatten',
                    'special_care': 'Kleinster Kaktus der Welt! Oft gepfropft.'
                },
                'Brasilicactus graessneri & haselbergii': {
                    'substrate': 'Mineralisch',
                    'temperature': '20-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Standard-Aussaat, relativ unkompliziert.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Regelmäßig',
                    'watering_winter': 'Mäßig feucht',
                    'light_requirements': 'Hell bis halbschattig',
                    'special_care': 'Blüht früh und reichlich'
                },
                'Buiningia brevicylindrica': {
                    'substrate': 'Rein mineralisch',
                    'temperature': '22-28°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Brasilianische Art, benötigt höhere Temperaturen und verträgt keine Kälte.',
                    'temperature_min': 22,
                    'temperature_max': 28,
                    'watering_summer': 'Regelmäßig bei Hitze',
                    'watering_winter': 'Warm und trocken halten',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Minimum 15°C im Winter!'
                },
                'Carnegiea gigantea': {
                    'substrate': 'Mineralisch',
                    'temperature': '25-35°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Benötigt hohe Keimtemperaturen. Wachstum ist extrem langsam.',
                    'temperature_min': 25,
                    'temperature_max': 35,
                    'watering_summer': 'Durchdringend bei Hitze',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Volle Wüstensonne',
                    'special_care': 'Der berühmte Saguaro! Wird 200 Jahre alt.'
                },
                'Cintia knizei': {
                    'substrate': 'Rein mineralisch, sehr durchlässig, tiefe Töpfe',
                    'temperature': '18-25°C',
                    'germination_time': 'Wochen-Monate',
                    'care_notes': 'Hochlandart, kühle Nächte vorteilhaft, extrem fäulnisempfindlich.',
                    'temperature_min': 18,
                    'temperature_max': 25,
                    'watering_summer': 'Sehr vorsichtig',
                    'watering_winter': 'Knochentrocken',
                    'light_requirements': 'Sehr hell',
                    'special_care': 'Bolivianische Rarität, oft gepfropft'
                },
                'Cleistocactus strausii': {
                    'substrate': 'Mineralisch mit Sand',
                    'temperature': '25°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Lichtkeimer, nicht abdecken. Relativ unkompliziert.',
                    'temperature_min': 22,
                    'temperature_max': 28,
                    'watering_summer': 'Regelmäßig',
                    'watering_winter': 'Sparsam',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Silbersäulenkaktus, säulenförmig'
                },
                'Copiapoa gigantea & Mischung': {
                    'substrate': 'Rein mineralisch',
                    'temperature': '20-28°C',
                    'germination_time': '1-4 Wochen',
                    'care_notes': 'Tag/Nacht-Temperaturdifferenz (28°C Tag / 20°C Nacht) förderlich.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Sehr sparsam',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Chilenische Küstenwüste, verträgt Nebel'
                },
                'Coryphantha boehmei, calipensis, elephantidens': {
                    'substrate': 'Mineralisch',
                    'temperature': '22-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Keimen in der Regel schnell und zuverlässig.',
                    'temperature_min': 22,
                    'temperature_max': 28,
                    'watering_summer': 'Regelmäßig',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Große Blüten, warzenförmige Struktur'
                },
                'Echinofossulocactus spp': {
                    'substrate': 'Mineralisch, kalkhaltig',
                    'temperature': '20-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Mexikanische Gattung, relativ unkompliziert. Viel Licht und gute Drainage.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Mäßig',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Hell bis vollsonnig',
                    'special_care': 'Charakteristische gewellte Rippen'
                },
                'Epithelantha micromeris': {
                    'substrate': 'Mineralisch, kalkhaltig',
                    'temperature': '15-20°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Bevorzugt etwas kühlere Keimtemperaturen.',
                    'temperature_min': 15,
                    'temperature_max': 20,
                    'watering_summer': 'Vorsichtig',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Winzige weiße Dornen, rosa Früchte'
                },
                'Glandulicactus uncinatus': {
                    'substrate': 'Mineralisch, kiesig',
                    'temperature': '20-28°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Benötigt sehr durchlässiges Substrat und gute Luftbewegung.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Mäßig',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Hakendornen, große Blüten'
                },
                'Homalocephala texensis': {
                    'substrate': 'Rein mineralisch',
                    'temperature': '25-35+°C',
                    'germination_time': '1-4 Wochen',
                    'care_notes': 'SICHERHEIT BEACHTEN! Hartschalig. Säurebehandlung oder hohe Hitze nötig.',
                    'temperature_min': 25,
                    'temperature_max': 35,
                    'watering_summer': 'Bei Hitze durchdringend',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Brennende Sonne',
                    'special_care': 'Teufelskopfkaktus, extrem scharfe Dornen!'
                },
                'Lophophora jourdaniana & Mischung': {
                    'substrate': 'Mineralisch mit <40% organ. Anteil',
                    'temperature': '20-25°C',
                    'germination_time': '8-14 Tage',
                    'care_notes': 'Detaillierte Anleitung beachten. Lichtkeimer.',
                    'temperature_min': 20,
                    'temperature_max': 25,
                    'watering_summer': 'Mäßig, von unten',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Hell, keine pralle Sonne',
                    'special_care': 'Peyote, dornenlos, Rübenwurzel'
                },
                'Maihuenia poeppigii': {
                    'substrate': 'Mineralisch',
                    'temperature': '15-20°C',
                    'germination_time': 'Monate-Jahre',
                    'care_notes': 'Benötigt Kältereiz. Pflanzen benötigen auch im Winter leichte Feuchtigkeit.',
                    'temperature_min': 15,
                    'temperature_max': 20,
                    'watering_summer': 'Regelmäßig',
                    'watering_winter': 'Leicht feucht',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Frosthart bis -20°C! Patagonien.'
                },
                'Maihueniopsis glomeratus': {
                    'substrate': 'Mineralisch',
                    'temperature': '15-20°C',
                    'germination_time': 'Monate-Jahre',
                    'care_notes': 'Hartschalig, Kältebehandlung notwendig. Frosttolerant.',
                    'temperature_min': 15,
                    'temperature_max': 20,
                    'watering_summer': 'Mäßig',
                    'watering_winter': 'Trocken bei Frost',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Anden-Hochgebirge, extrem frosthart'
                },
                'Matucana oreodoxa & yanganucensis': {
                    'substrate': 'Mineralisch',
                    'temperature': '20-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Standard-Aussaat, relativ unkompliziert.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Regelmäßig',
                    'watering_winter': 'Fast trocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Peruanische Anden, schöne Blüten'
                },
                'Navajoa fickeisenii maja': {
                    'substrate': 'Mineralisch, sauer',
                    'temperature': '15-22°C',
                    'germination_time': 'Wochen-Monate',
                    'care_notes': 'Schwierig, Kältebehandlung empfohlen.',
                    'temperature_min': 15,
                    'temperature_max': 22,
                    'watering_summer': 'Sehr vorsichtig',
                    'watering_winter': 'Knochentrocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Rarität, oft gepfropft'
                },
                'Oreocereus Mischung': {
                    'substrate': 'Mineralisch',
                    'temperature': '20-25°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Lichtkeimer, nicht abdecken. Kühle Überwinterung fördert Blütenbildung.',
                    'temperature_min': 20,
                    'temperature_max': 25,
                    'watering_summer': 'Mäßig',
                    'watering_winter': 'Trocken und kühl',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Alte-Mann-der-Anden, wollige Behaarung'
                },
                'Ortegocactus macdougalii': {
                    'substrate': 'Rein mineralisch, kiesig, kalkhaltig',
                    'temperature': '20-25°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Hochlandart, keine große Hitze. Sehr fäulnisempfindlich.',
                    'temperature_min': 20,
                    'temperature_max': 25,
                    'watering_summer': 'Sehr sparsam',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Hell, keine pralle Sonne',
                    'special_care': 'Mexikanische Rarität, langsam wachsend'
                },
                'Pelecyphora aselliformis & pseudopectinata': {
                    'substrate': 'Rein mineralisch, kalkhaltig',
                    'temperature': '20-28°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Sehr fäulnisempfindlich, sparsam wässern.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Minimal',
                    'watering_winter': 'Knochentrocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Assel-Kaktus, winzige Warzen'
                },
                'Roseocactus kotschoubeyanus': {
                    'substrate': 'Rein mineralisch',
                    'temperature': '25°C',
                    'germination_time': '3-4 Wochen',
                    'care_notes': 'Langsam wachsend, tiefe Töpfe für Rübenwurzel.',
                    'temperature_min': 22,
                    'temperature_max': 28,
                    'watering_summer': 'Sehr sparsam',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Lebender Stein, flach wachsend'
                },
                'Sclerocactus Mischung': {
                    'substrate': 'Mineralisch, sauer',
                    'temperature': '15-22°C',
                    'germination_time': 'Wochen-Monate',
                    'care_notes': 'Schwierig, Kältebehandlung empfohlen.',
                    'temperature_min': 15,
                    'temperature_max': 22,
                    'watering_summer': 'Vorsichtig',
                    'watering_winter': 'Trocken und kalt',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'US-Hochgebirge, frosthart'
                },
                'Selenicereus Mischung': {
                    'substrate': 'Mineralisch mit organ. Anteil',
                    'temperature': '20-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Epiphytisch, benötigt etwas mehr Feuchtigkeit, aber keine Staunässe.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Regelmäßig feucht',
                    'watering_winter': 'Mäßig feucht',
                    'light_requirements': 'Hell bis halbschattig',
                    'special_care': 'Königin der Nacht, klettert/hängt'
                },
                'Stenocactus Mischung': {
                    'substrate': 'Mineralisch',
                    'temperature': '20-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Samen flach aussäen, helles, indirektes Licht.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Mäßig',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Viele schmale Rippen'
                },
                'Strombocactus disciformis & pulcherrimus': {
                    'substrate': 'Rein mineralisch, kalkhaltig',
                    'temperature': '20-28°C',
                    'germination_time': 'Wochen-Monate',
                    'care_notes': 'Staubfeine Samen, extrem langsam wachsend, nicht abdecken.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Minimal',
                    'watering_winter': 'Knochentrocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Mexikanische Rarität, oft gepfropft'
                },
                'Submatucana Mischung': {
                    'substrate': 'Mineralisch',
                    'temperature': '16-25°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Benötigen viel Licht, aber keine pralle Sonne.',
                    'temperature_min': 16,
                    'temperature_max': 25,
                    'watering_summer': 'Regelmäßig',
                    'watering_winter': 'Fast trocken',
                    'light_requirements': 'Hell, leicht schattiert',
                    'special_care': 'Peruanische Anden'
                },
                'Tephrocactus articulatus': {
                    'substrate': 'Rein mineralisch',
                    'temperature': '25-35°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Große Samen gut ins Substrat drücken. Benötigt hohe Keimtemperaturen.',
                    'temperature_min': 25,
                    'temperature_max': 35,
                    'watering_summer': 'Sparsam',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Volle Sonne',
                    'special_care': 'Papierdornen-Varianten, frosthart'
                },
                'Thelocactus Mischung': {
                    'substrate': 'Mineralisch',
                    'temperature': '20-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Relativ unkompliziert nach Standardmethode.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Mäßig',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Große bunte Blüten'
                },
                'Toumea-Pediocactus papyracantha': {
                    'substrate': 'Mineralisch, sauer',
                    'temperature': '15-22°C',
                    'germination_time': 'Wochen-Monate',
                    'care_notes': 'Schwierig, Kältebehandlung empfohlen.',
                    'temperature_min': 15,
                    'temperature_max': 22,
                    'watering_summer': 'Minimal',
                    'watering_winter': 'Knochentrocken',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'US-Rarität, Papier-Dornen'
                },
                'Turbinicarpus lophophorioides & Mischung': {
                    'substrate': 'Rein mineralisch, kalkhaltig (Gipszugabe)',
                    'temperature': '20-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Fäulnisempfindlich, sehr gute Drainage erforderlich.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Sehr sparsam',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Mexikanische Zwergkakteen'
                },
                'Uncarina grandidieri': {
                    'substrate': 'Mineralisch mit 30% organ. Anteil',
                    'temperature': '25-32°C',
                    'germination_time': '1-2 Wochen',
                    'care_notes': 'NICHT Kaktus! Sukkulente aus Madagaskar. Höhere Luftfeuchtigkeit, frostempfindlich.',
                    'temperature_min': 25,
                    'temperature_max': 32,
                    'watering_summer': 'Reichlich',
                    'watering_winter': 'Mäßig, warm halten',
                    'light_requirements': 'Hell bis vollsonnig',
                    'special_care': 'Pachypodium-Verwandter, Caudex-Pflanze'
                },
                'Utahia sileri': {
                    'substrate': 'Rein mineralisch, sauer, sehr durchlässig',
                    'temperature': '15-22°C',
                    'germination_time': '3-8 Wochen',
                    'care_notes': 'Hochlandart aus Utah/Arizona. Extrem fäulnisempfindlich, kühle Winter notwendig.',
                    'temperature_min': 15,
                    'temperature_max': 22,
                    'watering_summer': 'Minimal',
                    'watering_winter': 'Knochentrocken und kalt',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'US-Endemit, sehr selten'
                },
                'Weingartia riograndensis': {
                    'substrate': 'Mineralisch',
                    'temperature': '18-25°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Bolivianische Hochlandart, kühle Temperaturen bevorzugt, gute Belüftung wichtig.',
                    'temperature_min': 18,
                    'temperature_max': 25,
                    'watering_summer': 'Regelmäßig',
                    'watering_winter': 'Trocken und kühl',
                    'light_requirements': 'Vollsonne',
                    'special_care': 'Reichblühend, robust'
                },

                'Turbinicarpus schwarzii': {
                    'substrate': 'Rein mineralisch, kalkhaltig',
                    'temperature': '18-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Sehr seltene Art, extrem langsam wachsend. Fäulnisempfindlich.',
                    'temperature_min': 18,
                    'temperature_max': 28,
                    'watering_summer': 'Minimal, nur bei Schrumpfung',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Hell, leichte Schattierung im Sommer',
                    'special_care': 'Mexikanische Rarität, oft gepfropft für besseres Wachstum'
                },
                'Stenocactus zacatecasensis': {
                    'substrate': 'Mineralisch, kalkhaltig',
                    'temperature': '20-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Charakteristische gewellte Rippen. Relativ unkompliziert.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Mäßig, wenn Substrat trocken',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Hell bis vollsonnig',
                    'special_care': 'Schöne Blüten, zahlreiche schmale Rippen'
                },
                'Turbinicarpus subterraneus': {
                    'substrate': 'Rein mineralisch, sehr durchlässig',
                    'temperature': '18-25°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Wächst halb unterirdisch. Extrem fäulnisempfindlich.',
                    'temperature_min': 18,
                    'temperature_max': 25,
                    'watering_summer': 'Sehr sparsam',
                    'watering_winter': 'Knochentrocken',
                    'light_requirements': 'Hell, aber geschützt',
                    'special_care': 'Name bedeutet "unterirdisch" - zieht sich bei Trockenheit zurück'
                },
                'Echinofossulocactus coptonogonus': {
                    'substrate': 'Mineralisch, kalkhaltig',
                    'temperature': '20-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Synonym für Stenocactus coptonogonus. Viele schmale Rippen.',
                    'temperature_min': 20,
                    'temperature_max': 28,
                    'watering_summer': 'Mäßig',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Hell bis vollsonnig',
                    'special_care': 'Gewellte Rippen, violette Blüten mit dunklem Mittelstreifen'
                },
                'Turbinicarpus valdezianus x rubiflorus': {
                    'substrate': 'Rein mineralisch',
                    'temperature': '18-26°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Hybride mit interessanten Eigenschaften beider Elternteile.',
                    'temperature_min': 18,
                    'temperature_max': 26,
                    'watering_summer': 'Sparsam',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Kreuzung vereint weiße und rosa Blütenfarben'
                },
                'Turbinicarpus polaskii': {
                    'substrate': 'Rein mineralisch, Gipszugabe',
                    'temperature': '18-28°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Seltene Art aus Mexiko. Sehr langsam wachsend.',
                    'temperature_min': 18,
                    'temperature_max': 28,
                    'watering_summer': 'Minimal',
                    'watering_winter': 'Knochentrocken',
                    'light_requirements': 'Hell',
                    'special_care': 'Winzige Art, blüht rosa-weiß, Gipsböden in der Natur'
                },
                'Turbinicarpus panarottoi': {
                    'substrate': 'Rein mineralisch',
                    'temperature': '18-26°C',
                    'germination_time': '2-4 Wochen',
                    'care_notes': 'Extrem seltene Art. Sehr fäulnisempfindlich.',
                    'temperature_min': 18,
                    'temperature_max': 26,
                    'watering_summer': 'Minimal',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Hell, leicht schattiert',
                    'special_care': 'Eine der seltensten Turbinicarpus-Arten'
                },
                'Turbinicarpus alonsoi': {
                    'substrate': 'Rein mineralisch, kalkhaltig',
                    'temperature': '18-28°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Kleinbleibende Art mit dichter Bedornung.',
                    'temperature_min': 18,
                    'temperature_max': 28,
                    'watering_summer': 'Sparsam',
                    'watering_winter': 'Trocken',
                    'light_requirements': 'Hell bis vollsonnig',
                    'special_care': 'Rosa Blüten, kompakter Wuchs, robust'
                },
                'Ariocarpus trigonus': {
                    'substrate': 'Rein mineralisch, kalkhaltig, tiefe Töpfe',
                    'temperature': '20-30°C',
                    'germination_time': '1-4 Wochen',
                    'care_notes': 'Sehr langsam wachsend. Dreieckige Warzen. Tiefe Rübenwurzel.',
                    'temperature_min': 20,
                    'temperature_max': 30,
                    'watering_summer': 'Sehr sparsam, nur bei Schrumpfung',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Hell, leichte Schattierung',
                    'special_care': 'Gelbe Blüten, extrem langsam, oft gepfropft'
                },
                'Ariocarpus retusus': {
                    'substrate': 'Rein mineralisch, kalkhaltig',
                    'temperature': '20-30°C',
                    'germination_time': '1-3 Wochen',
                    'care_notes': 'Klassischer Ariocarpus, etwas schneller als andere Arten.',
                    'temperature_min': 20,
                    'temperature_max': 30,
                    'watering_summer': 'Sparsam, wenn geschrumpft',
                    'watering_winter': 'Absolut trocken',
                    'light_requirements': 'Hell, keine pralle Mittagssonne',
                    'special_care': 'Weiße oder rosa Blüten, Rübenwurzel, relativ robust'
                },
                'Ariocarpus fissuratus': {
                    'substrate': 'Rein mineralisch, sehr durchlässig',
                    'temperature': '20-30°C',
                    'germination_time': '1-4 Wochen',
                    'care_notes': 'Lebender Stein. Extrem langsam, sehr fäulnisempfindlich.',
                    'temperature_min': 20,
                    'temperature_max': 30,
                    'watering_summer': 'Minimal, nur bei starker Schrumpfung',
                    'watering_winter': 'Knochentrocken',
                    'light_requirements': 'Hell, leicht schattiert',
                    'special_care': 'Flacher Wuchs, rosa Blüten, Mimikry an Steine'
                }
            }
            
            # Arten in Datenbank speichern
            for name, data in all_species.items():
                species = Species(
                    name=name,
                    substrate=data['substrate'],
                    temperature=data['temperature'],
                    germination_time=data['germination_time'],
                    care_notes=data['care_notes'],
                    temperature_min=data['temperature_min'],
                    temperature_max=data['temperature_max'],
                    watering_summer=data.get('watering_summer', 'Mäßig'),
                    watering_winter=data.get('watering_winter', 'Trocken'),
                    light_requirements=data.get('light_requirements', 'Hell'),
                    special_care=data.get('special_care', ''),
                    user_created=False
                )
                db.session.add(species)
            
            db.session.commit()
            print(f"✅ {len(all_species)} Arten erfolgreich geladen!")

# ==================== APP STARTEN ====================

if __name__ == '__main__':
    # Backup-Ordner erstellen
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    # Static-Ordner erstellen
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Datenbank initialisieren
    init_db()
    
    # Server starten
    print("\n🌵 Kaktus-Center startet...")
    print(f"📍 Zugriff über: http://localhost:5000")
    print(f"📍 Oder im Netzwerk: http://[PI-IP]:5000\n")
    
    # Debug-Modus für Entwicklung, False für Produktion
    app.run(host='0.0.0.0', port=5000, debug=True)

# Erweiterte app.py - Fügen Sie diese neuen Routen zu Ihrer bestehenden app.py hinzu

# ==================== NEUE MODELLE ====================
# Fügen Sie diese zur bestehenden app.py nach den anderen Modellen hinzu:

class PlantAction(db.Model):
    """Pflegeaktionen für Pflanzen"""
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # water, fertilize, repot
    action_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    plant = db.relationship('Plant', backref='actions')

class CareChecklistItem(db.Model):
    """Individuelle Pflege-Checklisten"""
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.String(50))  # daily, weekly, monthly
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    plant = db.relationship('Plant', backref='checklist_items')

# ==================== NEUE API ENDPOINTS ====================
# Fügen Sie diese zu Ihrer app.py hinzu:

@app.route('/api/plants/<int:plant_id>/action', methods=['POST'])
def add_plant_action(plant_id):
    """Pflegeaktion hinzufügen (Gießen, Düngen, Umtopfen)"""
    plant = Plant.query.get_or_404(plant_id)
    data = request.json
    
    action_type = data.get('action_type')
    if action_type not in ['water', 'fertilize', 'repot']:
        return jsonify({'error': 'Ungültiger Aktionstyp'}), 400
    
    # Neue Aktion erstellen
    action = PlantAction(
        plant_id=plant_id,
        action_type=action_type,
        action_date=datetime.strptime(data.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
        notes=data.get('notes', '')
    )
    db.session.add(action)
    
    # Update last_watered/last_fertilized in Plant model
    if action_type == 'water':
        plant.last_watered = action.action_date
    elif action_type == 'fertilize':
        plant.last_fertilized = action.action_date
    
    # Automatisch Tagebucheintrag erstellen
    diary_entry = DiaryEntry(
        date=action.action_date,
        species_id=plant.species_id,
        note=f"{'💧 Gegossen' if action_type == 'water' else '🌿 Gedüngt' if action_type == 'fertilize' else '🪴 Umgetopft'}: {action.notes or 'Standard'}",
        entry_type=action_type
    )
    db.session.add(diary_entry)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'action_id': action.id,
        'message': f'Aktion {action_type} erfolgreich hinzugefügt'
    })

@app.route('/api/plants/<int:plant_id>/actions', methods=['GET'])
def get_plant_actions(plant_id):
    """Alle Aktionen einer Pflanze abrufen"""
    actions = PlantAction.query.filter_by(plant_id=plant_id).order_by(PlantAction.action_date.desc()).all()
    
    return jsonify([{
        'id': a.id,
        'type': a.action_type,
        'date': a.action_date.isoformat(),
        'notes': a.notes
    } for a in actions])

@app.route('/api/sowings/<int:sowing_id>/auto-transfer', methods=['POST'])
def auto_transfer_to_plants(sowing_id):
    """Automatischer Transfer von Keimung zu Pflanzenbestand"""
    sowing = Sowing.query.get_or_404(sowing_id)
    data = request.json
    
    # Keimung vermerken
    sowing.germinated = True
    sowing.germination_date = datetime.strptime(data['germination_date'], '%Y-%m-%d').date()
    sowing.germinated_count = int(data['germinated_count'])
    
    # Automatisch Pflanze erstellen
    plant = Plant(
        species_id=sowing.species_id,
        purchase_date=sowing.germination_date,  # Keimdatum als "Kaufdatum"
        location=f"Topf {sowing.pot_number}",
        substrate='Mineralisch (Aussaat)',
        notes=f"Automatisch aus Aussaat vom {sowing.sowing_date} übernommen. {sowing.germinated_count} Sämlinge.",
        from_sowing=True,
        sowing_id=sowing_id
    )
    db.session.add(plant)
    
    # Tagebucheintrag
    diary = DiaryEntry(
        date=sowing.germination_date,
        species_id=sowing.species_id,
        note=f"🌱 Keimung: {sowing.germinated_count} von {sowing.seed_count} Samen gekeimt. Automatisch zum Bestand hinzugefügt.",
        entry_type='germination'
    )
    db.session.add(diary)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'plant_id': plant.id,
        'message': f'{sowing.germinated_count} Sämlinge wurden zum Bestand hinzugefügt'
    })

@app.route('/api/plants/<int:plant_id>/checklist', methods=['GET', 'POST'])
def handle_plant_checklist(plant_id):
    """Individuelle Pflege-Checkliste verwalten"""
    plant = Plant.query.get_or_404(plant_id)
    
    if request.method == 'GET':
        # Checkliste abrufen
        items = CareChecklistItem.query.filter_by(plant_id=plant_id).all()
        
        # Wenn keine Items, Standard-Checkliste erstellen
        if not items:
            default_tasks = [
                ('Auf Schädlinge kontrollieren', 'daily'),
                ('Temperatur prüfen', 'daily'),
                ('Lichtverhältnisse optimal?', 'daily'),
                ('Substratfeuchtigkeit prüfen', 'weekly'),
                ('Auf neue Triebe/Knospen prüfen', 'weekly'),
                ('Platzbedarf prüfen', 'monthly')
            ]
            
            for task, freq in default_tasks:
                item = CareChecklistItem(
                    plant_id=plant_id,
                    task=task,
                    frequency=freq
                )
                db.session.add(item)
            db.session.commit()
            items = CareChecklistItem.query.filter_by(plant_id=plant_id).all()
        
        return jsonify([{
            'id': item.id,
            'task': item.task,
            'frequency': item.frequency,
            'completed': item.completed,
            'completed_date': item.completed_date.isoformat() if item.completed_date else None
        } for item in items])
    
    elif request.method == 'POST':
        # Checklist-Item abhaken
        data = request.json
        item_id = data.get('item_id')
        completed = data.get('completed', False)
        
        item = CareChecklistItem.query.get_or_404(item_id)
        item.completed = completed
        item.completed_date = datetime.now().date() if completed else None
        
        db.session.commit()
        return jsonify({'status': 'success'})

@app.route('/api/care-alerts')
def get_care_alerts():
    """Pflegewarnungen für alle Pflanzen"""
    alerts = []
    plants = Plant.query.all()
    today = datetime.now().date()
    
    for plant in plants:
        # Gießwarnung
        if plant.last_watered:
            days_since_water = (today - plant.last_watered).days
            if days_since_water > 14:  # Standard 2 Wochen
                alerts.append({
                    'type': 'water',
                    'priority': 'high' if days_since_water > 21 else 'medium',
                    'plant_id': plant.id,
                    'species': plant.species.name,
                    'message': f'{plant.species.name} seit {days_since_water} Tagen nicht gegossen!',
                    'location': plant.location
                })
        else:
            alerts.append({
                'type': 'water',
                'priority': 'high',
                'plant_id': plant.id,
                'species': plant.species.name,
                'message': f'{plant.species.name} wurde noch nie gegossen!',
                'location': plant.location
            })
        
        # Düngwarnung
        if plant.last_fertilized:
            days_since_fertilize = (today - plant.last_fertilized).days
            if days_since_fertilize > 30:  # Standard 1 Monat
                alerts.append({
                    'type': 'fertilize',
                    'priority': 'low',
                    'plant_id': plant.id,
                    'species': plant.species.name,
                    'message': f'{plant.species.name} könnte gedüngt werden (vor {days_since_fertilize} Tagen)',
                    'location': plant.location
                })
        
        # Sämlingswarnung
        if hasattr(plant, 'from_sowing') and plant.from_sowing:
            age_days = (today - plant.purchase_date).days
            if age_days == 14:
                alerts.append({
                    'type': 'seedling',
                    'priority': 'medium',
                    'plant_id': plant.id,
                    'species': plant.species.name,
                    'message': f'Sämlinge {plant.species.name} sind 2 Wochen alt - Abhärtung beginnen',
                    'location': plant.location
                })
            elif age_days == 60:
                alerts.append({
                    'type': 'seedling',
                    'priority': 'medium',
                    'plant_id': plant.id,
                    'species': plant.species.name,
                    'message': f'Sämlinge {plant.species.name} sind 2 Monate alt - Umtopfen prüfen',
                    'location': plant.location
                })
    
    # Nach Priorität sortieren
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    alerts.sort(key=lambda x: priority_order[x['priority']])
    
    return jsonify(alerts)

@app.route('/api/plant-care-stats/<int:plant_id>')
def get_plant_care_stats(plant_id):
    """Detaillierte Pflegestatistiken für eine Pflanze"""
    plant = Plant.query.get_or_404(plant_id)
    actions = PlantAction.query.filter_by(plant_id=plant_id).all()
    
    # Statistiken berechnen
    water_actions = [a for a in actions if a.action_type == 'water']
    fertilize_actions = [a for a in actions if a.action_type == 'fertilize']
    repot_actions = [a for a in actions if a.action_type == 'repot']
    
    today = datetime.now().date()
    
    stats = {
        'plant_id': plant_id,
        'species': plant.species.name,
        'age_days': (today - plant.purchase_date).days,
        'location': plant.location,
        'total_waterings': len(water_actions),
        'total_fertilizations': len(fertilize_actions),
        'total_repottings': len(repot_actions),
        'days_since_water': (today - plant.last_watered).days if plant.last_watered else None,
        'days_since_fertilize': (today - plant.last_fertilized).days if plant.last_fertilized else None,
        'from_sowing': hasattr(plant, 'from_sowing') and plant.from_sowing,
        'recommended_water_interval': plant.species.watering_summer if hasattr(plant.species, 'watering_summer') else '14 Tage',
        'recent_actions': [{
            'type': a.action_type,
            'date': a.action_date.isoformat(),
            'notes': a.notes
        } for a in sorted(actions, key=lambda x: x.action_date, reverse=True)[:5]]
    }
    
    return jsonify(stats)

# ==================== ERWEITERTE DASHBOARD STATS ====================
# Ersetzen Sie die bestehende dashboard-stats Route:

@app.route('/api/dashboard-stats')
def show_dashboard_stats():
    """Erweiterte Dashboard-Statistiken"""
    now = datetime.now()
    today = now.date()
    month_ago = now - timedelta(days=30)
    
    # Pflegeerinnerungen
    care_alerts = []
    
    # Prüfe alle Pflanzen auf Pflegebedarf
    plants = Plant.query.all()
    for plant in plants:
        if plant.last_watered:
            days_since = (today - plant.last_watered).days
            if days_since > 14:
                care_alerts.append({
                    'type': 'warning',
                    'message': f'⚠️ {plant.species.name} ({plant.location}) seit {days_since} Tagen nicht gegossen!'
                })
        else:
            care_alerts.append({
                'type': 'warning',
                'message': f'⚠️ {plant.species.name} ({plant.location}) wurde noch nie gegossen!'
            })
    
    # Keimungsüberwachung
    for sowing in Sowing.query.filter(Sowing.germinated == False).all():
        days = (today - sowing.sowing_date).days
        if days > 30:
            care_alerts.append({
                'type': 'info',
                'message': f'📍 {sowing.species.name} (Topf {sowing.pot_number}) seit {days} Tagen ohne Keimung'
            })
    
    stats = {
        'overview': {
            'total_species': Species.query.count(),
            'total_sowings': Sowing.query.count(),
            'active_sowings': Sowing.query.filter(Sowing.germinated == False).count(),
            'total_plants': Plant.query.count(),
            'plants_from_sowings': Plant.query.filter(Plant.from_sowing == True).count() if hasattr(Plant, 'from_sowing') else 0,
            'total_diary_entries': DiaryEntry.query.count(),
            'total_actions': PlantAction.query.count() if PlantAction else 0
        },
        'recent': {
            'sowings_this_month': Sowing.query.filter(Sowing.sowing_date >= month_ago.date()).count(),
            'germinations_this_month': Sowing.query.filter(
                Sowing.germination_date >= month_ago.date()
            ).count(),
            'plants_added_this_month': Plant.query.filter(Plant.purchase_date >= month_ago.date()).count(),
            'actions_this_week': PlantAction.query.filter(
                PlantAction.action_date >= (today - timedelta(days=7))
            ).count() if PlantAction else 0
        },
        'care_alerts': care_alerts[:10]  # Maximal 10 Warnungen
    }
    
    return jsonify(stats)

# ==================== MIGRATION ====================
# Fügen Sie diese Funktion zur init_db() hinzu:

def upgrade_database():
    """Erweitert die bestehende Datenbank um neue Felder"""
    with app.app_context():
        # Prüfen ob die neuen Tabellen existieren
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'plant_action' not in existing_tables:
            db.create_all()
            print("✅ Neue Tabellen erstellt: PlantAction, CareChecklistItem")
        
        # Füge neue Spalte zu Plant hinzu falls nicht vorhanden
        if 'plant' in existing_tables:
            columns = [col['name'] for col in inspector.get_columns('plant')]
            if 'from_sowing' not in columns:
                with db.engine.connect() as conn:
                    conn.execute('ALTER TABLE plant ADD COLUMN from_sowing BOOLEAN DEFAULT FALSE')
                    conn.execute('ALTER TABLE plant ADD COLUMN sowing_id INTEGER')
                    conn.commit()
                print("✅ Plant-Tabelle erweitert")
