from typing import Protocol, Generator, Any
from collections import Counter

from dotenv import load_dotenv
from litellm import completion
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


# --- 1. Abstractions (Interfaces) ---
class LanguageModel(Protocol):
    """Defines the interface for a language model provider. (DIP)"""

    def generate(
        self,
        messages: list[
            ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam
        ],
    ) -> Generator[str, None, None]:
        """Generates a response, yielding chunks as they arrive."""
        ...


class Bot(Protocol):
    """Defines the interface for any bot in the conversation. (ISP)"""

    name: str

    def generate_response(
        self, conversation_history: str, other_bots: list["Bot"], topic_text: str
    ) -> str: ...

    def generate_custom_response(
        self,
        conversation_history: str,
        other_bots: list["Bot"],
        topic_text: str,
        custom_prompt: str,
    ) -> str: ...


# --- 2. Concrete Implementations ---
class LiteLLMModel:
    """
    Concrete implementation of LanguageModel using 'litellm'.
    Its single responsibility is to call the LLM API. (SRP)
    """

    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(
        self,
        messages: list[
            ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam
        ],
    ):
        """Generates a response by streaming chunks as they arrive."""
        try:
            response = completion(
                model=self.model_name,
                messages=messages,
                stream=True,
            )
            for chunk in response:
                if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield delta.content
        except Exception as e:
            print(f"\n❌ Error calling model {self.model_name}: {e}")
            yield "(No se pudo generar una respuesta debido a un error.)"


class PersonalityBot:
    """
    Represents a bot with a specific personality, responsible for crafting prompts.
    Depends on the LanguageModel abstraction. (SRP & DIP)
    """

    def __init__(
        self,
        name: str,
        model: LanguageModel,
        system_prompt_template: str,
    ):
        self.name = name
        self.model = model
        self.system_prompt_template = system_prompt_template

    def _prepare_messages(
        self,
        conversation_history: str,
        other_bots: list[Bot],
        topic_text: str,
        user_prompt_override: str | None = None,
    ) -> list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam]:
        """Prepares messages, allowing for a custom user prompt."""
        other_names = ", ".join([bot.name for bot in other_bots])
        formatted_system_prompt = self.system_prompt_template.format(
            self_name=self.name, other_names=other_names
        )
        system_message = ChatCompletionSystemMessageParam(
            role="system", content=formatted_system_prompt
        )

        if user_prompt_override:
            user_prompt = user_prompt_override
        else:
            user_prompt = f"""
            Eres {self.name}, en una conversación con {other_names}.
            Todos están analizando el siguiente documento sobre un sistema de IA para el juego "Turbo Mines".

            --- INICIO DEL DOCUMENTO ---
            {topic_text}
            --- FIN DEL DOCUMENTO ---

            La conversación hasta ahora:
            {conversation_history}

            Ahora, proporciona tu análisis experto basado en tu personalidad y experiencia específica.
            """

        user_message = ChatCompletionUserMessageParam(role="user", content=user_prompt)
        return [system_message, user_message]

    def generate_response(
        self, conversation_history: str, other_bots: list[Bot], topic_text: str
    ) -> str:
        """Generates a standard debate response with streaming display."""
        messages = self._prepare_messages(conversation_history, other_bots, topic_text)

        print(f"== {self.name.upper()}: ", end="", flush=True)
        full_response = []
        for chunk in self.model.generate(messages):
            print(chunk, end="", flush=True)
            full_response.append(chunk)
        print()  # Nueva línea al terminar

        return "".join(full_response)

    def generate_custom_response(
        self,
        conversation_history: str,
        other_bots: list[Bot],
        topic_text: str,
        custom_prompt: str,
    ) -> str:
        """Generates a response for a specific, one-off task like voting with streaming."""
        messages = self._prepare_messages(
            conversation_history, other_bots, topic_text, custom_prompt
        )

        print(f"== {self.name.upper()}: ", end="", flush=True)
        full_response = []
        for chunk in self.model.generate(messages):
            print(chunk, end="", flush=True)
            full_response.append(chunk)
        print()  # Nueva línea al terminar

        return "".join(full_response)


