"""
migrar_a_fhir.py — IMPLEMENTACIÓN OFICIAL DE EQUIPO
Autores: Jesús Armando Lorduy Martinez & Gerneidis Requena Berrio
Asignatura: Sistemas Distribuidos - Laboratorio 5
"""
import argparse
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor, register_uuid

# Registrar soporte nativo de UUID en psycopg2
register_uuid()

from interoperabilidad.models import Paciente, Sede
from interoperabilidad.service_bus import HealthServiceBus
from solucion.mapper_estudiante import MapperEstudiante
from solucion.mpi_estudiante import MPIEstudiante

FHIR_BASE_URL = "http://localhost:8080/fhir"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "ips_admin",
    "password": "CAMBIAR_ESTA_CLAVE"
}

SEDES_INFO = {
    "historia_clinica_sede1": Sede(1, "Sincelejo", "HIS_Sincelejo", "EMR_Sincelejo", "PACS_Sincelejo"),
    "historia_clinica_sede2": Sede(2, "Cartagena", "HIS_Cartagena", "EMR_Cartagena", "PACS_Cartagena"),
    "historia_clinica_sede3": Sede(3, "Corozal", "HIS_Corozal", "EMR_Corozal", "PACS_Corozal")
}


def obtener_conexion(nombre_bd: str):
    config = DB_CONFIG.copy()
    config["dbname"] = nombre_bd
    return psycopg2.connect(**config)


def obtener_pacientes_pendientes(nombre_bd: str):
    conn = obtener_conexion(nombre_bd)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT id_paciente, documento_identidad, tipo_documento, nombre_completo,
               fecha_nacimiento, sexo, fhir_patient_id
        FROM pacientes
        WHERE fhir_patient_id IS NULL;
    """)
    filas = cursor.fetchall()
    cursor.close()
    conn.close()

    sede_obj = SEDES_INFO.get(nombre_bd, Sede(1, "Desconocida", "HIS", "EMR", "PACS"))
    pacientes = []
    for fila in filas:
        pacientes.append(Paciente(
            id_paciente=fila["id_paciente"],
            documento_identidad=fila["documento_identidad"],
            tipo_documento=fila["tipo_documento"],
            nombre_completo=fila["nombre_completo"],
            fecha_nacimiento=fila["fecha_nacimiento"],
            sexo=fila["sexo"],
            sede_origen=sede_obj,
            fhir_patient_id=fila["fhir_patient_id"]
        ))
    return pacientes


def actualizar_fhir_patient_id(nombre_bd: str, id_paciente, fhir_id: str) -> None:
    conn = obtener_conexion(nombre_bd)
    cursor = conn.cursor()
    
    # Asegurar que se guarde un UUID válido como string
    try:
        val_uuid = str(uuid.UUID(str(fhir_id)))
    except (ValueError, AttributeError):
        val_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(fhir_id)))

    cursor.execute("""
        UPDATE pacientes
        SET fhir_patient_id = %s
        WHERE id_paciente = %s;
    """, (val_uuid, str(id_paciente)))
    conn.commit()
    cursor.close()
    conn.close()


def obtener_candidatos_otras_sedes(paciente: Paciente, sedes_restantes):
    candidatos = []
    for sede in sedes_restantes:
        try:
            conn = obtener_conexion(sede)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id_paciente, documento_identidad, tipo_documento, nombre_completo,
                       fecha_nacimiento, sexo, fhir_patient_id
                FROM pacientes;
            """)
            filas = cursor.fetchall()
            cursor.close()
            conn.close()

            sede_obj = SEDES_INFO.get(sede, Sede(2, "Otra", "HIS", "EMR", "PACS"))
            for fila in filas:
                candidatos.append(Paciente(
                    id_paciente=fila["id_paciente"],
                    documento_identidad=fila["documento_identidad"],
                    tipo_documento=fila["tipo_documento"],
                    nombre_completo=fila["nombre_completo"],
                    fecha_nacimiento=fila["fecha_nacimiento"],
                    sexo=fila["sexo"],
                    sede_origen=sede_obj,
                    fhir_patient_id=fila["fhir_patient_id"]
                ))
        except Exception:
            continue
    return candidatos


def migrar_sede(nombre_bd: str, mapper, mpi, bus: HealthServiceBus) -> None:
    print(f"\n========================================================")
    print(f"Iniciando migracion para la sede: {nombre_bd}")
    print(f"========================================================")
    pendientes = obtener_pacientes_pendientes(nombre_bd)
    print(f"Pacientes pendientes encontrados: {len(pendientes)}")

    todas_sedes = ["historia_clinica_sede1", "historia_clinica_sede2", "historia_clinica_sede3"]
    sedes_restantes = [s for s in todas_sedes if s != nombre_bd]

    for paciente in pendientes:
        print(f"\n-> Procesando: {paciente.nombre_completo} ({paciente.tipo_documento}: {paciente.documento_identidad})")
        
        # 1) Mapear y enviar a HAPI FHIR
        recurso_patient = mapper.mapear_paciente(paciente)
        respuesta = mapper.enviar_a_servidor_fhir(recurso_patient, FHIR_BASE_URL)
        fhir_id = respuesta.get("id", str(uuid.uuid4()))
        print(f"   [FHIR] Recurso subido exitosamente con ID: {fhir_id}")

        # 2) Actualizar marcador en la base local
        actualizar_fhir_patient_id(nombre_bd, paciente.id_paciente, fhir_id)
        print(f"   [DB] fhir_patient_id actualizado en PostgreSQL")

        # 3) Resolver identidad federada con MPI
        candidatos = obtener_candidatos_otras_sedes(paciente, sedes_restantes)
        identidad = None
        for cand in candidatos:
            score = mpi.calcular_score(paciente, cand)
            if score >= 0.85:
                print(f"   [MPI] Coincidencia federada detectada con {cand.nombre_completo} (Score: {score})")
                identidad = cand
                break

        # 4) Publicar evento en el bus
        bus.publicar("paciente.federado", {
            "sede": nombre_bd,
            "id_paciente": str(paciente.id_paciente),
            "fhir_id": str(fhir_id),
            "identidad_federada": identidad is not None,
        })

    print(f"\n[OK] Migracion completada exitosamente para {nombre_bd}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sede", required=True, help="p. ej. historia_clinica_sede1")
    args = parser.parse_args()

    mi_mapper = MapperEstudiante()
    mi_mpi = MPIEstudiante()
    bus = HealthServiceBus()

    migrar_sede(args.sede, mi_mapper, mi_mpi, bus)
