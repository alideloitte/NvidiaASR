import requests
import time

payload = {
            "text": "texto a ser falado"
        }

url = "http://127.0.0.1:8000"

start_time = time.time()
response = requests.post(f"{url}/tts", json=payload)
end_time = time.time()
response_time = end_time-start_time
print("response: ", response)
print("time: ", response_time)