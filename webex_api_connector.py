# Copyright (c) 2023 Cisco and/or its affiliates.

# This software is licensed to you under the terms of the Cisco Sample
# Code License, Version 1.1 (the "License"). You may obtain a copy of the
# License at

#                https://developer.cisco.com/docs/licenses

# All use of the material herein must be in accordance with the terms of
# the License. All rights not expressly granted by the License are
# reserved. Unless required by applicable law or agreed to separately in
# writing, software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.

import requests
import json
import time
from dotenv import load_dotenv
import os

load_dotenv()


class Webex_API_Connector():

    def __init__(self, token, expires_at):
        '''
        Initialize a Webex Connector object
        '''
        
        self.user_token = token
        self.token_expires_at = expires_at
        self.base_url = "https://webexapis.com/v1"
        self.user_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' +  self.user_token
            }
        self.device_tag=os.environ['TAG'] 


    @staticmethod
    def is_token_valid(expires_at):
        '''
        Returns if the token is valid or expired
        '''
        return expires_at != None and time.time() < expires_at


    def create_meetings(self, title, start_date, end_date, legal_external_persons_email, legal_external_persons_display_name, host_email, device_email, device_display_name):
        '''
        Creates a meetings with the Webex Rest API.
        See also: https://developer.webex.com/docs/api/v1/meetings/create-a-meeting
        '''
        
        method = "POST"
        url = self.base_url +"/meetings"
        
        payload = {}
        invitee1 = {}
        invitee2 = {}
        payload['title'] = title
        payload['start'] = start_date
        payload['end'] = end_date
        payload['allowAnyUserToBeCoHost'] = True
        payload['enabledJoinBeforeHost'] = False
        payload['unlockedMeetingJoinSecurity'] = "blockFromJoin" 
        payload['publicMeeting'] = False
        invitee1['email'] = device_email
        invitee1['displayName'] = device_display_name
        invitee1['panelist'] = False
        invitee2['email'] = legal_external_persons_email
        invitee2['displayName'] = legal_external_persons_display_name
        invitee2['panelist'] = False
        payload['invitees'] = [invitee1, invitee2]
        payload['sendEmail'] = True #MUST be True otherwise workspace will not book meeting
        payload['hostEmail'] = host_email
        payload['timezone'] = "Europe/Berlin"
        
        response = self.execute_rest_call(method, url, payload)

        return response


    def get_own_details(self):
        '''
        Get own Webex person details
        See also: https://developer.webex.com/docs/api/v1/people/get-my-own-details
        '''
        
        method = "GET"
        url = self.base_url + "/people/me"
        
        response = self.execute_rest_call(method, url)
        
        return response


    def get_tagged_devices(self):
        '''
        Retrieves all Webex device with a specific tag identify phonebook devices.
        See: https://developer.webex.com/docs/api/v1/devices/list-devices
        '''

        method="GET"
        url = self.base_url + f"/devices?tag={self.device_tag}"

        response = self.execute_rest_call(method, url)

        return response['items']

    
    
    def get_workspaces(self):
        '''
        Retrieves all Webex workspaces.
        See: https://developer.webex.com/docs/api/v1/workspaces/list-workspaces
        '''

        method="GET"
        url = self.base_url + f"/workspaces"

        response = self.execute_rest_call(method, url)

        return response['items']


    def get_workspace_locations(self):
        '''
        Retrieves all Webex workspace locations.
        See: https://developer.webex.com/docs/api/v1/workspace-locations/list-workspace-locations
        '''

        method="GET"
        url = self.base_url + f"/workspaceLocations"

        response = self.execute_rest_call(method, url)


        return response['items']


    def get_booking_list_xapi(self, device_id):
        '''
        Retrieves all bookings for a specific device. 
        See: https://roomos.cisco.com/xapi/Command.Bookings.List/?search=bookings
        And: https://developer.webex.com/docs/api/v1/xapi/execute-command 
        '''

        method = "POST"
        url = self.base_url + "/xapi/command/Bookings.List"

        payload = {
        "deviceId": device_id,
        "arguments": {
            "DayOffset": 0, 
            "Days": 365
        }
        }
        
        response = self.execute_rest_call(method, url, payload)
        
        return response


    def execute_rest_call(self, method, url, payload={}):
        '''
        Execute a Rest API call based on the given method, url and payload. Return response json.
        '''

        response = requests.request(method, url, headers=self.user_headers, data=json.dumps(payload))

        print(f"Status Code for {url}: {response.status_code}")

        if response.status_code != 200:
            raise Exception(response.json())
        else:
            return response.json()