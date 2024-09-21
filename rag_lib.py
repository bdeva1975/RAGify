import os
import itertools
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_or_create_collection(collection_name):
    embedding_function = OpenAIEmbeddingFunction(api_key=os.environ.get("OPENAI_API_KEY"), model_name="text-embedding-ada-002")
    
    chroma_client = chromadb.Client()
    
    # Try to get the collection if it exists
    try:
        collection = chroma_client.get_collection(name=collection_name, embedding_function=embedding_function)
        print(f"Using existing collection: {collection_name}")
    except ValueError:
        # If the collection doesn't exist, create it
        collection = chroma_client.create_collection(name=collection_name, embedding_function=embedding_function)
        print(f"Created new collection: {collection_name}")
        
        # Sample data to populate the collection
        documents = [
            "OpenAI is an artificial intelligence research laboratory consisting of the for-profit corporation OpenAI LP and its parent company, the non-profit OpenAI Inc.",
            "OpenAI's mission is to ensure that artificial general intelligence benefits all of humanity.",
            "OpenAI has released several models including GPT-3, DALL-E, and ChatGPT.",
            "OpenAI was founded in 2015 by Elon Musk, Sam Altman, and others.",
            "GPT-3, developed by OpenAI, is one of the largest and most powerful language models in the world.",
            "DALL-E is an AI model by OpenAI that can create images from textual descriptions.",
            "ChatGPT is a conversational AI model developed by OpenAI that can engage in human-like dialogue.",
            "OpenAI has been at the forefront of developments in natural language processing and generation."
        ]
        
        collection.add(
            documents=documents,
            ids=[f"doc{i}" for i in range(len(documents))]
        )
    
    return collection

def get_vector_search_results(collection, question):
    results = collection.query(
        query_texts=[question],
        n_results=4
    )
    
    return results

def get_rag_response(question):
    collection = get_or_create_collection("openai_faqs_collection")
    
    search_results = get_vector_search_results(collection, question)
    
    flattened_results_list = search_results['documents'][0]
    
    if not flattened_results_list:
        return "I'm sorry, but I don't have any information to answer this question based on my current knowledge.", []

    rag_content = "\n\n".join(flattened_results_list)
    print("Retrieved content:")
    print(rag_content)
    print("\n" + "-"*50 + "\n")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that answers questions based ONLY on the provided content. If the provided content does not contain information to answer the question, respond with 'I don't have enough information to answer this question.'"},
        {"role": "user", "content": f"Here is the content to use for answering questions:\n\n{rag_content}\n\nBased ONLY on the content above, please answer the following question. If the content does not contain relevant information, say you don't have enough information:\n{question}"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # You can change this to "gpt-4" if you have access
        messages=messages,
        max_tokens=2000,
        temperature=0,
        top_p=0.9,
    )
    
    return response.choices[0].message.content, flattened_results_list

def main():
    print("Welcome to the OpenAI Q&A System!")
    print("You can ask questions about OpenAI, and the system will provide answers based on its knowledge.")
    print("Type 'quit' to exit the program.\n")

    while True:
        question = input("Please enter your question: ")
        
        if question.lower() == 'quit':
            print("Thank you for using the OpenAI Q&A System. Goodbye!")
            break
        
        answer, sources = get_rag_response(question)
        
        print("\nAnswer:")
        print(answer)
        print("\nSources:")
        for source in sources:
            print(f"- {source}")
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()