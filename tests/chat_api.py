import requests
from requests.auth import HTTPBasicAuth
import json
import time
import os
from dotenv import load_dotenv
from termcolor import colored
from app.utils.get_state_with_labels import get_state_with_labels

load_dotenv("./config/.env", verbose=True)

URL_LOCAL = "http://127.0.0.1:8000"

URL_MAIN = os.getenv("URL_MAIN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN_ENDPOINT = os.getenv("TOKEN_ENDPOINT")

def get_access_token(client_id, client_secret):
    auth = HTTPBasicAuth(client_id, client_secret)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = {"grant_type": "client_credentials"}
    response = requests.post(TOKEN_ENDPOINT, auth=auth, headers=headers, data=body)
    return response.json().get("access_token")

def chat_test():
    """Simulates a chat with the agent
    HOW_TO_RUN: python -m tests.chat_test
    """
    
    url = URL_LOCAL
    state = {}
    history = []
    headers = None
    if url == URL_MAIN:
        token = get_access_token(CLIENT_ID, CLIENT_SECRET)
        headers = {"Authorization": f"Bearer {token}"}
    
    AI_GREETING = "Hello!"
    AI_FIRST_QUERY = "How can I help?"
    
    AI_COLOR = "yellow"
    USER_COLOR = "green"

    print(f"{colored('AI', AI_COLOR)}:\t{AI_GREETING}")
    while True:
        
        if history == []:
            history.append({"role":"ai", "content":AI_FIRST_QUERY})
            print(f"{colored('AI', AI_COLOR)}:\t{AI_FIRST_QUERY}")

        user_input = str(input(f"{colored('User', USER_COLOR)}:\t"))
        print()

        audio_output = "false"

        payload = {
            "user_input": user_input,
            "state": state,
            "history": history,
            "audio_output": audio_output
        }
        start_time = time.time()
        
        response = requests.post(f"{url}/chatbot", json=payload, headers=headers)
        if response.status_code == 401:
            token = get_access_token(CLIENT_ID, CLIENT_SECRET)
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(f"{url}/chatbot", json=payload, headers=headers)
        
        end_time = time.time()
        response_dict = json.loads(response.text)

        #ENDPOINT RESPONSE
        history = response_dict.get("history", [])
        state = response_dict.get("state", {})
        # print(f"""
        #       HISTORY: {history}
        #       """)
        print(f"\n\t{colored('STATE', 'magenta')}:")
        print("\t\t" + get_state_with_labels(state).replace("\n", "\n\t\t"))
        # for k, v in state.items():
        #     if type(v) == dict:
        #          for k2, v2 in v.items():
        #              print(f"\t\t\t{k2}: {v2}")
        #     else:
        #         print(f"\t\t{k}: {v}")
        output_to_user = response_dict.get("output_to_user", "").replace("\n", "\n\t")

        print(f"\n{colored('AI', AI_COLOR)}:\t{output_to_user}")

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(colored(f'\t\t\t---- Elapsed time: {elapsed_time:.2f}s ----\n', 'cyan')) 



if __name__ == "__main__":
    chat_test()
