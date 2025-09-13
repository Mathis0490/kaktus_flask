#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script zum sicheren Hinzufügen neuer Kakteen-Arten zur bestehenden Datenbank
OHNE Verlust der vorhandenen Daten (Gießeinträge, Pflanzen, etc.)
"""

from app import app, db, Species
from datetime import datetime

def add_missing_species():
    """Fügt nur die neuen Arten hinzu, die noch nicht in der Datenbank sind"""

    # NUR die Arten, die Sie spezifisch benötigen
    new_species = {
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

    with app.app_context():
        print("\n" + "="*60)
        print("🌵 KAKTEEN-ARTEN HINZUFÜGEN")
        print("="*60)

        # Zuerst alle vorhandenen Arten anzeigen
        existing_species = Species.query.all()
        print(f"\n📊 Aktuell in der Datenbank: {len(existing_species)} Arten")

        added_count = 0
        skipped_count = 0

        print("\n🔍 Prüfe neue Arten...\n")

        for name, data in new_species.items():
            # Prüfen ob Art schon existiert
            existing = Species.query.filter_by(name=name).first()

            if not existing:
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
                added_count += 1
                print(f"✅ HINZUGEFÜGT: {name}")
            else:
                skipped_count += 1
                print(f"⏭️  Bereits vorhanden: {name}")

        # Änderungen speichern
        db.session.commit()

        # Zusammenfassung
        print("\n" + "="*60)
        print("📊 ZUSAMMENFASSUNG:")
        print(f"   ✅ Neu hinzugefügt: {added_count} Arten")
        print(f"   ⏭️  Übersprungen (bereits vorhanden): {skipped_count} Arten")
        print(f"   📚 Gesamt in Datenbank: {Species.query.count()} Arten")
        print("="*60)

        if added_count > 0:
            print("\n🎉 Neue Arten wurden erfolgreich zur Datenbank hinzugefügt!")
            print("   Ihre bestehenden Daten (Gießeinträge, Pflanzen, etc.) sind erhalten geblieben.")
        else:
            print("\n✨ Alle gewünschten Arten sind bereits in der Datenbank vorhanden.")

if __name__ == "__main__":
    # Sicherheitsabfrage
    print("\n" + "🔒 "*20)
    print("SICHERHEITSHINWEIS:")
    print("Dieses Script fügt NUR neue Arten hinzu.")
    print("Ihre bestehenden Daten bleiben ERHALTEN!")
    print("🔒 "*20)

    confirm = input("\nMöchten Sie fortfahren? (ja/nein): ").lower().strip()

    if confirm in ['ja', 'j', 'yes', 'y']:
        add_missing_species()
        print("\n✅ Script erfolgreich ausgeführt!")
    else:
        print("\n❌ Abgebrochen. Keine Änderungen vorgenommen.")
