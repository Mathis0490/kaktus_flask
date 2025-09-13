# 🌵 Kaktus Anzucht System Pro

Ein professionelles Tracking-System für Kakteen-Liebhaber zur Verwaltung von Aussaaten, Pflanzenbestand und Pflegeprotokollen.

## 📋 Features

- **Aussaat-Tracking**: Verfolge Aussaaten vom Samen bis zur Keimung
- **Bestandsverwaltung**: Katalogisiere deine Kakteen-Sammlung mit Standort und Pflegestatus
- **Tagebuch**: Dokumentiere alle Pflegeaktivitäten
- **Dashboard**: Übersicht über alle wichtigen Statistiken
- **Lot-System**: Eindeutige Identifikation von Aussaaten und deren Nachkommen
- **Automatische Übernahme**: Gekeimte Sämlinge werden automatisch in den Bestand übernommen

## 🔧 Voraussetzungen

- Raspberry Pi (beliebiges Modell, empfohlen: Pi 3 oder neuer)
- Raspberry Pi OS (Lite oder Desktop)
- Python 3.7 oder höher
- Mindestens 1GB freier Speicherplatz
- Netzwerkzugriff (für Installation und Zugriff)

## 📦 Installation

### 1. System vorbereiten

```bash
# System aktualisieren
sudo apt update
sudo apt upgrade -y

# Python und pip installieren (falls nicht vorhanden)
sudo apt install python3 python3-pip git -y
```

### 2. Projekt herunterladen

```bash
# Ins Home-Verzeichnis wechseln
cd ~

# Projekt-Ordner erstellen
mkdir kaktus-system
cd kaktus-system

# Dateien erstellen (siehe unten für Inhalte)
nano app.py
nano index.html
```

### 3. Python-Abhängigkeiten installieren

```bash
# Virtuelle Umgebung erstellen (empfohlen)
python3 -m venv venv
source venv/bin/activate

# Flask und Abhängigkeiten installieren
pip install flask flask-sqlalchemy flask-cors
```

### 4. Dateistruktur erstellen

```bash
# Erforderliche Ordner erstellen
mkdir static
mkdir backups

# index.html in static-Ordner verschieben
mv index.html static/
```

Die Dateistruktur sollte so aussehen:
```
kaktus-system/
├── app.py              # Flask-Backend
├── static/
│   └── index.html      # Frontend
├── backups/            # Backup-Ordner (wird automatisch erstellt)
├── kaktus.db          # SQLite-Datenbank (wird automatisch erstellt)
└── venv/              # Python Virtual Environment
```

### 5. System starten

```bash
# Virtual Environment aktivieren (falls nicht aktiv)
source venv/bin/activate

# App starten
python3 app.py
```

Das System läuft nun auf:
- **Lokal**: http://localhost:5000
- **Im Netzwerk**: http://[RASPBERRY-PI-IP]:5000

Die IP-Adresse deines Raspberry Pi findest du mit:
```bash
hostname -I
```

## 🚀 Autostart einrichten

### Systemd Service erstellen (empfohlen)

1. Service-Datei erstellen:
```bash
sudo nano /etc/systemd/system/kaktus.service
```

2. Folgenden Inhalt einfügen:
```ini
[Unit]
Description=Kaktus Anzucht System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/kaktus-system
Environment="PATH=/home/pi/kaktus-system/venv/bin"
ExecStart=/home/pi/kaktus-system/venv/bin/python /home/pi/kaktus-system/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Service aktivieren:
```bash
# Service neu laden
sudo systemctl daemon-reload

# Service aktivieren
sudo systemctl enable kaktus.service

# Service starten
sudo systemctl start kaktus.service

# Status prüfen
sudo systemctl status kaktus.service
```

## 📱 Zugriff von anderen Geräten

### Im lokalen Netzwerk:
1. Öffne einen Browser auf PC, Tablet oder Smartphone
2. Gib die IP-Adresse des Raspberry Pi ein: `http://192.168.x.x:5000`

### Von außerhalb (optional):
- Port-Forwarding im Router einrichten (Port 5000)
- DynDNS-Service verwenden für feste Adresse
- **Sicherheitshinweis**: Verwende HTTPS und Authentifizierung für externen Zugriff!

