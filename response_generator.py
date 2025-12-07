from transformers import AutoModelForCausalLM, AutoTokenizer

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
        model_name = "Qwen/Qwen2.5-0.5B-Instruct"
        self._model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype="auto",
            device_map="auto"
        )
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
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
        text = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = (
            self._tokenizer([text], return_tensors="pt")
            .to(self._model.device)
        )
        generated_ids = self._model.generate(
            **model_inputs,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids,
                                             generated_ids)
        ]
        response = self._tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )
        return response[0]

if __name__ == "__main__":
    with open("schema_example.txt") as fp:
        schema = fp.read().strip()

    print("Preparing pipeline ....")
    generator = ResponseGenerator(schema)

    question = "List all players and their levels."
    query = """
MATCH (p:Player)-[:SHARES]->(l:Level)
RETURN p.username AS username, l.name AS level_name
    """.strip()
    query_result_str = """
{'username': 'Galactic71', 'level_name': 'Lanterns Preview'}
{'username': 'Demonmaster197', 'level_name': 'fun adventure'}
{'username': 'Demonmaster197', 'level_name': 'moonlight'}
{'username': 'usnsrDEMON', 'level_name': 'memories'}
    """.strip()

    print("Generating ...")
    response = generator(question, query, query_result_str)
    print(response)
