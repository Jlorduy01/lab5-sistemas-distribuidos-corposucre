import uuid
from typing import List, Optional

from interoperabilidad.mpi_service import MPIService, UMBRAL_COINCIDENCIA_SUGERIDO
from interoperabilidad.models import IdentidadFederada, Paciente


class MPIEstudiante(MPIService):

    def calcular_score(self, paciente_a: Paciente, paciente_b: Paciente) -> float:
        score = 0.0

        doc_a = str(paciente_a.documento_identidad).strip().lower()
        doc_b = str(paciente_b.documento_identidad).strip().lower()
        if doc_a and doc_b and doc_a == doc_b:
            score += 0.70

        nom_a = str(paciente_a.nombre_completo).strip().lower()
        nom_b = str(paciente_b.nombre_completo).strip().lower()
        if nom_a and nom_b and nom_a == nom_b:
            score += 0.20
        elif nom_a and nom_b and any(token in nom_b for token in nom_a.split() if len(token) > 2):
            score += 0.10

        if paciente_a.fecha_nacimiento and paciente_b.fecha_nacimiento:
            if str(paciente_a.fecha_nacimiento) == str(paciente_b.fecha_nacimiento):
                score += 0.10

        return min(1.0, round(score, 2))

    def resolver_identidad(
        self, paciente: Paciente, candidatos: List[Paciente]
    ) -> Optional[IdentidadFederada]:
        if not candidatos:
            return None

        mejor_score = 0.0
        mejor_candidato = None

        for cand in candidatos:
            sc = self.calcular_score(paciente, cand)
            if sc > mejor_score:
                mejor_score = sc
                mejor_candidato = cand

        if mejor_score >= UMBRAL_COINCIDENCIA_SUGERIDO and mejor_candidato is not None:
            pacientes_map = {
                paciente.sede_origen.id_sede: paciente,
                mejor_candidato.sede_origen.id_sede: mejor_candidato
            }
            return IdentidadFederada(
                id_mpi=uuid.uuid4(),
                pacientes_por_sede=pacientes_map,
                score_coincidencia=mejor_score
            )

        return None

