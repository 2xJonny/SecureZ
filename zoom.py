import requests
import base64

client_id = 'ExM7FRjvQUG9oYbwmm9UzA'
client_secret = 'Tnm0QQf45ZAR2E8A6deJx69W0LTsGhM8'
auth_url = 'https://zoom.us/oauth/token'

def get_access_token(client_id, client_secret):
    auth_string = f'{client_id}:{client_secret}'
    encoded_auth_string = base64.b64encode(auth_string.encode()).decode()
    headers = {
        'Authorization': 'Basic ' + encoded_auth_string,
        'Host': 'zoom.us'
    }
    data = {
        'grant_type': 'account_credentials',
        'account_id': 'Gv5scKHoSxWMgcFye2DtYg'
    }
    response = requests.post(auth_url, headers=headers, data=data)
    print("response: ")
    print(response.json())
    return response.json()['access_token']

access_token = get_access_token(client_id, client_secret)


def add_participant_to_meeting(meeting_id, first_name, last_name, email):
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }
    data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email
    }
    response = requests.post(f'https://api.zoom.us/v2/meetings/{meeting_id}/registrants', headers=headers, json=data)
    print("response:")
    print(response.json())
    print("Participant added to meeting")

add_participant_to_meeting("81866150394", "Jason", "Testing2", "j.steinberg702@gmail.com")