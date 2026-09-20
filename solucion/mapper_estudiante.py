from typing import Any, Dict
import requests

from interoperabilidad.mappers import HL7v2ToFhirMapper
from interoperabilidad.models import Encuentro, Paciente


class MapperEstudiante(HL7v2ToFhirMapper):

    def mapear_paciente(self, paciente: Paciente) -> Dict[str, Any]:
        return {
            "resourceType": "Patient",
            "id": str(paciente.id_paciente),
            "identifier": [
                {
                    "system": "urn:oid:co-documento-identidad",
                    "value": str(paciente.documento_identidad),
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": str(paciente.tipo_documento)
                            }
                        ]
                    }
                }
            ],
            "name": [
                {
                    "text": str(paciente.nombre_completo)
                }
            ],
            "gender": "male" if str(paciente.sexo).lower().startswith("m") else "female",
            "birthDate": str(paciente.fecha_nacimiento)
        }

    def mapear_condicion(self, encuentro: Encuentro, condicion) -> Dict[str, Any]:
        return {
            "resourceType": "Condition",
            "id": str(getattr(condicion, "id_condicion", "")),
            "subject": {
                "reference": f"Patient/{encuentro.paciente.id_paciente}"
            },
            "encounter": {
                "reference": f"Encounter/{encuentro.id_encuentro}"
            },
            "code": {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/icd-10",
                        "code": str(condicion.codigo_cie10),
                        "display": str(getattr(condicion, "descripcion", ""))
                    }
                ],
                "text": str(getattr(condicion, "descripcion", ""))
            },
            "recordedDate": str(getattr(condicion, "fecha_diagnostico", ""))
        }

    def mapear_observacion(self, encuentro: Encuentro, observacion) -> Dict[str, Any]:
        return {
            "resourceType": "Observation",
            "id": str(getattr(observacion, "id_observacion", "")),
            "status": "final",
            "subject": {
                "reference": f"Patient/{encuentro.paciente.id_paciente}"
            },
            "encounter": {
                "reference": f"Encounter/{encuentro.id_encuentro}"
            },
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": str(observacion.codigo_loinc)
                    }
                ]
            },
            "valueQuantity": {
                "value": str(getattr(observacion, "valor", "")),
                "unit": str(getattr(observacion, "unidad", ""))
            },
            "effectiveDateTime": str(getattr(observacion, "fecha_medicion", ""))
        }

    def generar_bundle_document(self, encuentro: Encuentro) -> Dict[str, Any]:
        recurso_paciente = self.mapear_paciente(encuentro.paciente)

        composition = {
            "resourceType": "Composition",
            "status": "final",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "11503-0",
                        "display": "Medical Records"
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{encuentro.paciente.id_paciente}"
            },
            "date": str(encuentro.fecha_atencion),
            "title": f"Registro de Atencion - {encuentro.sede.nombre_ciudad}",
            "section": []
        }

        entries = [
            {"resource": composition},
            {"resource": recurso_paciente}
        ]

        for cond in getattr(encuentro, "condiciones", []):
            entries.append({"resource": self.mapear_condicion(encuentro, cond)})

        for obs in getattr(encuentro, "observaciones", []):
            entries.append({"resource": self.mapear_observacion(encuentro, obs)})

        return {
            "resourceType": "Bundle",
            "type": "document",
            "entry": entries
        }

    def enviar_a_servidor_fhir(self, recurso: Dict[str, Any], base_url: str) -> Dict[str, Any]:
        tipo_recurso = recurso.get("resourceType", "")
        url = f"{base_url.rstrip('/')}/{tipo_recurso}"
        headers = {"Content-Type": "application/fhir+json; charset=utf-8"}
        try:
            resp = requests.post(url, json=recurso, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                return resp.json()
            return {"id": recurso.get("id", "id-local"), "status": resp.status_code}
        except Exception:
            return {"id": recurso.get("id", "id-local"), "status": "error_red"}

