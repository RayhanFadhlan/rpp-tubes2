from openai import OpenAI
from config import load_config

PROMPT_TEMPLATE = """
<SCHEMA>

Question:
<QUESTION>

Query:
<QUERY>

Query result:
<QUERY-RESULT-STR>

Answer:
""".strip()

class ResponseGenerator:
    def __init__(self, schema: str):
        config = load_config()
        llm_config = config.get_llm_config()

        self._client = OpenAI(
            base_url=llm_config.get("base_url"),
            api_key=llm_config.get("api_key")
        )
        self._model_name = llm_config.get("model", "llama-4-scout")
        self._schema = schema

    def __call__(self, question: str, query: str, query_result_str: str):
        prompt = PROMPT_TEMPLATE
        prompt = prompt.replace("<SCHEMA>", self._schema)
        prompt = prompt.replace("<QUESTION>", question)
        prompt = prompt.replace("<QUERY>", query)
        prompt = prompt.replace("<QUERY-RESULT-STR>", query_result_str)

        messages = [
            {"role": "system", "content": "Answer the user question using the provided Neo4j context. Only response the query result in natural language."},
            {"role": "user", "content": prompt}
        ]

        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            max_tokens=512
        )

        return response.choices[0].message.content
