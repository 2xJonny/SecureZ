import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase import firebase
from dotenv import load_dotenv
import os

load_dotenv()

dbURL = os.environ.get("REALTIME_FB_URL")

serviceAccountInfo = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(serviceAccountInfo)

dbService = firestore.client()

firebase = firebase.FirebaseApplication(dbURL, None)

def get_client_file_as_obj(discordServerID):

	clientFile = dbService.collection("clientData").document(discordServerID).get()
	clientDict = clientFile.to_dict()

	ownerEmail = list(clientDict["Owner"])[0]
	ownerName = clientDict["Owner"][ownerEmail]

	accountID = clientDict["AccountID"]

	clientSecret = clientDict["ClientSecret"]
	clientID = clientDict["ClientID"]

	zoomMeetings = clientDict["ZoomMeetings"]

	clientObj = Client(ownerEmail, ownerName, accountID, clientID, clientSecret, zoomMeetings, discordServerID)

	return clientObj

def get_meeting_file_as_obj(meetingID):

	meetingFile = dbService.collection("clientRegistrants").document(meetingID).get()
	meetingDict = meetingFile.to_dict()

	registrants = meetingDict["Registrants"]

	acceptedRoles = meetingDict["AcceptedRoles"]

	meetingObj = Meeting(acceptedRoles, registrants, meetingID)

	return meetingObj

def update_cloud_client_file(discordServerID, clientObject):

	dbService.collection("clientData").document(discordServerID).update({
		'Owner': {clientObject.ownerEmail: clientObject.ownerName}, 
		'ZoomMeetings': clientObject.zoomMeetings
	})


def update_cloud_meeting_file(meetingID, meetingObj):

	dbService.collection("clientRegistrants").document(meetingID).update({
		'AcceptedRoles': meetingObj.acceptedRoles, 
		'Registrants': meetingObj.registrants
	})
	

class Client:

	def __init__(self, ownerEmail, ownerName, accountID, clientID, clientSecret, zoomMeetings, discordServerID):
		self.ownerEmail = ownerEmail
		self.ownerName = ownerName
		self.accountID = accountID
		self.clientID = clientID
		self.clientSecret = clientSecret
		self.zoomMeetings = zoomMeetings
		self.discordServerID = discordServerID

	def add_meeting_role(self, meetingID, newRoleID):

		try:
			roleIDs = self.zoomMeetings[meetingID]
			roleIDs.append(newRoleID)

			self.zoomMeetings[meetingID] = list(roleIDs)

			meetingObj = get_meeting_file_as_obj(meetingID)
			meetingObj.acceptedRoles = list(roleIDs)

			update_cloud_client_file(self.discordServerID, self)
			update_cloud_meeting_file(meetingID, meetingObj)

		except:

			print("Failed")

	def delete_meeting_role(self, meetingID, roleID):

		try: 

			self.zoomMeetings[meetingID].remove(roleID)

			meetingObj = get_meeting_file_as_obj(meetingID)
			meetingObj.acceptedRoles.remove(roleID)

			meetingObj.remove_individuals_based_roleID(roleID)

			update_cloud_client_file(self.discordServerID, self)
			update_cloud_meeting_file(meetingID, meetingObj)

		
		except:
			print("Invlalid RoleID to remove")

class Meeting:

	def __init__(self, acceptedRoles, registrants, meetingID):
		self.acceptedRoles = acceptedRoles
		self.registrants = registrants
		self.meetingID = meetingID

	def add_registrant(self, email, firstName, roleID):
		self.registrants[email] = [firstName, roleID]

		update_cloud_meeting_file(self.meetingID, self)

	def remove_individual_registrant(self, email):
		del self.registrants[email]

		update_cloud_meeting_file(self.meetingID, self)


	def remove_individuals_based_roleID(self, roleID):

		registrantsToDelete = []

		for registrant in self.registrants:
			if self.registrants[registrant][1] == roleID:
				registrantsToDelete.append(registrant)


		for registrantToDelete in registrantsToDelete:
			print(registrantToDelete)
			self.remove_individual_registrant(registrantToDelete)

		update_cloud_meeting_file(self.meetingID, self)

	def get_registrants(self):
		return self.registrants

	def change_email(self, email, newEmail):
		listOfRegistrantInfo = self.registrants[email]
		del self.registrants[email]
		self.registrants[newEmail] = listOfRegistrantInfo
		update_cloud_meeting_file(self.meetingID, self)

	def change_role(self, newRoleID, email):
		listToReAssign = self.registrants[email]
		listToReAssign[1] = newRoleID
		self.registrants[email] = listToReAssign
		update_cloud_meeting_file(self.meetingID, self)







		

