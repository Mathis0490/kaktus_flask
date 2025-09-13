#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def generate_batch_ids():
    conn = sqlite3.connect('kaktus.db')
    cursor = conn.cursor()
    
    print("🔄 Generiere Batch-IDs für bestehende Pflanzen...")
    
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
    
    year_month = datetime.now().strftime('%y%m')
    
    for plant_id, species_id, species_name, pot_number in plants:
        # Generiere Batch-ID
        if species_name:
            species_code = ''.join(species_name.split()[:2])[:3].upper()
        else:
            species_code = 'UNK'
        
        pot_code = pot_number if pot_number else f"M{plant_id}"
        batch_id = f"{year_month}-{species_code}-{pot_code}-{str(plant_id).zfill(3)}"
        
        # Update mit allen neuen Feldern
        cursor.execute("""
            UPDATE plant 
            SET batch_id = ?,
                origin_date = COALESCE(origin_date, purchase_date)
            WHERE id = ?
        """, (batch_id, plant_id))
        
        print(f"  ✓ Plant ID {plant_id}: {batch_id}")
    
    conn.commit()
    print(f"\n✅ {len(plants)} Batch-IDs generiert!")
    
    # Zeige Statistik
    cursor.execute("SELECT COUNT(*) FROM plant WHERE batch_id IS NOT NULL")
    total_with_batch = cursor.fetchone()[0]
    print(f"📊 Gesamt mit Batch-ID: {total_with_batch}")
    
    conn.close()

if __name__ == "__main__":
    generate_batch_ids()
    print("\n🚀 Fertig! Du kannst jetzt 'python app.py' starten")