# --- 3. Conversation Orchestration ---
class Conversation:
    """Manages the history and state of the conversation."""

    def __init__(self, bots: list[Bot], topic_text: str):
        self.bots = bots
        self.topic_text = topic_text
        self.history: str = "La conversación acaba de comenzar."

    def run_turn(self, bot: Bot):
        """Runs a standard debate turn for a bot."""
        other_bots = [b for b in self.bots if b.name != bot.name]
        response = bot.generate_response(self.history, other_bots, self.topic_text)
        self.history += f"\n{bot.name}: {response}"

    def run_custom_turn(self, bot: Bot, custom_prompt: str) -> str:
        """Runs a turn with a custom prompt and returns the response."""
        other_bots = [b for b in self.bots if b.name != bot.name]
        response = bot.generate_custom_response(
            self.history, other_bots, self.topic_text, custom_prompt
        )
        return response


class ConversationController:
    """Orchestrates the entire multi-round conversation including special phases."""

    def __init__(self, expert_bots: list[Bot], moderator_bot: Bot, topic_text: str):
        self.expert_bots = expert_bots
        self.moderator_bot = moderator_bot
        self.topic_text = topic_text
        self.main_conversation = Conversation(expert_bots, topic_text)
        self.moderator_conversation = Conversation(
            [moderator_bot] + expert_bots, topic_text
        )

    def run_simulation(self, total_rounds: int, voting_interval: int):
        """Runs the full debate simulation with all phases."""
        self._start_introduction()

        for i in range(total_rounds):
            round_num = i + 1
            print(f"\n-- RONDA {round_num}/{total_rounds} --\n")

            for bot in self.expert_bots:
                self.main_conversation.run_turn(bot)

            self._run_moderator_summary()

            if round_num % voting_interval == 0 and round_num < total_rounds:
                self._run_voting_phase()
                self._run_adjustment_phase()

        self._end_simulation()

    def _start_introduction(self):
        print("✅ Tema cargado. Iniciando conversación...")
        print("\n-- INTRODUCCIÓN --")
        self.moderator_conversation.run_turn(self.moderator_bot)
        self.main_conversation.history = self.moderator_conversation.history

    def _run_moderator_summary(self):
        print("\n-- RESUMEN DEL MODERADOR --")
        self.moderator_conversation.history = self.main_conversation.history
        self.moderator_conversation.run_turn(self.moderator_bot)
        self.main_conversation.history = self.moderator_conversation.history

    def _run_voting_phase(self):
        print("\n-- FASE DE VOTACIÓN --")
        self.moderator_conversation.run_custom_turn(
            self.moderator_bot,
            "Ha llegado el momento de votar. Expertos, por favor indiquen cuál teoría de sus colegas les parece más convincente hasta ahora. Pueden votar por ustedes mismos.",
        )

        bot_names = [bot.name for bot in self.expert_bots]
        votes = []
        for bot in self.expert_bots:
            prompt = f"""
            Basándote en la discusión, ¿cuál argumento es el más sólido?
            Elige un nombre de esta lista: {", ".join(bot_names)}.
            Responde SOLO con el nombre.
            """
            vote = self.main_conversation.run_custom_turn(bot, prompt)
            # Limpiamos el voto para que coincida con un nombre
            cleaned_vote = next((name for name in bot_names if name in vote), None)
            if cleaned_vote:
                votes.append(cleaned_vote)

        vote_counts = Counter(votes)
        winner = vote_counts.most_common(1)[0][0] if vote_counts else "Nadie"

        self.moderator_conversation.run_custom_turn(
            self.moderator_bot,
            f"Los votos están contabilizados. Con {vote_counts.most_common(1)[0][1]} voto(s), la teoría predominante actual es de {winner}. Los resultados completos fueron: {vote_counts}",
        )
        self.main_conversation.history = self.moderator_conversation.history

    def _run_adjustment_phase(self):
        print("\n-- FASE DE AJUSTE --")
        self.moderator_conversation.run_custom_turn(
            self.moderator_bot,
            "Dados los resultados de la votación, ¿desean ajustar o reforzar su postura actual? Expresen brevemente su posición.",
        )
        self.main_conversation.history = self.moderator_conversation.history

        for bot in self.expert_bots:
            self.main_conversation.run_turn(bot)

    def _end_simulation(self):
        print("\n-- CONCLUSIÓN FINAL --")
        self.moderator_conversation.run_custom_turn(
            self.moderator_bot,
            "El debate ha concluido. Por favor proporcionen un resumen final y completo de toda la discusión y su evolución.",
        )


