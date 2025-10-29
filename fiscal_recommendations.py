#!/usr/bin/env python3
"""
Módulo para generar recomendaciones fiscales usando IA
Sigue los principios SOLID para mantener código limpio y extensible
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Generator
import google.generativeai as genai


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

        return f"""
        Eres "Gatito Fiscal" 🐱, un gato profesional asesor fiscal mexicano especializado en optimización fiscal para personas físicas. 
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

        ## INSTRUCCIONES:
        1. Preséntate brevemente como "Gatito Fiscal", tu asesor profesional
        2. Analiza la situación fiscal específica de este contribuyente
        3. Proporciona EXACTAMENTE 5 consejos estratégicos para AUMENTAR EL SALDO A FAVOR
        4. Cada consejo debe ser ESPECÍFICO, PRÁCTICO y con números basados en su situación
        5. Considera las leyes fiscales mexicanas vigentes para {fiscal_year + 1}
        6. Enfócate en estrategias legales para maximizar deducciones y minimizar impuestos
        
        ## FORMATO DE RESPUESTA:
        IMPORTANTE: Estructura tu respuesta exactamente así:
        
        1. **Saludo gatuno breve según la hora:**
        - Si es mañana (6:00-11:59): "¡Miau-nos días!" o "¡Buenos días! 🐱"
        - Si es tarde (12:00-18:59): "¡Buenas tar-des!" o "¡Buenas tardes! 🐾"
        - Si es noche (19:00-5:59): "¡Buenas no-ches!" o "¡Buenas noches! 😸"
        
        2. **Presentación breve (1 línea):**
        "Soy Gatito Fiscal 🐱, tu asesor profesional, y te daré 5 consejos purr-fectos para aumentar tu saldo a favor:"
        
        3. **Exactamente 5 consejos numerados** usando toques gatunos sutiles como: "purr-fecto", "gat-rantizo", "es-paw-cialmente", "feli-nanzas", "miau-ravilloso"
        
        Para cada uno de los 5 consejos usa esta estructura:
        ### [número]. **[Título del consejo para aumentar saldo a favor]**
        
        [Explicación de cómo este consejo específicamente AUMENTARÁ su saldo a favor]
        
        > **Cálculo purr-fecto para ti:**
        > [Ejemplo con números exactos de cuánto AUMENTARÍA su saldo a favor con este consejo, basado en sus ${calculation_result.gross_annual_income:,.0f} de ingresos anuales]
        
        ---
        
        """

        # ## CONSEJOS ESPECÍFICOS PARA AUMENTAR SALDO A FAVOR:
        # - **Deducciones generales:** Mostrar cuánto saldo adicional obtendría maximizando deducciones (límite 15% = ${calculation_result.gross_annual_income * 0.15:,.0f})
        # - **PPR/Afore:** Calcular saldo extra con contribuciones adicionales (límite 10% ingresos o 5 UMAs)
        # - **Colegiaturas:** Saldo adicional aprovechando topes educativos máximos
        # - **Planeación fiscal:** Estrategias específicas para el próximo ejercicio
        # - **Optimización de retenciones:** Cómo ajustar para mayor saldo a favor

    def _process_response(self, response_text: str) -> str:
        """
        Procesa la respuesta de Gemini manteniéndola en formato Markdown
        Principio: Single Responsibility Principle (SRP)
        """
        # Limpiar la respuesta
        response_text = response_text.strip()

        # Si no hay contenido, devolver mensaje de error
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
