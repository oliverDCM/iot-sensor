import paho.mqtt.client as mqtt
import mysql.connector
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import time

# ── Firebase init ──────────────────────────────────────
cred = credentials.Certificate("/app/firebase-key.json")
firebase_admin.initialize_app(cred)
db_firebase = firestore.client()

# ── MariaDB  ───
def conectar_db():
    while True:
        try:
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASS'),
                autocommit=True
            )
            return conn
        except:
            print("[DB] Esperando MariaDB...")
            time.sleep(3)

db = conectar_db()
topic = os.getenv('MQTT_TOPIC')

def on_message(client, userdata, msg):
    global db
    try:
        data = json.loads(msg.payload.decode())

        if not db.is_connected():
            db = conectar_db()
        cursor = db.cursor()
        sql = "INSERT INTO lecturas (sensor, deteccion, estado, timestamp_esp) VALUES (%s, %s, %s, %s)"
        values = (data['sensor'], 1 if data['deteccion'] else 0, data['estado'], data['timestamp'])
        cursor.execute(sql, values)
        cursor.close()

       
        db_firebase.collection("lecturas").add({
            "sensor":    data['sensor'],
            "deteccion": data['deteccion'],
            "estado":    data['estado'],
            "timestamp": data['timestamp'],
            "fecha":     firestore.SERVER_TIMESTAMP
        })

        print(f"[OK] Guardado en MariaDB + Firebase: {data['estado']}")

    except Exception as e:
        print(f"Error: {e}")

client = mqtt.Client()
client.on_message = on_message
client.connect(os.getenv('MQTT_HOST'), 1883)
client.subscribe(topic)
client.loop_forever()