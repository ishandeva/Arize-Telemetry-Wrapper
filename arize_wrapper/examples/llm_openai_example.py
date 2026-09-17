"""End-to-end OpenAI + Arize AX example.

Install:
  pip install "arize-telemetry-wrapper[llm]" openai \
      openinference-instrumentation-openai

Set the ARIZE_* values from .env.example and OPENAI_API_KEY, then run this
file. A successful response means the wrapper finished its span; inspect the
configured Arize project for the submitted trace and required attributes.
"""

from openai import OpenAI
from openinference.instrumentation.openai import OpenAIInstrumentor

from arize_wrapper import ArizeConfig, configure_default_logging
from arize_wrapper.llm import initialize_llm

configure_default_logging()
telemetry = initialize_llm(ArizeConfig.from_env())

# Register after initialize_llm so provider spans share the configured Arize
# tracer provider. The provider instrumentor captures messages/tokens; the
# wrapper supplies organizational metadata and prompt-template standards.
OpenAIInstrumentor().instrument(tracer_provider=telemetry.tracer_provider)
client = OpenAI()


@telemetry.llm(
    prompt_template="Answer the customer question clearly: {question}",
    prompt_template_version="2026-09-17",
    temperature=0.2,
    span_name="support.answer_question",
)
def answer_question(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=[{"role": "user", "content": question}],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


if __name__ == "__main__":
    print(answer_question("How can I reset my password?"))
