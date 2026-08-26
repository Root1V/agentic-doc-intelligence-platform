"""Target extraction schema for ``debt_capacity_calculation`` — the output
of an internal BBVA loan-affordability tool ('Calculadora', referenced
internally as 'Kontigo'): given a client's credit-bureau score, income,
deductions, and existing BBVA debt by product, it computes maximum
debt-service capacity and evaluates a requested new loan against it.
Promoted from a real ``generic`` extraction (2026-08-23: 'Copia de
calcufast 9', 35 cleanly-extracted fields) once the pattern proved
extractable with a stable field set."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted

IncomeLineKind = Literal["income", "deduction"]


class ExistingDebtLine(BaseModel):
    """One row of existing BBVA debt broken down by product (Tarjeta,
    CCONVPLAN, CPLD, etc.)."""

    product: Extracted[str] = Field(description="Producto BBVA de la deuda existente (p. ej. 'BBVA Tarjeta', 'BBVA CCONVPLAN', 'BBVA CPLD').")
    debt_amount: Extracted[float] = Field(description="Monto de la deuda existente en ese producto.")
    estimated_installment: Extracted[float] | None = Field(default=None, description="Cuota mensual estimada de esa deuda.")


class IncomeOrDeductionLine(BaseModel):
    """One itemized income or deduction line feeding into the net-income
    calculation (e.g. 'REM, CONSOLIDADA', 'DL. 22595 CPMP 6% RC')."""

    kind: Extracted[IncomeLineKind] = Field(description="'income' si es un ingreso, 'deduction' si es un descuento.")
    concept: Extracted[str] = Field(description="Nombre/codigo del concepto tal como aparece.")
    amount: Extracted[float] = Field(description="Monto del concepto.")


class DebtCapacityCalculationSchema(BaseModel):
    calculation_datetime: Extracted[str] | None = Field(default=None, description="Fecha y hora en que se genero el calculo.")
    analyst_email: Extracted[str] | None = Field(default=None, description="Correo del asesor/analista BBVA que realizo el calculo.")
    calculator_type: Extracted[str] | None = Field(default=None, description="'Tipo de Calculadora'.")
    request_number: Extracted[str] | None = Field(default=None, description="'Numero de Solicitud Kontigo'.")
    client_dni: Extracted[str] = Field(description="'Documento' del cliente evaluado.")
    client_name: Extracted[str] = Field(description="'Nombre de Cliente'.")
    final_age: Extracted[str] | None = Field(default=None, description="'Edad Final' del cliente al termino del credito.")
    convenio: Extracted[str] | None = Field(default=None, description="Convenio/empleador del cliente.")
    position_modality: Extracted[str] | None = Field(default=None, description="'Modalidad / Cargo'.")
    special_condition: Extracted[str] | None = Field(default=None, description="'Condicion Especial', si se indica.")
    credit_bureau_score: Extracted[str] | None = Field(default=None, description="'Buro' — clasificacion de central de riesgo del cliente.")
    max_credit_bureau_score: Extracted[str] | None = Field(default=None, description="'Buro Maximo' permitido para el producto.")
    max_age: Extracted[str] | None = Field(default=None, description="'Edad Maxima' permitida.")
    grace_period_months: Extracted[int] | None = Field(default=None, description="'Periodo de Gracia' en meses.")
    due_day: Extracted[int] | None = Field(default=None, description="'Dia de Vencimiento' de la cuota.")
    term_months: Extracted[int] | None = Field(default=None, description="'Cuotas' — plazo del credito en meses.")
    installment_factor: Extracted[str] | None = Field(default=None, description="'Factor Cuota'.")
    fixed_income: Extracted[float] | None = Field(default=None, description="'Ingresos Fijos'.")
    variable_income: Extracted[float] | None = Field(default=None, description="'Ingresos Variables'.")
    total_deductions: Extracted[float] | None = Field(default=None, description="'Descuentos' totales.")
    net_income: Extracted[float] | None = Field(default=None, description="'Ingresos Neto'.")
    max_debt_installment: Extracted[float] | None = Field(default=None, description="'Cuota de Endeudamiento Maximo'.")
    debt_ratio_pct: Extracted[str] | None = Field(default=None, description="'% Endeudamiento'.")
    requested_product: Extracted[str] | None = Field(default=None, description="'Producto Solicitado' (codigo, p. ej. 'CCONV').")
    requested_amount: Extracted[float] | None = Field(default=None, description="'Importe Producto' solicitado.")
    requested_monthly_installment: Extracted[float] | None = Field(default=None, description="'Cuota Mensual Producto' del credito solicitado.")
    holder_number: Extracted[int] | None = Field(default=None, description="'Nro de Titular'.")
    existing_debts: list[ExistingDebtLine] = Field(
        default_factory=list, description="Cada linea de deuda BBVA existente por producto (Tarjeta, CCONVPLAN, CPLD, etc.)."
    )
    income_lines: list[IncomeOrDeductionLine] = Field(
        default_factory=list, description="Cada linea de ingreso/descuento numerada (Ingreso 1, Ingreso 2, Descuento 1, Descuento 2, ...)."
    )
    summary: Extracted[str] | None = Field(default=None, description="Resumen breve (1-2 frases) sobre que es este documento y su contenido principal.")
