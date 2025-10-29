#!/usr/bin/env python3
"""
Módulo para generar recomendaciones fiscales usando IA
Sigue los principios SOLID para mantener código limpio y extensible
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Generator
import google.generativeai as genai
from tabla_isr_constants import get_tabla_isr
from dotenv import load_dotenv

load_dotenv()


class RecommendationGenerator(ABC):
    """
    Interfaz abstracta para generadores de recomendaciones fiscales
    Principio: Interface Segregation Principle (ISP)
    """

    @abstractmethod
    def generate_recommendations_stream(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> Generator[str, None, None]:
        """Genera recomendaciones fiscales personalizadas con streaming"""
        pass


class FallbackRecommendationGenerator(RecommendationGenerator):
    """
    Generador de recomendaciones por defecto
    Principio: Single Responsibility Principle (SRP)
    """

    def generate_recommendations_stream(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ):
        """Genera recomendaciones fiscales por defecto como stream simulado en formato Markdown"""
        recommendations_markdown = """
### 1. **Maximizar deducciones personales**

Asegúrate de conservar todos los comprobantes fiscales de gastos médicos, dentales, gastos funerarios, donativos, intereses reales de créditos hipotecarios y primas de seguros de gastos médicos mayores para el próximo ejercicio fiscal.

> 💡 **Ejemplo para tu situación:**
> Con tus ingresos actuales, puedes deducir hasta el 15% en gastos médicos y generales, lo que te generaría un ahorro fiscal significativo.

---

### 2. **Planificación de inversiones (PPR)**

Considera abrir una cuenta de ahorro para el retiro (PPR) que te permita deducir hasta 5 UMAs anuales, reduciendo tu base gravable y generando rendimientos a largo plazo con beneficios fiscales.

> 💡 **Ejemplo para tu situación:**
> Puedes deducir hasta 10% de tus ingresos en PPR, lo que reduciría tu base gravable considerablemente.

---

### 3. **Estrategia de colegiaturas**

Si tienes gastos educativos, verifica que las instituciones estén autorizadas por la SEP y que los montos no excedan los topes establecidos por nivel educativo para maximizar esta deducción.

---

### 4. **Optimización de retenciones**

Revisa con tu empleador la posibilidad de ajustar las retenciones mensuales para evitar retenciones excesivas que generen saldos a favor importantes.

---

### 5. **Documentación y cumplimiento**

Mantén un archivo digital organizado de todos tus comprobantes fiscales y considera usar herramientas de gestión fiscal para automatizar el seguimiento de deducciones durante el año.

---

### 6. **Consulta especializada**