def read_topic_from_file(filepath: str) -> str:
    """Reads the conversation topic from a markdown file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: Topic file not found at '{filepath}'")
        return ""


def main() -> None:
    """Initializes bots and runs the conversation simulation."""
    topic_file = "conversation_topic.md"
    topic_text = read_topic_from_file(topic_file)
    if not topic_text:
        return

    gpt_model = LiteLLMModel(model_name="xai/grok-4")
    claude_model = LiteLLMModel(model_name="anthropic/claude-sonnet-4-5")
    gemini_model = LiteLLMModel(model_name="gemini/gemini-2.5-pro")
    flash_model = LiteLLMModel(model_name="openai/gpt-4o-mini")

    expert_bots: list[Bot] = [
        PersonalityBot(
            name="Dra. Anya Sharma",
            model=gpt_model,
            system_prompt_template="""
                Eres la Dra. Anya Sharma, una experta cautelosa y meticulosa en probabilidad y estadística.
                Tu análisis debe estar basado en datos. Eres escéptica de afirmaciones sin pruebas estadísticas.
                Te enfocas en puntajes de confianza, análisis de datos históricos y la validez del modelo predictivo.
                Estás en una conversación con {other_names}.
            """,
        ),
        PersonalityBot(
            name="Leo 'Vegas' Vance",
            model=claude_model,
            system_prompt_template="""
                Eres Leo 'Vegas' Vance, un teórico de juegos astuto y pragmático, experto en casinos.
                Ves todo como un riesgo calculado. Te enfocas en la estrategia del
                jugador, riesgo vs. recompensa, y en explotar las reglas del sistema.
                Eres práctico y te importa el camino óptimo para ganar.
                Estás en una conversación con {other_names}.
            """,
        ),
        PersonalityBot(
            name="Marco Chen",
            model=gemini_model,
            system_prompt_template="""
                Eres Marco Chen, un arquitecto de sistemas e ingeniero de software.
                Te enfocas en la implementación técnica, escalabilidad y viabilidad de la arquitectura propuesta.
                Analizas flujos de datos, interacciones de componentes y posibles cuellos de botella del sistema.
                Estás en una conversación con {other_names}.
            """,
        ),
        PersonalityBot(
            name="Isabelle Moreau",
            model=flash_model,
            system_prompt_template="""
                Eres Isabelle Moreau, una especialista en Interacción Humano-Computadora (HCI) y experiencia de usuario (UX).
                Te preocupa cómo el usuario interactuará con el sistema.
                Te enfocas en el overlay, tiempos de respuesta, carga cognitiva y cómo las recomendaciones de la IA afectan el comportamiento y confianza del jugador.
                Estás en una conversación con {other_names}.
            """,
        ),
    ]

    moderator_bot = PersonalityBot(
        name="Moderador",
        model=flash_model,
        system_prompt_template="""
            Eres un moderador de reuniones neutral y eficiente. Tus tareas son:
            1. Presentar brevemente el tema al inicio.
            2. Al final de cada ronda, proporcionar un resumen conciso de una oración con los puntos clave.
            3. Anunciar las fases de votación y los resultados claramente.
            4. Guiar la discusión de ajuste post-votación.
            Estás moderando una discusión entre {other_names}.
            Mantén tus intervenciones breves y al punto.
        """,
    )

    # --- Run Conversation ---
    controller = ConversationController(expert_bots, moderator_bot, topic_text)
    controller.run_simulation(total_rounds=9, voting_interval=3)


if __name__ == "__main__":
    load_dotenv()
    main()
