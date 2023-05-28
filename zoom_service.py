import requests
import base64

class ZoomService:
    # TODO: PULL FROM DYNAMICALLY FIREBASE DEPENDING ON CLIENT

    auth_url = 'https://zoom.us/oauth/token'


    def __init__(self, client_id, client_secret, account_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.account_id = account_id
        self.access_token = self.get_access_token(self.client_id, self.client_secret)


    def get_access_token(self, client_id, client_secret):
        auth_string = f'{client_id}:{client_secret}'
        encoded_auth_string = base64.b64encode(auth_string.encode()).decode()
        headers = {
            'Authorization': 'Basic ' + encoded_auth_string,
            'Host': 'zoom.us'
        }
        data = {
            'grant_type': 'account_credentials',
            'account_id': self.account_id
        }
        response = requests.post(self.auth_url, headers=headers, data=data)
        print("response: ")
        print(response.json())
        return response.json()['access_token']
    
    def get_registrant_id(self, meeting_id, email):
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/json'
        }

        url = f'https://api.zoom.us/v2/meetings/{meeting_id}/registrants'

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            registrants = response.json().get('registrants')
            for registrant in registrants:
                if registrant.get('email') == email:
                    return registrant.get('id')
        else:
            print(f"Failed to retrieve registrants. Response: {response.status_code} {response.text}")
        return None

    def add_participant_to_meeting(self, meeting_id, first_name, last_name, email):
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
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

    def remove_participant_from_meeting(self, meeting_id, email):
            registrant_id = self.get_registrant_id(meeting_id, email)

            print("Attempting to remove participant from meeting...")
            headers = {
                'Authorization': 'Bearer ' + self.access_token,
                'Content-Type': 'application/json'
            }

            url = f'https://api.zoom.us/v2/meetings/{meeting_id}/registrants/{registrant_id}'

            response = requests.delete(url, headers=headers)
            
            print(response)
            if response.status_code == 204:
                print(f"Participant with registrant ID {registrant_id} removed from meeting")
            else:
                print(f"Failed to remove participant. Response: {response.status_code} {response.text}")

    def change_participant_email(self, meeting_id, old_email, new_email, first_name, last_name):
        self.remove_participant_from_meeting(meeting_id, old_email)
        self.add_participant_to_meeting(meeting_id, first_name, last_name, new_email)



# zoomService = ZoomService(zoom_client_id, zoom_client_secret)

# meeting_id = "81866150394"
# email = "hockeydudej46@gmail.com"

# Test 1
# zoomService.add_participant_to_meeting(meeting_id, "jsteinberg7", "-", email)

# Test 2
# zoomService.remove_participant_from_meeting(meeting_id, email)

# # Test 3
# zoomService.change_participant_email(meeting_id, "j.steinberg702@gmail.com", "hockeydudej46@gmail.com", "Jason", "Steinberg")


