#!/usr/bin/env python3
"""
Módulo para generar recomendaciones fiscales usando IA
Sigue los principios SOLID para mantener código limpio y extensible
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import google.generativeai as genai


class RecommendationGenerator(ABC):
    """
    Interfaz abstracta para generadores de recomendaciones fiscales
    Principio: Interface Segregation Principle (ISP)
    """

    @abstractmethod
    def generate_recommendations(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> List[str]:
        """Genera recomendaciones fiscales personalizadas"""
        pass


class FallbackRecommendationGenerator(RecommendationGenerator):
    """
    Generador de recomendaciones por defecto
    Principio: Single Responsibility Principle (SRP)
    """

    def generate_recommendations(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> List[str]:
        """Genera recomendaciones fiscales por defecto"""
        return [
            "<li><strong>Maximizar deducciones personales:</strong> Asegúrate de conservar todos los comprobantes fiscales de gastos médicos, dentales, gastos funerarios, donativos, intereses reales de créditos hipotecarios y primas de seguros de gastos médicos mayores para el próximo ejercicio fiscal.</li>",
            "<li><strong>Planificación de inversiones:</strong> Considera abrir una cuenta de ahorro para el retiro (PPR) que te permita deducir hasta 5 UMAs anuales, reduciendo tu base gravable y generando rendimientos a largo plazo con beneficios fiscales.</li>",
            "<li><strong>Estrategia de colegiaturas:</strong> Si tienes gastos educativos, verifica que las instituciones estén autorizadas por la SEP y que los montos no excedan los topes establecidos por nivel educativo para maximizar esta deducción.</li>",
            "<li><strong>Optimización de retenciones:</strong> Revisa con tu empleador la posibilidad de ajustar las retenciones mensuales para evitar retenciones excesivas que generen saldos a favor importantes.</li>",
            "<li><strong>Documentación y cumplimiento:</strong> Mantén un archivo digital organizado de todos tus comprobantes fiscales y considera usar herramientas de gestión fiscal para automatizar el seguimiento de deducciones durante el año.</li>",
            "<li><strong>Consulta especializada:</strong> Dada la complejidad de tu situación fiscal, considera una consulta con un contador público certificado para identificar oportunidades específicas de optimización fiscal.</li>",
        ]


class GeminiRecommendationGenerator(RecommendationGenerator):
    """
    Generador de recomendaciones usando la API de Gemini
    Principio: Single Responsibility Principle (SRP)
    """

    def __init__(self, api_key: str | None = None):
        """
        Inicializa el generador de Gemini

        Args:
            api_key: Clave de API de Gemini. Si no se proporciona, se busca en variables de entorno
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Usar gemini-2.5-pro que es más ampliamente disponible
            self.model = genai.GenerativeModel("gemini-2.5-pro")
        else:
            self.model = None

    def generate_recommendations(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> List[str]:
        """
        Genera recomendaciones fiscales usando Gemini AI

        Args:
            calculation_result: Resultado del cálculo fiscal
            user_data: Datos del contribuyente
            fiscal_year: Año fiscal

        Returns:
            Lista de recomendaciones en formato HTML
        """
        if not self.model:
            raise ValueError("Gemini API key not configured")

        prompt = self._create_prompt(calculation_result, user_data, fiscal_year)

        try:
            response = self.model.generate_content(prompt)

            if response.text:
                return self._process_response(response.text)
            else:
                raise ValueError("Empty response from Gemini")

        except Exception as e:
            raise RuntimeError(f"Error generating recommendations with Gemini: {e}")

    def _create_prompt(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> str:
        """
        Crea el prompt contextualizado para Gemini
        Principio: Single Responsibility Principle (SRP)
        """
        ingresos = user_data["ingresos"]
        contribuyente = user_data["contribuyente"]

        return f"""
        Eres un experto fiscal mexicano especializado en optimización fiscal para personas físicas. 
        Analiza la siguiente situación fiscal y proporciona 5-6 recomendaciones específicas y profesionales para maximizar el retorno fiscal.

        DATOS DEL CONTRIBUYENTE:
        - Nombre: {contribuyente.get("nombre_o_referencia", "No especificado")}
        - Ejercicio fiscal: {fiscal_year}
        - Ingreso bruto anual: ${calculation_result.gross_annual_income:,.2f}
        - Ingreso gravado total: ${calculation_result.total_taxable_income:,.2f}
        - Deducciones actuales: ${calculation_result.authorized_deductions:,.2f}
        - Base gravable: ${calculation_result.taxable_base:,.2f}
        - Impuesto determinado: ${calculation_result.determined_tax:,.2f}
        - Impuesto retenido: ${calculation_result.withheld_tax:,.2f}
        - Saldo a favor: ${calculation_result.balance_in_favor:,.2f}
        - Saldo a pagar: ${calculation_result.balance_to_pay:,.2f}

        CONTEXTO ADICIONAL:
        - Ingreso mensual ordinario: ${ingresos.get("ingreso_bruto_mensual_ordinario", 0):,.2f}
        - Días de aguinaldo: {ingresos.get("dias_aguinaldo", 0)}
        - Días de vacaciones: {ingresos.get("dias_vacaciones_anuales", 0)}

        INSTRUCCIONES:
        1. Analiza la situación fiscal específica de este contribuyente
        2. Proporciona recomendaciones ESPECÍFICAS y PRÁCTICAS para el próximo ejercicio fiscal
        3. Considera las leyes fiscales mexicanas vigentes para {fiscal_year + 1}
        4. Enfócate en estrategias legales para maximizar deducciones y minimizar impuestos
        5. Incluye números específicos cuando sea relevante
        6. Cada recomendación debe tener un título en negrita y una explicación detallada
        
        FORMATO DE RESPUESTA:
        Responde únicamente con 5-6 recomendaciones en formato HTML <li>, cada una con:
        - Un título descriptivo en <strong>
        - Una explicación detallada de 2-3 líneas
        - Sin numeración manual (se manejará automáticamente)
        
        Ejemplo de formato:
        <li><strong>Título de la recomendación:</strong> Explicación detallada de la estrategia fiscal específica para este contribuyente...</li>
        """

    def _process_response(self, response_text: str) -> List[str]:
        """
        Procesa la respuesta de Gemini y la convierte a formato de lista HTML
        Principio: Single Responsibility Principle (SRP)
        """
        import re

        # Limpiar la respuesta
        response_text = response_text.strip()

        # Si ya viene en formato HTML, extraer elementos <li>
        recommendations = re.findall(r"<li>.*?</li>", response_text, re.DOTALL)
        if recommendations:
            return recommendations

        # Si viene en formato markdown, convertir a HTML
        lines = response_text.split("\n")
        formatted_recommendations = []

        for line in lines:
            line = line.strip()
            if line and ("**" in line or "*" in line):
                # Convertir formato markdown a HTML
                line = line.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
                line = line.replace("*", "<strong>", 1).replace("*", "</strong>", 1)

                if not line.startswith("<li>"):
                    line = f"<li>{line}</li>"

                formatted_recommendations.append(line)

        return (
            formatted_recommendations
            if formatted_recommendations
            else [
                "<li><strong>Error procesando recomendaciones:</strong> No se pudieron procesar las recomendaciones de IA correctamente.</li>"
            ]
        )


class RecommendationService:
    """
    Servicio principal para generar recomendaciones fiscales
    Principios: Dependency Inversion Principle (DIP) y Open/Closed Principle (OCP)
    """

    def __init__(
        self,
        primary_generator: RecommendationGenerator,
        fallback_generator: RecommendationGenerator,
    ):
        """
        Inicializa el servicio con generadores primario y de respaldo

        Args:
            primary_generator: Generador principal (ej: Gemini)
            fallback_generator: Generador de respaldo (recomendaciones por defecto)
        """
        self.primary_generator = primary_generator
        self.fallback_generator = fallback_generator

    def get_recommendations(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> List[str]:
        """
        Obtiene recomendaciones fiscales usando el generador primario,
        con fallback automático en caso de error

        Args:
            calculation_result: Resultado del cálculo fiscal
            user_data: Datos del contribuyente
            fiscal_year: Año fiscal

        Returns:
            Lista de recomendaciones en formato HTML
        """
        try:
            print("🤖 Generando recomendaciones fiscales personalizadas con IA...")
            recommendations = self.primary_generator.generate_recommendations(
                calculation_result, user_data, fiscal_year
            )
            print("✅ Recomendaciones generadas exitosamente con IA")
            return recommendations

        except Exception as e:
            print(f"⚠️  Error con generador primario: {e}")
            print("🔄 Usando recomendaciones por defecto...")

            return self.fallback_generator.generate_recommendations(
                calculation_result, user_data, fiscal_year
            )


class RecommendationFactory:
    """
    Factory para crear servicios de recomendaciones
    Principio: Factory Pattern y Single Responsibility Principle (SRP)
    """

    @staticmethod
    def create_service(
        use_ai: bool = True, api_key: str | None = None
    ) -> RecommendationService:
        """
        Crea un servicio de recomendaciones configurado

        Args:
            use_ai: Si usar IA (Gemini) como generador primario
            api_key: Clave de API de Gemini

        Returns:
            Servicio de recomendaciones configurado
        """
        fallback_generator = FallbackRecommendationGenerator()

        if use_ai:
            try:
                primary_generator = GeminiRecommendationGenerator(api_key)
                return RecommendationService(primary_generator, fallback_generator)
            except Exception as e:
                print(f"⚠️  No se pudo configurar Gemini: {e}")
                print("🔄 Usando solo recomendaciones por defecto...")

        # Si no se puede usar IA, usar fallback como primario
        return RecommendationService(fallback_generator, fallback_generator)
