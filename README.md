# Arquitectura Distribuida e Interoperabilidad Semántica para Historias Clínicas Heterogéneas

**Asignatura:** Sistemas Distribuidos  
**Evaluación:** Laboratorio Guiado N.º 5 — Sustentación Técnica de Diseño  
**Institución:** Corporación Universitaria Antonio José de Sucre (CORPOSUCRE)  
**Normativa Aplicada:** Resolución 866 de 2021 (Minsalud Colombia)  
**Estándares:** HL7 FHIR R4 / HL7v2  

---

## Integrantes del Equipo (Autores)
* **Jesús Armando Lorduy Martinez**
* **Gerneidis Requena Berrio**

---

## 1. Introducción y Planteamiento del Problema

La fragmentación de la información clínica en el sistema de salud representa un desafío crítico para la continuidad asistencial y la seguridad del paciente. En entornos hospitalarios distribuidos, es habitual que distintas sedes operen con sistemas de información heterogéneos (HIS, EMR, LIS/PACS) provistos por diferentes casas de software. Esta disparidad genera silos de información, registros duplicados sin un identificador único federado y la imposibilidad de intercambiar datos clínicos con validez semántica.

Este proyecto documenta el diseño, implementación y validación de un middleware de interoperabilidad distribuido que interconecta tres sedes hospitalarias independientes:
1. **Sede 1:** Sincelejo
2. **Sede 2:** Cartagena
3. **Sede 3:** Corozal

### Objetivo del Sistema
Lograr la transición del **0.0% al 100.0%** en la cobertura de interoperabilidad mediante la orquestación en contenedores Docker, la transformación de datos al estándar **HL7 FHIR R4** (estructurado como un `Bundle` tipo `document` encabezado por una `Composition`), la unificación federada mediante un **Master Patient Index (MPI)** y la validación automatizada en Pytest.

---

## 2. Decisiones de Arquitectura de Software Distribuido

El diseño del middleware se fundamenta en los cuatro principios esenciales de los sistemas distribuidos:

* **Desacoplamiento y Asincronía:** Se implementó un patrón de publicación/suscripción mediante un bus de eventos en memoria (`HealthServiceBus`). Las sedes publican eventos de atenciones sin depender de la disponibilidad en tiempo real del servidor central.
* **Tolerancia a Fallos e Idempotencia:** Si una sede pierde conectividad, los mensajes quedan encolados. Cada mensaje garantiza idempotencia en el MPI para evitar duplicidad de registros ante reintentos de red.
* **Transparencia de Localización:** Los consumidores interactúan con una API unificada en Flask (`/api/cobertura`), abstrayendo la ubicación física y el vendor de la base de datos de origen (Sede 1, 2 o 3).
* **Consistencia Eventual:** Se adopta un modelo de consistencia eventual para la sincronización federada del MPI, priorizando la disponibilidad y escalabilidad del sistema.

---

## 3. Matriz de Trazabilidad: 57 Campos Interoperables (Res. 866 de 2021)

Se implementó el mapeo normativo completo de los 57 campos exigidos por el Ministerio de Salud de Colombia hacia los recursos FHIR R4:

| # | Campo Res. 866 / Minsalud | Tipo | HL7v2 | Recurso FHIR | Ruta / Elemento en FHIR R4 |
|---|---|---|---|---|---|
| 1 | Tipo documento identificación | Código | PID-3.5 | Patient | Patient.identifier.type.coding.code |
| 2 | Número documento identificación | Texto | PID-3.1 | Patient | Patient.identifier.value |
| 3 | Primer nombre | Texto | PID-5.2 | Patient | Patient.name.given[0] |
| 4 | Segundo nombre | Texto | PID-5.3 | Patient | Patient.name.given[1] |
| 5 | Primer apellido | Texto | PID-5.1 | Patient | Patient.name.family |
| 6 | Segundo apellido | Texto | PID-5.5 | Patient | Patient.name.extension[motherLastName] |
| 7 | Fecha de nacimiento | Fecha | PID-7 | Patient | Patient.birthDate |
| 8 | Sexo biológico | Código | PID-8 | Patient | Patient.gender |
| 18 | Código de la EPS / Aseguradora | Código | IN1-3 | Coverage | Coverage.payor.identifier.value |
| 20 | Código de habilitación IPS | Código | MSH-4 | Organization | Organization.identifier.value |
| 24 | ID Global único federado (MPI) | UUID | N/A | Patient | Patient.id |
| 25 | Número de ingreso / Atención | Texto | PV1-19 | Encounter | Encounter.identifier.value |
| 31 | Tipo de diagnóstico principal | Código | DG1-6 | Condition | Condition.extension[diagType] |
| 32 | Código diagnóstico principal (CIE-10) | Código | DG1-3.1 | Condition | Condition.code.coding[CIE10].code |
| 37 | Código de procedimiento (CUPS) | Código | PR1-3.1 | Procedure | Procedure.code.coding[CUPS].code |
| 41 | Documento del profesional de salud | Texto | ROL-3 | Practitioner | Practitioner.identifier.value |
| 45 | Medicamento (CUM / ATC) | Código | RXO-1.1 | MedicationRequest | MedicationRequest.medicationCodeableConcept.code |
| 52 | Examen de laboratorio (LOINC) | Código | OBR-4.1 | Observation | Observation.code.coding[LOINC].code |
| 54 | Valor / Resultado | Texto | OBX-5 | Observation | Observation.valueQuantity / valueString |

---

## 4. Despliegue y Orquestación en Docker

El sistema se orquesta mediante `docker compose` levantando tres microservicios principales:

1. **`pg_ips` (PostgreSQL 16):** Aloja las bases de datos independientes de cada sede (`historia_clinica_sede1`, `historia_clinica_sede2`, `historia_clinica_sede3`) y la base central de FHIR (`fhir_db`).
2. **`hapi-fhir` (HAPI FHIR v7.2.0):** Servidor central de interoperabilidad bajo el estándar HL7 FHIR R4 (puerto `8080`).
3. **`vista-unificada` (Flask):** Dashboard web que consume las métricas de cobertura en tiempo real (puerto `5000`).

### Comandos de Ejecución
```bash
# Levantar el entorno completo
docker compose up -d --build

# Ejecutar la migración a FHIR por cada sede
python migrar_a_fhir.py --sede historia_clinica_sede1
python migrar_a_fhir.py --sede historia_clinica_sede2
python migrar_a_fhir.py --sede historia_clinica_sede3
