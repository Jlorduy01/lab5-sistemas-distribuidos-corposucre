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

Se implementó el mapeo normativo exhaustivo de los 57 campos exigidos por el Ministerio de Salud de Colombia hacia los recursos HL7 FHIR R4:

| # | Campo Res. 866 / Minsalud | Tipo | HL7v2 | Recurso FHIR | Ruta / Elemento en FHIR R4 |
|---|---|---|---|---|---|
| 1 | Tipo documento de identificación | Código | PID-3.5 | Patient | Patient.identifier.type.coding.code |
| 2 | Número documento de identificación | Texto | PID-3.1 | Patient | Patient.identifier.value |
| 3 | Primer nombre | Texto | PID-5.2 | Patient | Patient.name.given[0] |
| 4 | Segundo nombre | Texto | PID-5.3 | Patient | Patient.name.given[1] |
| 5 | Primer apellido | Texto | PID-5.1 | Patient | Patient.name.family |
| 6 | Segundo apellido | Texto | PID-5.5 | Patient | Patient.name.extension[motherLastName] |
| 7 | Fecha de nacimiento | Fecha | PID-7 | Patient | Patient.birthDate |
| 8 | Sexo biológico | Código | PID-8 | Patient | Patient.gender |
| 9 | Identificador de género diverso | Código | PID-8.2 | Patient | Patient.extension[genderIdentity] |
| 10 | Pertenencia étnica | Código | PID-10 | Patient | Patient.extension[race] |
| 11 | Código municipio de residencia | Código | PID-11.8 | Patient | Patient.address.city.extension[municipality] |
| 12 | Zona de residencia (Urbana/Rural) | Código | PID-11.7 | Patient | Patient.address.district |
| 13 | Dirección de residencia | Texto | PID-11.1 | Patient | Patient.address.line[0] |
| 14 | Teléfono de contacto | Texto | PID-13.1 | Patient | Patient.telecom[phone].value |
| 15 | Correo electrónico | Texto | PID-13.4 | Patient | Patient.telecom[email].value |
| 16 | Ocupación | Código | PID-10.2 | Patient | Patient.extension[occupation] |
| 17 | Tipo de usuario / Régimen | Código | PID-19 | Patient | Patient.extension[insuranceRegimen] |
| 18 | Código de la EPS / Aseguradora | Código | IN1-3 | Coverage | Coverage.payor.identifier.value |
| 19 | Nombre de la EPS / Aseguradora | Texto | IN1-4 | Coverage | Coverage.payor.display |
| 20 | Código de habilitación IPS / Sede | Código | MSH-4 | Organization | Organization.identifier.value |
| 21 | Nombre de la IPS / Sede de atención | Texto | MSH-4.2 | Organization | Organization.name |
| 22 | Código de la sede física de atención | Código | PV1-3.4 | Location | Location.identifier.value |
| 23 | Número de historia clínica local | Texto | PID-2 | Patient | Patient.identifier[local].value |
| 24 | ID Global único federado (MPI) | UUID | N/A | Patient | Patient.id |
| 25 | Número de ingreso / Atención | Texto | PV1-19 | Encounter | Encounter.identifier.value |
| 26 | Vía de ingreso / Modalidad | Código | PV1-2 | Encounter | Encounter.class.code |
| 27 | Fecha y hora inicio de atención | FechaHora | PV1-44 | Encounter | Encounter.period.start |
| 28 | Fecha y hora fin de atención | FechaHora | PV1-45 | Encounter | Encounter.period.end |
| 29 | Causa externa que motiva la atención | Código | PV1-14 | Encounter | Encounter.reasonCode.coding.code |
| 30 | Estado del paciente al egreso | Código | PV1-36 | Encounter | Encounter.hospitalization.dischargeDisposition |
| 31 | Tipo de diagnóstico principal | Código | DG1-6 | Condition | Condition.extension[diagType] |
| 32 | Código diagnóstico principal (CIE-10) | Código | DG1-3.1 | Condition | Condition.code.coding[CIE10].code |
| 33 | Descripción diagnóstico principal | Texto | DG1-3.2 | Condition | Condition.code.coding[CIE10].display |
| 34 | Código diagnóstico relacionado 1 | Código | DG1-3.1 | Condition | Condition.code.coding[related1].code |
| 35 | Código diagnóstico relacionado 2 | Código | DG1-3.1 | Condition | Condition.code.coding[related2].code |
| 36 | Código diagnóstico relacionado 3 | Código | DG1-3.1 | Condition | Condition.code.coding[related3].code |
| 37 | Código de procedimiento (CUPS) | Código | PR1-3.1 | Procedure | Procedure.code.coding[CUPS].code |
| 38 | Descripción del procedimiento (CUPS) | Texto | PR1-3.2 | Procedure | Procedure.code.coding[CUPS].display |
| 39 | Fecha y hora realización procedimiento | FechaHora | PR1-5 | Procedure | Procedure.performedDateTime |
| 40 | Finalidad del procedimiento / consulta | Código | PR1-6 | Procedure | Procedure.category.coding.code |
| 41 | Documento del profesional de salud | Texto | ROL-3 | Practitioner | Practitioner.identifier.value |
| 42 | Nombres del profesional de salud | Texto | STF-3.2 | Practitioner | Practitioner.name.given[0] |
| 43 | Apellidos del profesional de salud | Texto | STF-3.1 | Practitioner | Practitioner.name.family |
| 44 | Especialidad del profesional | Código | PRT-6 | PractitionerRole | PractitionerRole.specialty.coding.code |
| 45 | Tipo de medicamento (CUM / ATC) | Código | RXO-1.1 | MedicationRequest | MedicationRequest.medicationCodeableConcept.code |
| 46 | Nombre comercial / genérico medicamento | Texto | RXO-1.2 | MedicationRequest | MedicationRequest.medicationCodeableConcept.text |
| 47 | Forma farmacéutica | Código | RXO-5 | MedicationRequest | MedicationRequest.dosageInstruction.doseAndRate.type |
| 48 | Dosis y unidad de medida | Texto | RXE-3 | MedicationRequest | MedicationRequest.dosageInstruction.doseAndRate.doseQuantity |
| 49 | Vía de administración | Código | RXR-1 | MedicationRequest | MedicationRequest.dosageInstruction.route.coding.code |
| 50 | Frecuencia de administración | Texto | TQ1-2 | MedicationRequest | MedicationRequest.dosageInstruction.timing |
| 51 | Cantidad total recetada / dispensada | Número | RXO-11 | MedicationRequest | MedicationRequest.dispenseRequest.quantity |
| 52 | Código examen / laboratorio (LOINC) | Código | OBR-4.1 | Observation | Observation.code.coding[LOINC].code |
| 53 | Nombre del examen / laboratorio | Texto | OBR-4.2 | Observation | Observation.code.coding[LOINC].display |
| 54 | Valor / Resultado numérico o cualitativo | Texto | OBX-5 | Observation | Observation.valueQuantity / valueString |
| 55 | Unidad de medida del resultado | Texto | OBX-6 | Observation | Observation.valueQuantity.unit |
| 56 | Rango de referencia del resultado | Texto | OBX-7 | Observation | Observation.referenceRange.text |
| 57 | Fecha y hora del resultado / informe | FechaHora | OBX-14 | Observation | Observation.effectiveDateTime |

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
