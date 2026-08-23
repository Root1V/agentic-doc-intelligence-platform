"""Document-type classification — new relative to the PoC, which had no
notion of document-level type (only PaddleOCR's built-in per-*region* labels).
A single structured-output call produces a routing decision; nothing
downstream needs to know how that decision was made."""

from __future__ import annotations

from pydantic import BaseModel, Field

from idp.config import Settings
from idp.domain.document_types import DocumentType
from idp.llm.structured_output import extract_structured
from idp.observability.otel import traced_llm_call
from idp.parsing.normalize import ParsedDocument

_TYPE_DESCRIPTIONS = {
    DocumentType.PAYSLIP: "boleta de pago — detalle de ingresos/descuentos de un empleado en un periodo",
    DocumentType.INSURANCE_DISCLOSURE: "declaracion personal de seguros (p. ej. seguro de desgravamen) asociada a un prestamo",
    DocumentType.AUTHORIZATION_LETTER: (
        "carta de autorizacion breve (1 pagina, formato carta) en la que una persona autoriza a un tercero "
        "(empleador, banco) a actuar en su nombre o a descontar dinero de sus ingresos — p. ej. autorizacion "
        "de descuento por planilla para amortizar un prestamo personal. No es un formulario con secciones "
        "ni casillas de seleccion."
    ),
    DocumentType.LOAN_APPLICATION: (
        "solicitud de prestamo o convenio bancario — un FORMULARIO extenso (varias secciones marcadas con "
        "letras A, B, C..., casillas de seleccion, campos para llenar) que recopila datos del prestamo, "
        "datos personales del solicitante, datos laborales, del conyuge, patrimonio, referencias y una "
        "seccion de evaluacion/aprobacion del banco. Se distingue de authorization_letter por ser un "
        "formulario de captura de datos multi-seccion, no una carta corta de autorizacion."
    ),
    DocumentType.GENERIC: "cualquier otro documento que no encaje claramente en los tipos anteriores",
}
_TYPE_LIST = "\n".join(f"- {t.value}: {desc}" for t, desc in _TYPE_DESCRIPTIONS.items())

_SYSTEM_PROMPT = f"""Eres un clasificador de documentos empresariales. Dado el texto \
extraido de un documento, determina su tipo. Los tipos validos son:
{_TYPE_LIST}

Si el documento no encaja claramente en ninguno de los tipos especificos, clasifica como generic.
Responde con el tipo, tu confianza (0-1) y una breve justificacion."""


class ClassificationResult(BaseModel):
    document_type: DocumentType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


def classify(settings: Settings, parsed: ParsedDocument) -> ClassificationResult:
    text_excerpt = parsed.full_text[:4000]
    with traced_llm_call(role="reasoning", model=settings.reasoning_model):
        result = extract_structured(
            settings,
            role="reasoning",
            response_model=ClassificationResult,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Texto del documento:\n\n{text_excerpt}"},
            ],
        )
    return result


def needs_review(settings: Settings, result: ClassificationResult) -> bool:
    return result.confidence < settings.classification_confidence_threshold or result.document_type == DocumentType.GENERIC
