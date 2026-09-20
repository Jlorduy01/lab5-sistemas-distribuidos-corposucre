#!/bin/bash
# 01-init-databases.sh — Configuración de sedes hospitalarias con autoría de equipo
# Jesús Armando Lorduy Martinez & Gerneidis Requena Berrio
set -e

for DB in historia_clinica_sede1 historia_clinica_sede2 historia_clinica_sede3; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE $DB' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB')\gexec
EOSQL

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS pacientes (
        id_paciente UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        documento_identidad VARCHAR(20) NOT NULL,
        tipo_documento VARCHAR(5) NOT NULL,
        nombre_completo VARCHAR(150) NOT NULL,
        fecha_nacimiento DATE NOT NULL,
        sexo CHAR(1) NOT NULL,
        fhir_patient_id UUID  -- NULL = 0% cobertura inicial
    );
EOSQL

  case "$DB" in
    historia_clinica_sede1)
      psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB" <<-EOSQL
        INSERT INTO pacientes (tipo_documento, documento_identidad, nombre_completo, fecha_nacimiento, sexo, fhir_patient_id) VALUES
        ('CC', '1102800001', 'Jesús Armando Lorduy Martinez', '2005-03-15', 'M', NULL),
        ('CC', '1102600004', 'María Camila Vergara Ramos', '2001-05-12', 'F', NULL),
        ('TI', '1050300005', 'Juan David Barreto Gómez', '2008-09-05', 'M', NULL),
        ('CC', '1102500006', 'Ana Milena Castro Morales', '1999-07-22', 'F', NULL),
        ('CC', '1102400007', 'Roberto Carlos Meza Salcedo', '1995-12-03', 'M', NULL);
EOSQL
      ;;
    historia_clinica_sede2)
      psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB" <<-EOSQL
        INSERT INTO pacientes (tipo_documento, documento_identidad, nombre_completo, fecha_nacimiento, sexo, fhir_patient_id) VALUES
        ('CC', '1102900002', 'Gerneidis Requena Berrio', '2004-08-20', 'F', NULL),
        ('CC', '1102600004', 'María Camila Vergara Ramos', '2001-05-12', 'F', NULL),
        ('CC', '1102300008', 'Andrés Felipe Paternina Ruiz', '1997-04-18', 'M', NULL),
        ('CC', '1102200009', 'Laura Sofía Herrera Díaz', '2002-10-30', 'F', NULL),
        ('CC', '1102100010', 'Daniel Eduardo Arrieta Buelvas', '2000-01-14', 'M', NULL);
EOSQL
      ;;
    historia_clinica_sede3)
      psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB" <<-EOSQL
        INSERT INTO pacientes (tipo_documento, documento_identidad, nombre_completo, fecha_nacimiento, sexo, fhir_patient_id) VALUES
        ('CC', '1102700003', 'Carlos Andrés Mendoza Pérez', '1998-11-10', 'M', NULL),
        ('CC', '1102000011', 'Valentina Paola Benítez Gómez', '2003-06-25', 'F', NULL),
        ('CC', '1101900012', 'Jorge Luis Monterrosa Cárdenas', '1994-09-08', 'M', NULL),
        ('CC', '1101800013', 'Diana Marcela Hoyos Hoyos', '2001-03-19', 'F', NULL),
        ('CC', '1101700014', 'Pedro José Sierra Navarro', '1996-08-11', 'M', NULL);
EOSQL
      ;;
  esac
done
