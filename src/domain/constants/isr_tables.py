#!/usr/bin/env python3
"""
Constantes de la tabla ISR para múltiples ejercicios fiscales
Más eficiente que cargar archivos JSON en runtime
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class TramoPorcentaje:
    """Representa un tramo de la tabla ISR mensual"""

    limite_inferior: float
    limite_superior: float
    cuota_fija: float
    porcentaje_excedente: float


@dataclass
class ConstantesISR:
    """Constantes fiscales para un ejercicio específico"""

    valor_uma_diario: float
    valor_uma_anual: float
    exencion_aguinaldo_umas: int
    exencion_prima_vacacional_umas: int
    tope_lentes_mxn: float
    tope_general_deducciones_umas: float
    tope_ppr_deducciones_umas: float


@dataclass
class TopesColegiaturas:
    """Límites de deducibilidad para colegiaturas por nivel educativo"""

    preescolar: float
    primaria: float
    secundaria: float
    profesional_tecnico: float
    preparatoria: float


@dataclass
class TablaISR:
    """Tabla ISR completa para un ejercicio fiscal"""

    ejercicio: int
    constantes: ConstantesISR
    topes_colegiaturas: TopesColegiaturas
    tabla_isr_mensual: List[TramoPorcentaje]


# =====================================================
# EJERCICIO FISCAL 2024
# =====================================================

CONSTANTES_2024 = ConstantesISR(
    valor_uma_diario=108.57,
    valor_uma_anual=39606.36,
    exencion_aguinaldo_umas=30,
    exencion_prima_vacacional_umas=15,
    tope_lentes_mxn=2500.0,
    tope_general_deducciones_umas=5.0,
    tope_ppr_deducciones_umas=5.0,
)

COLEGIATURAS_2024 = TopesColegiaturas(
    preescolar=14200.0,
    primaria=12900.0,
    secundaria=19900.0,
    profesional_tecnico=17100.0,
    preparatoria=24500.0,
)

TABLA_ISR_MENSUAL_2024 = [
    TramoPorcentaje(0.01, 746.04, 0.0, 0.0192),
    TramoPorcentaje(746.05, 6332.05, 14.32, 0.064),
    TramoPorcentaje(6332.06, 11128.0, 371.83, 0.1088),
    TramoPorcentaje(11128.01, 12935.81, 893.64, 0.16),
    TramoPorcentaje(12935.82, 15487.71, 1182.89, 0.1792),
    TramoPorcentaje(15487.72, 31236.49, 1640.18, 0.2136),
    TramoPorcentaje(31236.50, 49233.01, 4998.95, 0.2352),
    TramoPorcentaje(49233.02, 93993.9, 9235.19, 0.28),
    TramoPorcentaje(93993.91, 125325.2, 21768.14, 0.32),
    TramoPorcentaje(125325.21, 375975.6, 31794.26, 0.34),
    TramoPorcentaje(375975.61, float("inf"), 117020.5, 0.35),
]

ISR_2024 = TablaISR(
    ejercicio=2024,
    constantes=CONSTANTES_2024,
    topes_colegiaturas=COLEGIATURAS_2024,
    tabla_isr_mensual=TABLA_ISR_MENSUAL_2024,
)

# =====================================================
# EJERCICIO FISCAL 2025
# =====================================================

CONSTANTES_2025 = ConstantesISR(
    valor_uma_diario=108.57,  # Actualizar cuando se publiquen valores oficiales
    valor_uma_anual=39606.36,  # Actualizar cuando se publiquen valores oficiales
    exencion_aguinaldo_umas=30,
    exencion_prima_vacacional_umas=15,
    tope_lentes_mxn=2500.0,
    tope_general_deducciones_umas=5.0,
    tope_ppr_deducciones_umas=5.0,
)

COLEGIATURAS_2025 = TopesColegiaturas(
    preescolar=14200.0,  # Actualizar cuando se publiquen valores oficiales
    primaria=12900.0,
    secundaria=19900.0,
    profesional_tecnico=17100.0,
    preparatoria=24500.0,
)

TABLA_ISR_MENSUAL_2025 = [
    TramoPorcentaje(0.01, 746.04, 0.0, 0.0192),
    TramoPorcentaje(746.05, 6332.05, 14.32, 0.064),
    TramoPorcentaje(6332.06, 11128.01, 371.83, 0.1088),
    TramoPorcentaje(11128.02, 12935.82, 893.63, 0.16),
    TramoPorcentaje(12935.83, 15487.71, 1182.88, 0.1792),
    TramoPorcentaje(15487.72, 31236.49, 1640.18, 0.2136),
    TramoPorcentaje(31236.50, 49233.01, 4998.95, 0.2352),
    TramoPorcentaje(49233.02, 93993.9, 9235.19, 0.28),
    TramoPorcentaje(93993.91, 125325.2, 21768.14, 0.32),
    TramoPorcentaje(125325.21, 375975.6, 31794.26, 0.34),
    TramoPorcentaje(375975.61, float("inf"), 117020.5, 0.35),
]

ISR_2025 = TablaISR(
    ejercicio=2025,
    constantes=CONSTANTES_2025,
    topes_colegiaturas=COLEGIATURAS_2025,
    tabla_isr_mensual=TABLA_ISR_MENSUAL_2025,
)

# =====================================================
# DICCIONARIO PARA ACCESO POR AÑO
# =====================================================

TABLAS_ISR: Dict[int, TablaISR] = {
    2024: ISR_2024,
    2025: ISR_2025,
}


def get_tabla_isr(ejercicio: int) -> TablaISR:
    """
    Obtiene la tabla ISR para el ejercicio fiscal especificado

    Args:
        ejercicio: Año del ejercicio fiscal

    Returns:
        TablaISR correspondiente al ejercicio

    Raises:
        KeyError: Si no existe la tabla para el ejercicio solicitado
    """
    if ejercicio not in TABLAS_ISR:
        # Si no existe el año solicitado, usar el más reciente disponible
        ejercicio_disponible = max(TABLAS_ISR.keys())
        return TABLAS_ISR[ejercicio_disponible]

    return TABLAS_ISR[ejercicio]
