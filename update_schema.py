#!/usr/bin/env python3
# update_schema.py - Fügt neue Spalten zur bestehenden Datenbank hinzu

import sqlite3
from datetime import datetime
import shutil
import os

def update_database_schema():
    """Fügt die neuen Spalten zur bestehenden Datenbank hinzu"""
    
    print("🔄 Starte Datenbank-Schema Update...")
    
    # Backup erstellen
    if os.path.exists('kaktus.db'):
        backup_name = f"kaktus_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy('kaktus.db', backup_name)
        print(f"💾 Backup erstellt: {backup_name}")
    
    # Verbindung zur Datenbank
    conn = sqlite3.connect('kaktus.db')
    cursor = conn.cursor()
    
    try:
        # Prüfe welche Spalten bereits existieren
        cursor.execute("PRAGMA table_info(plant)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Existierende Spalten in 'plant': {existing_columns}")
        
        # Neue Spalten hinzufügen (nur wenn sie noch nicht existieren)
        new_columns = [
            ("batch_id", "VARCHAR(50)", "NULL"),
            ("parent_batch_id", "VARCHAR(50)", "NULL"),
            ("status", "VARCHAR(50)", "'active'"),
            ("stage", "VARCHAR(50)", "'adult'"),
            ("origin_type", "VARCHAR(50)", "'unknown'"),
            ("origin_date", "DATE", "NULL"),
            ("sowing_id", "INTEGER", "NULL"),
            ("pot_size", "VARCHAR(20)", "'10cm'"),
            ("pot_number", "VARCHAR(20)", "NULL"),
            ("health_status", "VARCHAR(50)", "'healthy'"),
            ("special_marks", "TEXT", "NULL"),
            ("last_repotted", "DATE", "NULL"),
            ("updated_at", "DATETIME", "NULL")
        ]
        
        added = 0
        for col_name, col_type, default_val in new_columns:
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE plant ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"
                    cursor.execute(sql)
                    print(f"  ✅ Spalte '{col_name}' hinzugefügt")
                    added += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"  ⏭️  Spalte '{col_name}' existiert bereits")
                    else:
                        print(f"  ❌ Fehler bei '{col_name}': {e}")
        
        # Neue Tabellen erstellen (falls nicht vorhanden)
        
        # PlantHistory Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plant_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL,
                batch_id VARCHAR(50) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                event_date DATE NOT NULL,
                old_value VARCHAR(200),
                new_value VARCHAR(200),
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plant_id) REFERENCES plant(id)
            )
        """)
        print("  ✅ Tabelle 'plant_history' erstellt/geprüft")
        
        # PlantMeasurement Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plant_measurement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL,
                batch_id VARCHAR(50) NOT NULL,
                measurement_date DATE NOT NULL,
                height_cm REAL,
                diameter_cm REAL,
                arm_count INTEGER,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plant_id) REFERENCES plant(id)
            )
        """)
        print("  ✅ Tabelle 'plant_measurement' erstellt/geprüft")
        
        # PlantAction Tabelle (falls nicht vorhanden)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plant_action (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                action_date DATE NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plant_id) REFERENCES plant(id)
            )
        """)
        print("  ✅ Tabelle 'plant_action' erstellt/geprüft")
        
        # CareChecklistItem Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS care_checklist_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL,
                task VARCHAR(200) NOT NULL,
                frequency VARCHAR(50),
                completed BOOLEAN DEFAULT 0,
                completed_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plant_id) REFERENCES plant(id)
            )
        """)
        print("  ✅ Tabelle 'care_checklist_item' erstellt/geprüft")
        
        # Änderungen speichern
        conn.commit()
        print(f"\n✅ Schema-Update abgeschlossen! {added} neue Spalten hinzugefügt.")
        
        # Jetzt die origin_date mit purchase_date füllen (für bestehende Einträge)
        cursor.execute("""
            UPDATE plant 
            SET origin_date = purchase_date 
            WHERE origin_date IS NULL AND purchase_date IS NOT NULL
        """)
        conn.commit()
        print("  ✅ origin_date mit purchase_date befüllt")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
    finally:
        conn.close()

def generate_batch_ids():
    """Generiert Batch-IDs für existierende Pflanzen"""
    
    print("\n🔄 Generiere Batch-IDs...")
    
    conn = sqlite3.connect('kaktus.db')
    cursor = conn.cursor()
    
    try:
        # Hole alle Pflanzen ohne batch_id
        cursor.execute("""
            SELECT p.id, p.species_id, s.name, p.pot_number
            FROM plant p
            LEFT JOIN species s ON p.species_id = s.id
            WHERE p.batch_id IS NULL OR p.batch_id = ''
        """)
        
        plants = cursor.fetchall()
        
        if not plants:
            print("✅ Alle Pflanzen haben bereits Batch-IDs")
            return
        
        print(f"📦 Gefunden: {len(plants)} Pflanzen ohne Batch-ID")
        
        from datetime import datetime
        now = datetime.now()
        year_month = now.strftime('%y%m')
        
        for plant_id, species_id, species_name, pot_number in plants:
            # Generiere Batch-ID
            if species_name:
                species_code = ''.join(species_name.split()[:2])[:3].upper()
            else:
                species_code = 'UNK'
            
            pot_code = pot_number if pot_number else f"M{plant_id}"
            
            # Eindeutige Nummer
            batch_id = f"{year_month}-{species_code}-{pot_code}-{str(plant_id).zfill(3)}"
            
            # Update
            cursor.execute("""
                UPDATE plant 
                SET batch_id = ? 
                WHERE id = ?
            """, (batch_id, plant_id))
            
            print(f"  ✓ Plant ID {plant_id} ({species_name}): {batch_id}")
        
        conn.commit()
        print(f"\n✅ {len(plants)} Batch-IDs generiert!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Schritt 1: Schema updaten
    update_database_schema()
    
    # Schritt 2: Batch-IDs generieren
    generate_batch_ids()
    
    print("\n🎉 Migration komplett abgeschlossen!")
    print("🚀 Du kannst jetzt die App mit 'python app.py' starten")
