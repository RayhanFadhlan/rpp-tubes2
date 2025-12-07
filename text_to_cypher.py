from openai import OpenAI
from config import load_config

class TextToCypher:
    def __init__(self, schema: str):
        self._schema = schema

        config = load_config()
        llm_config = config.get_llm_config()

        self._client = OpenAI(
            base_url=llm_config.get("base_url"),
            api_key=llm_config.get("api_key")
        )
        self._model_name = llm_config.get("model", "llama-4-scout")

    def __call__(self, question: str):
        system_prompt = (
            "You are an expert Neo4j developer. "
            "Translate the user's natural language question into a standard Cypher query based on the provided schema. "
            "Do NOT include explanations, markdown formatting, or preamble. "
            "If the user's question is unrelated to the provided schema (Dota 2), or cannot be answered by it, return exactly the word: IRRELEVANT. "
            "Otherwise, return ONLY the raw Cypher query string."
        )

        user_prompt = f"Schema:\n{self._schema}\n\nQuestion: {question}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=0.0,
            max_tokens=256
        )

        generated_text = response.choices[0].message.content.strip()

        if generated_text.startswith("```"):
            generated_text = generated_text.replace("```cypher", "").replace("```", "").strip()

        if "IRRELEVANT" in generated_text:
            return ""

        return generated_text

if __name__ == "__main__":
    schema = "Node: Hero(name)"
    ttc = TextToCypher(schema)
    print(f"Valid Query: {ttc('Who is Anti-Mage?')}")
    print(f"Irrelevant Query: {ttc('How do I bake a cake?')}")