## 💾 Backup & Restore

### Backup erstellen:
```bash
# Manuelles Backup der Datenbank
cp kaktus.db backups/kaktus_$(date +%Y%m%d_%H%M%S).db
```

### Automatisches Backup (Cron):
```bash
# Crontab öffnen
crontab -e

# Tägliches Backup um 2 Uhr nachts hinzufügen:
0 2 * * * cp /home/pi/kaktus-system/kaktus.db /home/pi/kaktus-system/backups/kaktus_$(date +\%Y\%m\%d).db
```

### Daten exportieren:
Das System bietet einen Export aller Daten als ZIP-Datei mit CSV-Dateien:
- Öffne das System im Browser
- Navigiere zu: `http://[IP]:5000/api/export/all`

## 🛠️ Konfiguration

### Port ändern:
In `app.py` ganz unten:
```python
app.run(host='0.0.0.0', port=5000, debug=False)  # Port hier ändern
```

### Produktionsmodus:
Für den Dauerbetrieb in `app.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=False)  # debug=False für Produktion
```

## 📊 Datenbank

Das System verwendet SQLite als Datenbank. Die Datei `kaktus.db` enthält alle Daten.

### Datenbank zurücksetzen:
```bash
# VORSICHT: Löscht alle Daten!
rm kaktus.db
python3 app.py  # Erstellt neue, leere Datenbank
```

### Datenbank-Schema anzeigen:
```bash
sqlite3 kaktus.db ".schema"
```

## 🐛 Fehlerbehebung

### System läuft nicht:
```bash
# Logs prüfen
sudo journalctl -u kaktus.service -f

# Port prüfen
sudo netstat -tlnp | grep 5000
```

### Keine Verbindung möglich:
```bash
# Firewall prüfen
sudo ufw status

# Port freigeben (falls UFW aktiv)
sudo ufw allow 5000
```

### Berechtigungsfehler:
```bash
# Berechtigungen korrigieren
chmod 755 /home/pi/kaktus-system
chmod 644 /home/pi/kaktus-system/kaktus.db
```

## 📱 Mobile Nutzung

Das System ist vollständig responsive und funktioniert auf:
- Desktop-Browsern (Chrome, Firefox, Safari, Edge)
- Tablets (iPad, Android-Tablets)
- Smartphones (iOS, Android)

**Tipp**: Auf mobilen Geräten kann die Seite als "App" zum Homescreen hinzugefügt werden.

## 🔒 Sicherheit

### Für lokale Nutzung:
- Standardkonfiguration ist ausreichend
- Raspberry Pi sollte sich in sicherem Heimnetzwerk befinden

### Für externen Zugriff (nicht empfohlen ohne zusätzliche Sicherheit):
1. Nginx als Reverse Proxy installieren
2. SSL-Zertifikat einrichten (Let's Encrypt)
3. Basic Authentication hinzufügen
4. Firewall konfigurieren

## 📈 Performance

### Optimierungen für Raspberry Pi:
- SQLite ist optimal für Single-User-Betrieb
- Bei >10.000 Einträgen ggf. auf PostgreSQL wechseln
- Regelmäßige Backups nicht zur Hauptnutzungszeit

### Ressourcenverbrauch:
- RAM: ~50-100 MB
- CPU: Minimal (<5% im Idle)
- Speicher: ~10 MB + Datenbankgröße

## 🆘 Support & Kontakt

Bei Fragen oder Problemen:
1. Prüfe diese README
2. Schaue in die Logs: `sudo journalctl -u kaktus.service`
3. Erstelle ein Issue auf GitHub (falls verfügbar)

## 📄 Lizenz

Dieses Projekt ist für private Nutzung freigegeben. 
Kommerzielle Nutzung bitte anfragen.

## 🌟 Features in Entwicklung

- [ ] Foto-Upload für Pflanzen
- [ ] Wetter-Integration
- [ ] Email-Benachrichtigungen
- [ ] Multi-User-Support
- [ ] Automatische Pflegeerinnerungen

## 🙏 Danksagung

Entwickelt mit Liebe für die Kakteen-Community 🌵

---

**Version**: 1.0.0  
**Letzte Aktualisierung**: September 2025