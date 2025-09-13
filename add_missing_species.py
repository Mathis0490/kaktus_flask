#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script zum Hinzufügen spezialisierter und seltener Kakteen-Arten
Erweiterte Sammlung für Kakteen-Spezialisten
"""

from app import app, db, Species
from datetime import datetime

def add_specialized_species():
    """Fügt spezialisierte und seltene Kakteen-Arten hinzu"""

    # Spezialisierte Arten mit korrekten botanischen Namen
    specialized_species = {
        # ==================== ECHINOCEREUS ====================
        'Echinocereus pulcherrimus venustus': {
            'substrate': 'Mineralisch, sehr durchlässig',
            'temperature': '15-25°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Hochgebirgsart aus Mexiko. Benötigt kühle Winterruhe für Blütenbildung.',
            'temperature_min': 5,
            'temperature_max': 30,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken und kühl',
            'light_requirements': 'Vollsonne',
            'special_care': 'Prächtige rosa Blüten, Winterkälte bis -10°C'
        },
        'Echinocereus sp. krügeri': {
            'substrate': 'Mineralisch, kalkhaltig',
            'temperature': '18-28°C',
            'germination_time': '2-3 Wochen',
            'care_notes': 'Seltene Krüger-Form. Oft in Privatsammlungen.',
            'temperature_min': 5,
            'temperature_max': 32,
            'watering_summer': 'Regelmäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Sammler-Rarität, spezielle Herkunft'
        },
        'Echinocereus pulchellus tolantonso': {
            'substrate': 'Mineralisch',
            'temperature': '18-28°C',
            'germination_time': '1-3 Wochen',
            'care_notes': 'Kleinbleibende Art mit großen Blüten.',
            'temperature_min': 5,
            'temperature_max': 32,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Magenta-rosa Blüten, sehr dekorativ'
        },
        'Echinocereus ctenoides': {
            'substrate': 'Mineralisch, sandig',
            'temperature': '20-30°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Mexikanische Art mit charakteristischen Dornen.',
            'temperature_min': 10,
            'temperature_max': 35,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Gelbe bis rote Blüten'
        },
        'Echinocereus canus': {
            'substrate': 'Mineralisch, sehr durchlässig',
            'temperature': '15-28°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Texas/Mexiko. Graue Bedornung.',
            'temperature_min': 0,
            'temperature_max': 35,
            'watering_summer': 'Sparsam',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Extrem frosthart, magenta Blüten'
        },
        'Echinocereus triglochidiatus otero': {
            'substrate': 'Mineralisch',
            'temperature': '15-28°C',
            'germination_time': '2-3 Wochen',
            'care_notes': 'Otero County Form. Gruppenbildend.',
            'temperature_min': -15,
            'temperature_max': 35,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Extrem frosthart, rote Blüten'
        },
        'Echinocereus triglochidiatus ssp. mojave': {
            'substrate': 'Mineralisch, sandig',
            'temperature': '18-30°C',
            'germination_time': '2-3 Wochen',
            'care_notes': 'Mojave-Wüsten Form. Sehr hitzeresistent.',
            'temperature_min': -5,
            'temperature_max': 40,
            'watering_summer': 'Sparsam',
            'watering_winter': 'Trocken',
            'light_requirements': 'Volle Wüstensonne',
            'special_care': 'Extreme Hitze- und Kältetoleranz'
        },
        'Echinocereus relictus': {
            'substrate': 'Mineralisch, sehr durchlässig',
            'temperature': '15-25°C',
            'germination_time': '3-6 Wochen',
            'care_notes': 'Sehr seltene Art. Nur wenige Standorte bekannt.',
            'temperature_min': -5,
            'temperature_max': 30,
            'watering_summer': 'Sehr sparsam',
            'watering_winter': 'Absolut trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Extrem seltene Relikt-Art'
        },
        'Echinocereus triglochidiatus manzano': {
            'substrate': 'Mineralisch',
            'temperature': '15-26°C',
            'germination_time': '2-3 Wochen',
            'care_notes': 'Manzano Mountains Form. Hochgebirgsart.',
            'temperature_min': -20,
            'temperature_max': 30,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Extrem frosthart bis -20°C'
        },

        # ==================== TURBINICARPUS ====================
        'Turbinicarpus schmiedeckianus': {
            'substrate': 'Rein mineralisch, kalkhaltig',
            'temperature': '18-26°C',
            'germination_time': '1-3 Wochen',
            'care_notes': 'Klassische Turbinicarpus-Art. Kleine weiße Blüten.',
            'temperature_min': 5,
            'temperature_max': 30,
            'watering_summer': 'Sehr sparsam',
            'watering_winter': 'Absolut trocken',
            'light_requirements': 'Hell',
            'special_care': 'Zwergkaktus, oft nur 2-3cm groß'
        },
        'Turbinicarpus bonatzii': {
            'substrate': 'Rein mineralisch, Gips',
            'temperature': '18-26°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Sehr seltene Art. Gipsböden in der Natur.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Minimal',
            'watering_winter': 'Knochentrocken',
            'light_requirements': 'Hell',
            'special_care': 'Mexikanische Rarität'
        },
        'Turbinicarpus booleanus': {
            'substrate': 'Rein mineralisch',
            'temperature': '18-26°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Seltene Art mit charakteristischen Dornen.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Minimal',
            'watering_winter': 'Absolut trocken',
            'light_requirements': 'Hell',
            'special_care': 'Kleine rosa-weiße Blüten'
        },
        'Turbinicarpus dickisoniae Aramberri': {
            'substrate': 'Rein mineralisch, kalkhaltig',
            'temperature': '18-26°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Aramberri-Form. Sehr seltene Lokalform.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Minimal',
            'watering_winter': 'Knochentrocken',
            'light_requirements': 'Hell',
            'special_care': 'Spezifische Herkunft Aramberri'
        },
        'Turbinicarpus ellisae': {
            'substrate': 'Rein mineralisch',
            'temperature': '18-26°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Winzige Art, oft nur 1-2cm Durchmesser.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Extrem sparsam',
            'watering_winter': 'Absolut trocken',
            'light_requirements': 'Hell',
            'special_care': 'Einer der kleinsten Kakteen'
        },
        'Turbinicarpus roseiflorus': {
            'substrate': 'Rein mineralisch',
            'temperature': '18-26°C',
            'germination_time': '1-3 Wochen',
            'care_notes': 'Rosa Blüten, relativ robuste Art.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Sparsam',
            'watering_winter': 'Trocken',
            'light_requirements': 'Hell',
            'special_care': 'Schöne rosa Blütenfarbe'
        },
        'Turbinicarpus schmiedickeanus La Perdida': {
            'substrate': 'Rein mineralisch, kalkhaltig',
            'temperature': '18-26°C',
            'germination_time': '1-3 Wochen',
            'care_notes': 'La Perdida Lokalform. Spezielle Herkunft.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Sehr sparsam',
            'watering_winter': 'Absolut trocken',
            'light_requirements': 'Hell',
            'special_care': 'Lokale Variante aus La Perdida'
        },
        'Turbinicarpus ysabelae': {
            'substrate': 'Rein mineralisch',
            'temperature': '18-26°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Sehr seltene Art aus Nuevo León.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Minimal',
            'watering_winter': 'Knochentrocken',
            'light_requirements': 'Hell',
            'special_care': 'Extrem seltene mexikanische Art'
        },
        'Turbinicarpus klinkerianus Huizache': {
            'substrate': 'Rein mineralisch',
            'temperature': '18-26°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Huizache-Form. Spezifische Lokalvarietät.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Sparsam',
            'watering_winter': 'Trocken',
            'light_requirements': 'Hell',
            'special_care': 'Lokale Huizache-Variante'
        },
        'Turbinicarpus schwarzii var. guadalcasar': {
            'substrate': 'Rein mineralisch, kalkhaltig',
            'temperature': '18-26°C',
            'germination_time': '1-3 Wochen',
            'care_notes': 'Guadalcasar-Variante der schwarzii.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Minimal',
            'watering_winter': 'Absolut trocken',
            'light_requirements': 'Hell',
            'special_care': 'Lokale Guadalcasar-Form'
        },
        'Turbinicarpus schwarzii var. rubriflorus': {
            'substrate': 'Rein mineralisch, kalkhaltig',
            'temperature': '18-26°C',
            'germination_time': '1-3 Wochen',
            'care_notes': 'Rotblühende Form der schwarzii.',
            'temperature_min': 5,
            'temperature_max': 28,
            'watering_summer': 'Minimal',
            'watering_winter': 'Absolut trocken',
            'light_requirements': 'Hell',
            'special_care': 'Seltene rotblühende Variante'
        },

        # ==================== ASTROPHYTUM ====================
        'Astrophytum crassispinoides': {
            'substrate': 'Mineralisch, kalkhaltig',
            'temperature': '20-28°C',
            'germination_time': '5-14 Tage',
            'care_notes': 'Dicke Dornen, zwischen ornatum und capricorne stehend.',
            'temperature_min': 10,
            'temperature_max': 35,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Hybride Eigenschaften, kräftige Bedornung'
        },
        'Astrophytum ornatum': {
            'substrate': 'Mineralisch, kalkhaltig',
            'temperature': '20-30°C',
            'germination_time': '5-14 Tage',
            'care_notes': 'Säulenförmig wachsend, gelbe Dornen.',
            'temperature_min': 10,
            'temperature_max': 35,
            'watering_summer': 'Regelmäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Wird säulenförmig, gelbe Blüten'
        },
        'Astrophytum senile red flower': {
            'substrate': 'Mineralisch, kalkhaltig',
            'temperature': '20-28°C',
            'germination_time': '5-14 Tage',
            'care_notes': 'Seltene rotblühende Form des senile.',
            'temperature_min': 10,
            'temperature_max': 32,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Extrem seltene rote Blütenfarbe'
        },
        'Astrophytum asterias var. nudum': {
            'substrate': 'Rein mineralisch',
            'temperature': '20-28°C',
            'germination_time': '3-10 Tage',
            'care_notes': 'Kulturform ohne weiße Punkte.',
            'temperature_min': 10,
            'temperature_max': 32,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Fast trocken',
            'light_requirements': 'Hell, keine pralle Sonne',
            'special_care': 'Glatte Form ohne Flecken'
        },
        'Astrophytum asterias superkabuto x capricorne': {
            'substrate': 'Mineralisch, kalkhaltig',
            'temperature': '20-28°C',
            'germination_time': '5-14 Tage',
            'care_notes': 'Hybride zwischen superkabuto und capricorne.',
            'temperature_min': 10,
            'temperature_max': 32,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Hell bis vollsonnig',
            'special_care': 'Interessante Hybrid-Eigenschaften'
        },

        # ==================== LOPHOPHORA ====================
        'Lophophora koehresii': {
            'substrate': 'Mineralisch mit <30% organisch',
            'temperature': '20-25°C',
            'germination_time': '7-21 Tage',
            'care_notes': 'Seltene Lophophora-Art. Kleine gelbe Blüten.',
            'temperature_min': 10,
            'temperature_max': 30,
            'watering_summer': 'Sparsam, von unten',
            'watering_winter': 'Trocken',
            'light_requirements': 'Hell, keine pralle Sonne',
            'special_care': 'Gelbe statt rosa Blüten'
        },
        'Lophophora williamsii': {
            'substrate': 'Mineralisch mit <30% organisch',
            'temperature': '20-25°C',
            'germination_time': '7-21 Tage',
            'care_notes': 'Klassischer Peyote. Dornenlos, Rübenwurzel.',
            'temperature_min': 10,
            'temperature_max': 30,
            'watering_summer': 'Sparsam, von unten',
            'watering_winter': 'Trocken',
            'light_requirements': 'Hell, keine pralle Sonne',
            'special_care': 'Kulturreligiöse Bedeutung, sehr langsam'
        },
        'Lophophora williamsii capitosa': {
            'substrate': 'Mineralisch mit <30% organisch',
            'temperature': '20-25°C',
            'germination_time': '7-21 Tage',
            'care_notes': 'Capitosa-Form mit mehreren Köpfen.',
            'temperature_min': 10,
            'temperature_max': 30,
            'watering_summer': 'Sparsam, von unten',
            'watering_winter': 'Trocken',
            'light_requirements': 'Hell, keine pralle Sonne',
            'special_care': 'Mehrköpfige Wuchsform'
        },

        # ==================== MAMMILLARIA ====================
        'Mammillaria pseudoerbella': {
            'substrate': 'Mineralisch',
            'temperature': '18-26°C',
            'germination_time': '1-2 Wochen',
            'care_notes': 'Kleine Art mit weißen Dornen.',
            'temperature_min': 5,
            'temperature_max': 30,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Hell',
            'special_care': 'Weiße Bedornung, gruppenbildend'
        },
        'Mammillaria bombycina': {
            'substrate': 'Mineralisch',
            'temperature': '18-26°C',
            'germination_time': '1-2 Wochen',
            'care_notes': 'Seidig-weiße Bedornung, sehr dekorativ.',
            'temperature_min': 5,
            'temperature_max': 30,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Hell bis vollsonnig',
            'special_care': 'Seidig-weiße Wolle und Dornen'
        },

        # ==================== WEITERE SELTENE ARTEN ====================
        'Hylocereus sp.': {
            'substrate': 'Humusreich, durchlässig',
            'temperature': '20-30°C',
            'germination_time': '1-3 Wochen',
            'care_notes': 'Epiphytischer Kletternkaktus. Drachenfrucht.',
            'temperature_min': 15,
            'temperature_max': 35,
            'watering_summer': 'Reichlich feucht',
            'watering_winter': 'Mäßig feucht',
            'light_requirements': 'Hell, keine direkte Sonne',
            'special_care': 'Kletterhilfe nötig, essbare Früchte'
        },
        'Thelocactus hexagonus': {
            'substrate': 'Mineralisch',
            'temperature': '20-28°C',
            'germination_time': '1-3 Wochen',
            'care_notes': 'Sechseckige Warzen, große gelbe Blüten.',
            'temperature_min': 5,
            'temperature_max': 32,
            'watering_summer': 'Mäßig',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Charakteristische sechseckige Struktur'
        },
        'Echinocactus horizonthalonius visubikii': {
            'substrate': 'Mineralisch, sehr durchlässig',
            'temperature': '20-30°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Subspecies mit spezieller Bedornung.',
            'temperature_min': 5,
            'temperature_max': 35,
            'watering_summer': 'Sparsam',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Lokale Subspecies-Variante'
        },
        'Echinocactus horizonthalonius coapas': {
            'substrate': 'Mineralisch, kalkhaltig',
            'temperature': '20-30°C',
            'germination_time': '2-4 Wochen',
            'care_notes': 'Coapas-Form mit charakteristischen Merkmalen.',
            'temperature_min': 5,
            'temperature_max': 35,
            'watering_summer': 'Sparsam',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Spezifische Coapas-Lokalform'
        },
        'Pseudolithos cubiformis': {
            'substrate': 'Rein mineralisch, extrem durchlässig',
            'temperature': '25-40°C',
            'germination_time': '4-8 Wochen',
            'care_notes': 'Würfelförmiger lebender Stein. Extrem schwierig!',
            'temperature_min': 20,
            'temperature_max': 45,
            'watering_summer': 'Nur nebeln',
            'watering_winter': 'Absolut trocken',
            'light_requirements': 'Sehr hell',
            'special_care': 'Einer der schwierigsten Sukkulenten'
        },
        'Pseudolithos migiurtinus': {
            'substrate': 'Rein mineralisch, extrem durchlässig',
            'temperature': '25-40°C',
            'germination_time': '4-8 Wochen',
            'care_notes': 'Somalischer lebender Stein. Sehr schwierig!',
            'temperature_min': 20,
            'temperature_max': 45,
            'watering_summer': 'Nur nebeln',
            'watering_winter': 'Knochentrocken',
            'light_requirements': 'Sehr hell',
            'special_care': 'Extreme Wärme und Trockenheit nötig'
        },
        'Uncarina stellulifera': {
            'substrate': 'Mineralisch mit organischem Anteil',
            'temperature': '22-32°C',
            'germination_time': '1-3 Wochen',
            'care_notes': 'Madagassische Caudex-Pflanze mit sternförmigen Haaren.',
            'temperature_min': 15,
            'temperature_max': 38,
            'watering_summer': 'Reichlich',
            'watering_winter': 'Trocken',
            'light_requirements': 'Vollsonne',
            'special_care': 'Charakteristische sternförmige Behaarung'
        }
    }

    with app.app_context():
        print("\n" + "="*60)
        print("🌵 SPEZIALISIERTE KAKTEEN-ARTEN HINZUFÜGEN")
        print("="*60)
        print("🔬 Seltene Arten für Kakteen-Spezialisten")

        # Zuerst alle vorhandenen Arten anzeigen
        existing_species = Species.query.all()
        existing_names = {s.name for s in existing_species}
        print(f"\n📊 Aktuell in der Datenbank: {len(existing_species)} Arten")

        added_count = 0
        skipped_count = 0

        print("\n🔍 Prüfe spezialisierte Arten...\n")

        for name, data in specialized_species.items():
            # Prüfen ob Art schon existiert
            if name not in existing_names:
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

                # Spezielle Markierungen für seltene Arten
                if 'seltene' in data['care_notes'].lower() or 'rarität' in data['special_care'].lower():
                    print(f"🏆 RARITÄT HINZUGEFÜGT: {name}")
                elif 'schwierig' in data['care_notes'].lower():
                    print(f"⚠️  SCHWIERIG HINZUGEFÜGT: {name}")
                elif 'giftig' in data['care_notes'].lower():
                    print(f"☠️  GIFTIG HINZUGEFÜGT: {name}")
                else:
                    print(f"✅ HINZUGEFÜGT: {name}")
            else:
                skipped_count += 1
                print(f"⭐ Bereits vorhanden: {name}")

        # Änderungen speichern
        if added_count > 0:
            db.session.commit()

        # Zusammenfassung mit Kategorien
        print("\n" + "="*60)
        print("📊 SPEZIALIST-SAMMLUNG ZUSAMMENFASSUNG:")
        print(f"   ✅ Neu hinzugefügt: {added_count} Arten")
        print(f"   ⭐ Bereits vorhanden: {skipped_count} Arten")
        print(f"   📚 Gesamt in Datenbank: {Species.query.count()} Arten")

        # Kategorien-Übersicht
        print("\n🏷️  KATEGORIEN DER NEUEN ARTEN:")
        echinocereus_count = len([name for name in specialized_species.keys() if 'Echinocereus' in name])
        turbinicarpus_count = len([name for name in specialized_species.keys() if 'Turbinicarpus' in name])
        astrophytum_count = len([name for name in specialized_species.keys() if 'Astrophytum' in name])
        lophophora_count = len([name for name in specialized_species.keys() if 'Lophophora' in name])

        print(f"   🌸 Echinocereus-Arten: {echinocereus_count}")
        print(f"   💎 Turbinicarpus-Arten: {turbinicarpus_count}")
        print(f"   ⭐ Astrophytum-Arten: {astrophytum_count}")
        print(f"   🏜️  Lophophora-Arten: {lophophora_count}")
        print(f"   🔬 Sonstige Raritäten: {added_count - echinocereus_count - turbinicarpus_count - astrophytum_count - lophophora_count}")

        print("="*60)

        if added_count > 0:
            print("\n🎉 Spezialisierte Arten wurden erfolgreich hinzugefügt!")
            print("   Ihre Sammlung ist jetzt noch umfangreicher!")
            print("\n💡 Starten Sie jetzt die App neu:")
            print("   python app.py")
            print("\n🔬 ACHTUNG: Viele dieser Arten sind:")
            print("   • Extrem selten und schwer zu bekommen")
            print("   • Sehr anspruchsvoll in der Pflege")
            print("   • Benötigen spezielle Bedingungen")
            print("   • Teilweise giftig (Euphorbien)")
        else:
            print("\n✨ Alle spezialisierten Arten sind bereits vorhanden!")

if __name__ == "__main__":
    # Sicherheitsabfrage
    print("\n" + "🔬"*20)
    print("SPEZIALIST-SAMMLUNG:")
    print("Dieses Script fügt seltene und anspruchsvolle Arten hinzu.")
    print("Viele davon sind extrem schwierig zu kultivieren!")
    print("🔬"*20)

    confirm = input("\nMöchten Sie diese Spezialisten-Arten hinzufügen? (ja/nein): ").lower().strip()

    if confirm in ['ja', 'j', 'yes', 'y']:
        add_specialized_species()
        print("\n✅ Spezialist-Script erfolgreich ausgeführt!")
        print("\n🚀 Starten Sie die App: python app.py")
    else:
        print("\n❌ Abgebrochen. Keine Änderungen vorgenommen.")
