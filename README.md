# Graph RAG Starter Kit
This repository is prepared for Project Task II, IF4070 Knowledge Representation and Reasoning course (2025-1), STEI-ITB. You can clone it and modify whatever you want for your own domain case.

## How to use
1. (Optional) Make a virtual environment. Command: `py -m venv ./venv`
2. Install required dependencies. Command: `pip install -r requirements.txt`
3. Copy `config_template.toml` to `config.toml`.
4. Modify `config.toml` based on your database configuration.
5. Run RAG system for testing. Command: `py rag.py`
6. Test with one sample question, such as "How many players?".

## Additional configuration
- You may need to change the schema path.
- You may need to set `HF_HOME` environment variable to determine the location of model cache.
  - More information: https://huggingface.co/docs/datasets/cache
- You may need to install other versions of PyTorch to support GPU (and possibly modify the code).
- You may need to change the models for better performance.
- You may need to handle Neo4j exceptions in case the generated Cypher is malformed.

## References
- https://neo4j.com/docs/python-manual/current/