Dada la complejidad de tu situación fiscal, considera una consulta con un contador público certificado para identificar oportunidades específicas de optimización fiscal.
        """

        # Simular streaming devolviendo todo el contenido de una vez
        yield recommendations_markdown.strip()


class GeminiRecommendationGenerator(RecommendationGenerator):
    """
    Generador de recomendaciones usando Gemini AI de Google
    Principio: Single Responsibility Principle (SRP) y Dependency Inversion Principle (DIP)
    """

    def __init__(self, api_key: str | None = None):
        """
        Inicializa el generador con la API key de Gemini

        Args:
            api_key: API key de Google Gemini. Si no se proporciona, se intenta obtener de variables de entorno
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key de Google Gemini no encontrada. "
                "Proporciona api_key o configura la variable de entorno GEMINI_API_KEY"
            )

        # Configurar Gemini
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.5-pro")
        except Exception:
            self.model = None

    def _get_isr_data(self, fiscal_year: int):
        """
        Obtiene los datos ISR para el año fiscal especificado

        Args:
            fiscal_year: Año fiscal

        Returns:
            TablaISR con la información fiscal del año
        """
        return get_tabla_isr(fiscal_year)

    def generate_recommendations_stream(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ):
        """
        Genera recomendaciones fiscales usando Gemini AI con streaming

        Args:
            calculation_result: Resultado del cálculo fiscal
            user_data: Datos del contribuyente
            fiscal_year: Año fiscal

        Yields:
            Fragmentos de texto de las recomendaciones en tiempo real
        """
        if not self.model:
            raise ValueError("Gemini API key not configured")

        prompt = self._create_prompt(calculation_result, user_data, fiscal_year)

        try:
            response = self.model.generate_content(prompt, stream=True)

            accumulated_text = ""
            for chunk in response:
                if chunk.text:
                    accumulated_text += chunk.text
                    yield chunk.text

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
        tabla_isr = self._get_isr_data(fiscal_year)

        # Extraer información relevante de la tabla ISR
        constantes = tabla_isr.constantes
        topes_colegiaturas = tabla_isr.topes_colegiaturas

        return f"""
        Eres un "Gatito Fiscal" 🐱, un gato profesional asesor fiscal mexicano especializado en optimización fiscal para personas físicas. 
        Te presentas como un asesor experto que ayuda a maximizar el saldo a favor de sus clientes.
        Tienes un tono profesional pero con personalidad gatuna, usando expresiones como "miau", "purr-fecto", "gat-rantizo", "es-paw-cialmente" de manera elegante.
        Tu misión es analizar la situación fiscal y dar exactamente 5 consejos estratégicos para AUMENTAR EL SALDO A FAVOR.

        ## DATOS DEL CONTRIBUYENTE:
        - **Nombre:** {contribuyente.get("nombre_o_referencia", "No especificado")}
        - **Ejercicio fiscal:** {fiscal_year}
        - **Ingreso bruto anual:** ${calculation_result.gross_annual_income:,.2f}
        - **Ingreso gravado total:** ${calculation_result.total_taxable_income:,.2f}
        - **Deducciones actuales:** ${calculation_result.authorized_deductions:,.2f}
        - **Base gravable:** ${calculation_result.taxable_base:,.2f}
        - **Impuesto determinado:** ${calculation_result.determined_tax:,.2f}
        - **Impuesto retenido:** ${calculation_result.withheld_tax:,.2f}
        - **Saldo a favor:** ${calculation_result.balance_in_favor:,.2f}
        - **Saldo a pagar:** ${calculation_result.balance_to_pay:,.2f}

        ## CONTEXTO ADICIONAL:
        - **Ingreso mensual ordinario:** ${ingresos.get("ingreso_bruto_mensual_ordinario", 0):,.2f}
        - **Días de aguinaldo:** {ingresos.get("dias_aguinaldo", 0)}
        - **Días de vacaciones:** {ingresos.get("dias_vacaciones_anuales", 0)}

        ## LÍMITES Y TOPES FISCALES OFICIALES {fiscal_year}:
        - **UMA diario:** ${constantes.valor_uma_diario:,.2f}
        - **UMA anual:** ${constantes.valor_uma_anual:,.2f}
        - **Tope deducciones generales:** {constantes.tope_general_deducciones_umas} UMAs = ${constantes.valor_uma_anual * constantes.tope_general_deducciones_umas:,.2f}
        - **Tope PPR/Afore:** {constantes.tope_ppr_deducciones_umas} UMAs = ${constantes.valor_uma_anual * constantes.tope_ppr_deducciones_umas:,.2f}
        - **Exención aguinaldo:** {constantes.exencion_aguinaldo_umas} UMAs = ${constantes.valor_uma_anual * constantes.exencion_aguinaldo_umas / 365:,.2f} diarios
        - **Exención prima vacacional:** {constantes.exencion_prima_vacacional_umas} UMAs = ${constantes.valor_uma_anual * constantes.exencion_prima_vacacional_umas / 365:,.2f} diarios
        
        ### TOPES COLEGIATURAS {fiscal_year}:
        - **Preescolar:** ${topes_colegiaturas.preescolar:,.2f}
        - **Primaria:** ${topes_colegiaturas.primaria:,.2f}
        - **Secundaria:** ${topes_colegiaturas.secundaria:,.2f}
        - **Profesional técnico:** ${topes_colegiaturas.profesional_tecnico:,.2f}
        - **Preparatoria:** ${topes_colegiaturas.preparatoria:,.2f}

        ## INSTRUCCIONES:
        1. Preséntate brevemente como "Mimo el Gatito Fiscal", y tu asesor profesional
        2. Analiza la situación fiscal específica de este contribuyente
        3. IMPORTANTE: Evalúa si ya están maximizadas ciertas deducciones usando los LÍMITES OFICIALES:
           - Si deducciones generales ya son ≥${constantes.valor_uma_anual * constantes.tope_general_deducciones_umas:,.0f} ({constantes.tope_general_deducciones_umas} UMAs), NO recomiendes incrementarlas
           - Si PPR/Afore ya está al máximo ${constantes.valor_uma_anual * constantes.tope_ppr_deducciones_umas:,.0f} ({constantes.tope_ppr_deducciones_umas} UMAs), NO recomiendes más contribuciones
           - Si colegiaturas están en los topes oficiales mostrados arriba, NO recomiendes aumentarlas
           - Usa los valores EXACTOS de UMA y topes oficiales en tus cálculos
        4. Proporciona EXACTAMENTE 5 consejos estratégicos RELEVANTES para AUMENTAR EL SALDO A FAVOR
        5. Cada consejo debe ser ESPECÍFICO, PRÁCTICO y con números basados en su situación
        6. Considera las leyes fiscales mexicanas vigentes para {fiscal_year + 1}
        7. Enfócate en estrategias legales para maximizar deducciones y minimizar impuestos
        
        ## FORMATO DE RESPUESTA:
        IMPORTANTE: Estructura tu respuesta exactamente así:
        
        1. **Saludo gatuno breve según la hora:**
        - Si es mañana (6:00-11:59): "¡Miau-nos días!" o "¡Buenos días! 🐱"
        - Si es tarde (12:00-18:59): "¡Buenas tar-des!" o "¡Buenas tardes! 🐾"
        - Si es noche (19:00-5:59): "¡Buenas no-ches!" o "¡Buenas noches! 😸"
        
        2. **Presentación breve (1 línea):**
        "Soy Mimo el Gatito Fiscal 🐱 y tu asesor profesional, y te daré consejos purr-fectos para aumentar tu saldo a favor:"
        
        3. **Da 4 o 5 consejos numerados** usando toques gatunos sutiles como: "purr-fecto", "gat-rantizo", "es-paw-cialmente", "feli-nanzas", "miau-ravilloso"
        
        Para cada uno de los consejos usa esta estructura:
        ### [número]. **[Título del consejo para aumentar saldo a favor]**
        
        [Explicación de cómo este consejo específicamente AUMENTARÁ su saldo a favor]
        
        > **Cálculo purr-fecto para ti:**
        > [Ejemplo con números exactos de cuánto AUMENTARÍA su saldo a favor con este consejo, basado en sus ${calculation_result.gross_annual_income:,.0f} de ingresos anuales]
        
        ---
        
        ## CONSEJOS ESPECÍFICOS PARA AUMENTAR SALDO A FAVOR:
        ANALIZA PRIMERO LA SITUACIÓN ACTUAL:
        - Deducciones actuales: ${calculation_result.authorized_deductions:,.0f}
        - Límite deducciones generales (15%): ${calculation_result.gross_annual_income * 0.15:,.0f}
        - Límite PPR (10%): ${calculation_result.gross_annual_income * 0.10:,.0f}
        - Límite colegiaturas según nivel educativo.

        SOLO RECOMIENDA ESTRATEGIAS RELEVANTES Y VIABLES:
        - NO recomiendes deducciones generales si ya superan el 15% del ingreso
        - NO recomiendes PPR si ya está al máximo
        - Enfócate en oportunidades reales de mejora
        - Incluye estrategias de planeación fiscal para el próximo ejercicio
        - Sugiere optimización de retenciones específica para su situación
        - Considera inversiones deducibles alternativas
        - Explora gastos médicos especializados no utilizados
        """

    def _process_response(self, response_text: str) -> str:
        """
        Procesa la respuesta de Gemini manteniéndola en formato Markdown
        Principio: Single Responsibility Principle (SRP)
        """
        response_text = response_text.strip()

        if not response_text:
            return "**Error procesando recomendaciones:** No se pudieron procesar las recomendaciones de IA correctamente."

        return response_text


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

    def get_recommendations_stream(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ):
        """
        Obtiene recomendaciones fiscales con streaming usando solo el generador primario

        Args:
            calculation_result: Resultado del cálculo fiscal
            user_data: Datos del contribuyente
            fiscal_year: Año fiscal

        Yields:
            Fragmentos de texto de las recomendaciones en tiempo real
        """
        print("🤖 Generando recomendaciones fiscales personalizadas con streaming...")

        for chunk in self.primary_generator.generate_recommendations_stream(
            calculation_result, user_data, fiscal_year
        ):
            yield chunk

        print("✅ Recomendaciones generadas exitosamente")


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
