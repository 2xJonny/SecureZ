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

	def get_meeting_ids_and_roles(self):
		return self.zoomMeetings


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

	def add_registrant(self, discord_member_ID, email, firstName, roleID):
		self.registrants[discord_member_ID] = [email, firstName, roleID]

		update_cloud_meeting_file(self.meetingID, self)

	def remove_individual_registrant(self, discord_member_ID):
		del self.registrants[discord_member_ID]

		update_cloud_meeting_file(self.meetingID, self)


	def remove_individuals_based_roleID(self, roleID):

		registrantsToDelete = []

		for discord_ID in self.registrants:
			if self.registrants[discord_ID][2] == roleID:
				registrantsToDelete.append(discord_ID)


		for registrantToDelete in registrantsToDelete:
			self.remove_individual_registrant(registrantToDelete)

		update_cloud_meeting_file(self.meetingID, self)

	def get_registrants(self):
		return self.registrants

	def change_email(self, discord_member_ID, newEmail):
		listOfRegistrantInfo = self.registrants[discord_member_ID]
		listOfRegistrantInfo[0] = newEmail
		self.registrants[discord_member_ID] = listOfRegistrantInfo
		update_cloud_meeting_file(self.meetingID, self)

	def change_role(self, newRoleID, discord_member_ID):
		listToReAssign = self.registrants[discord_member_ID]
		listToReAssign[2] = newRoleID
		self.registrants[discord_member_ID] = listToReAssign
		update_cloud_meeting_file(self.meetingID, self)

	def get_registrant(self, discord_id):
		return self.registrants[discord_id]

	def get_registrant_email(self, discord_id):
		return self.registrants[discord_id][0]

	def delete_registrant(self, discord_id):
		del self.registrants[discord_id]
		update_cloud_meeting_file(self.meetingID, self)









