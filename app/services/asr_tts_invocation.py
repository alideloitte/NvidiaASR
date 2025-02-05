import requests

def call_asr_endpoint(api_endpoint, file_name, request_file):
    files = [("audio_file", (file_name, request_file))]
    print("file will be sent to ec2")
    response = requests.post(api_endpoint, files=files)
    print("response: ", response)
    print("response text: ", response.text)

    if response.status_code == 200:
        return response.text.strip('"')
    else:
        return "Error in POST Request"
    

def call_tts_endpoint(api_endpoint, text):
    payload = {"text": text}
    print("Calling TTS Endpoint for text:\n", text)
    response = requests.post(api_endpoint, json=payload)
    print("response: ", response)
    print("response content: ", response.content)

    if response.status_code == 200:
        return response.content
    else:
        return "Error in POST Request"