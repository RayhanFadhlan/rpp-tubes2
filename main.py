from database import GraphDatabaseDriver
from response_generator import ResponseGenerator
from text_to_cypher import TextToCypher

from colorama import init, Fore, Style

init(autoreset=True)

with GraphDatabaseDriver() as driver:
    with open("schema_example.txt") as fp:
        schema = fp.read().strip()

    print(Fore.YELLOW + "Preparing text-to-Cypher pipeline ....")
    ttc = TextToCypher(schema)

    print(Fore.YELLOW + "Preparing response generator pipeline ....")
    generator = ResponseGenerator(schema)

    interrupt = False
    print(Fore.CYAN + "(Interrupt to stop.)")
    while not interrupt:
        try:
            print(Fore.GREEN + Style.BRIGHT, end="")
            question = input("Question: ")
            print(Style.RESET_ALL, end="")
        except KeyboardInterrupt:
            interrupt = True
            print() # Newline after interrupt

        if not interrupt:
            print(Fore.YELLOW + "Generating Cypher query ....")
            query = ttc(question)
            print(Fore.MAGENTA + f"Cypher Query:\n{query}")

            if not query or query=="":
                print(Fore.RED + "Question is irrelevant to the database context.")
                continue

            print(Fore.YELLOW + "Executing Cypher query ....")
            results = driver.execute_query(query)

            if len(results) > 0:
                query_result_str = "\n".join([
                    str(x) for x in results
                ])
            else:
                query_result_str = "(no result)"

            print(Fore.BLUE + f"Database Result:\n{query_result_str}")

            print(Fore.YELLOW + "Generating response ....")
            response = generator(question, query, query_result_str)
            print(Fore.WHITE + Style.BRIGHT + f"Answer:\n{response}")
            # Add a separator
            print("-" * 50)

    print(Fore.RED + "(Stopped.)")
