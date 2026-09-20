"""
app.py — IMPLEMENTACIÓN OFICIAL DE EQUIPO
Autores: Jesús Armando Lorduy Martinez & Gerneidis Requena Berrio
Asignatura: Sistemas Distribuidos - Laboratorio 5
"""
import os
import psycopg2
from flask import Flask, jsonify, render_template

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "pg_ips")
DB_USER = os.getenv("DB_USER", "ips_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "CAMBIAR_ESTA_CLAVE")
DB_PORT = int(os.getenv("DB_PORT", 5432))

SEDES = [
    {"nombre_bd": "historia_clinica_sede1", "ciudad": "Sincelejo"},
    {"nombre_bd": "historia_clinica_sede2", "ciudad": "Cartagena"},
    {"nombre_bd": "historia_clinica_sede3", "ciudad": "Corozal"},
]


def calcular_cobertura(nombre_bd: str) -> float:
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=nombre_bd,
            connect_timeout=3
        )
        cursor = conn.cursor()
        
        # Total de pacientes
        cursor.execute("SELECT COUNT(*) FROM pacientes;")
        total = cursor.fetchone()[0]
        
        if total == 0:
            cursor.close()
            conn.close()
            return 0.0

        # Pacientes con fhir_patient_id asignado
        cursor.execute("SELECT COUNT(*) FROM pacientes WHERE fhir_patient_id IS NOT NULL;")
        migrados = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()

        porcentaje = round((migrados / total) * 100.0, 1)
        return float(porcentaje)
    except Exception as e:
        print(f"Error al conectar a {nombre_bd}: {e}")
        return 0.0


@app.route("/api/cobertura")
def api_cobertura():
    resultado = []
    for sede in SEDES:
        pct = calcular_cobertura(sede["nombre_bd"])
        resultado.append({"ciudad": sede["ciudad"], "cobertura_pct": pct})
    return jsonify(resultado)


@app.route("/")
def dashboard():
    sedes_con_cobertura = []
    for sede in SEDES:
        pct = calcular_cobertura(sede["nombre_bd"])
        sedes_con_cobertura.append({
            "nombre_bd": sede["nombre_bd"],
            "ciudad": sede["ciudad"],
            "cobertura_pct": pct
        })
    return render_template("index.html", sedes=sedes_con_cobertura)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
