from database import GraphDatabaseDriver
from response_generator import ResponseGenerator
from text_to_cypher import TextToCypher

with GraphDatabaseDriver() as driver:
    with open("schema_example.txt") as fp:
        schema = fp.read().strip()

    print("Preparing text-to-Cypher pipeline ....")
    ttc = TextToCypher(schema)

    print("Preparing response generator pipeline ....")
    generator = ResponseGenerator(schema)

    interrupt = False
    print("(Interrupt to stop.)")
    while not interrupt:
        try:
            question = input("Question: ")
        except KeyboardInterrupt:
            interrupt = True

        if not interrupt:
            print("Generating Cypher query ....")
            query = ttc(question)
            print(query)

            print("Executing Cypher query ....")
            results = driver.execute_query(query)
            if len(results) > 0:
                query_result_str = "\n".join([
                    str(x) for x in results
                ])
            else:
                query_result_str = "(no result)"
            print(query_result_str)

            print("Generating response ....")
            response = generator(question, query, query_result_str)
            print(response)
    
    print("(Stopped.)")
