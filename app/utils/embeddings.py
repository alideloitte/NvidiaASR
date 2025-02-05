
import time

import numpy as np
from numpy.linalg import norm

import openai
from openai import AzureOpenAI

from dotenv import load_dotenv
import os

load_dotenv("config/.env")

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

azure_client = AzureOpenAI(api_key=OPENAI_API_KEY,  
    api_version=OPENAI_API_VERSION, 
    azure_endpoint = AZURE_ENDPOINT)


def embed_text(content, engine='text-embedding-ada-002', max_tokens=8191):
    # Split content into chunks of max_tokens
    chunks = [content[i:i+max_tokens] for i in range(0, len(content), max_tokens)]

    # Iterate through chunks and obtain embeddings
    for chunk in chunks:
        max_retries = 5  # Maximum number of retries
        attempt = 0
        retry_delay = 20  # Initial retry delay in seconds
        chunk = chunk.encode(encoding='utf-8', errors='ignore').decode()
        for attempt in range(max_retries + 1):
            try:
                response = azure_client.embeddings.create(input=chunk, model=engine)
                break
            except openai.RateLimitError as e:
                if attempt < max_retries:
                    print("RateLimit. Retrying. Attempt: "+str(attempt) + ". Delaying " + str(retry_delay) + " seconds.")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponentially increase retry delay
                else:
                    raise e
        vector = response.data[0].embedding

    return vector



def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (norm(v1) * norm(v2))

def euclidean_distance(point1, point2):
    """
    Calculates the Euclidean distance between two points.

    Args:
        point1 (tuple or list): Coordinates of the first point.
        point2 (tuple or list): Coordinates of the second point.

    Returns:
        float: Euclidean distance between the points.
    """
    return np.linalg.norm(np.array(point1) - np.array(point2))

def euclidean_similarity(v1, v2):
    """
    Converts Euclidean distance to a similarity score.

    Args:
        point1 (tuple or list): Coordinates of the first point.
        point2 (tuple or list): Coordinates of the second point.

    Returns:
        float: Similarity score (bounded between 0 and 1).
    """
    distance_value = euclidean_distance(v1, v2)
    return 1 / (1 + distance_value)


def get_best_chunks_by_embeddings(text, data, count, minimum_score = 0):
    vector = embed_text(text)
    scores = []
    embedding_chunks = []
    for i in data:
        score = euclidean_similarity(vector, i['vector'])
        print("SCORE:", score)
        if score > minimum_score:
            scores.append({'content': i['content'], 'score': score})
            ordered = sorted(scores, key=lambda d: d['score'], reverse=True)
            embedding_chunks = [chunk['content'] for chunk in ordered]
    return embedding_chunks[:count]


if __name__ == "__main__":    
    from termcolor import colored

    from tkinter import filedialog
    import json

    file_path = filedialog.askopenfilename(title="Embeddings File", filetypes=[("JSON files", "*.json")])
    with open(file_path, 'r') as infile:
        result = json.load(infile)
    
    user_input = input('User: ')
    chunks = get_best_chunks_by_embeddings(user_input, result, 1, minimum_score=0.6)
    processed_chunks = '\n----\n'.join(chunks)
    user_input = user_input + '\n\n####Take in consideration the following: \n'+processed_chunks
    print(colored("\nFinal User input:", "green") + f"\n{user_input}")
    # conversation = [
        # {'role': 'system', 'content': SYSTEM_PROMPT},
        # {'role': 'user', 'content': firstInput}
    # ]