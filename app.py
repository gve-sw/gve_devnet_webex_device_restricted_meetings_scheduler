''' Copyright (c) 2023 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
'''

from flask import Flask, render_template, request, redirect, session, url_for
from requests_oauthlib import OAuth2Session

from webex_api_connector import Webex_API_Connector
from settings import external_persons

from dotenv import load_dotenv
import os
import json
import time

app = Flask(__name__)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.secret_key = os.urandom(24)

load_dotenv()


@app.route("/")
@app.route('/?logout=<logout>',  methods=["GET"])
def login():
    '''Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e. Webex Teams)
    using a URL with a few key OAuth parameters.
    '''

    logout_old_session = request.args.get('logout')
    
    if logout_old_session:
        prompt = "select_account"
    else:
        prompt = None

    teams = OAuth2Session(CLIENT_ID, scope=SCOPE, redirect_uri=REDIRECT_URI)
    authorization_url, state = teams.authorization_url(AUTHORIZATION_BASE_URL, prompt=prompt)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state

    print("Step 1: User Authorization. Session state:", state)

    return redirect(authorization_url)


# Step 2: User authorization, this happens on the provider.
@app.route("/callback", methods=["GET"])
def callback():
    '''
    Step 2: Retrieving an access token.
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    '''

    try:
        auth_code = OAuth2Session(CLIENT_ID, state=session['oauth_state'], redirect_uri=REDIRECT_URI)
        token = auth_code.fetch_token(AUTH_TOKEN_URL, client_secret=CLIENT_SECRET,
                                    authorization_response=request.url)

        '''
        At this point you can fetch protected resources but lets save
        the token and show how this is done from a persisted token
        '''

        session['oauth_token'] = token

        print("Step 2: Retrieving an access token.")

    except Exception as e:
        print(e)
        return redirect(url_for('login'))
    
    return redirect(url_for('.started'))


@app.route("/started", methods=["GET"])
def started():
    
    try:
        teams_token = session['oauth_token']
        
        print("Step 3: Set token")

        session['token'] = teams_token['access_token']
        session['expires_at']  = teams_token['expires_at']

        webex_api_connector = Webex_API_Connector(session['token'], session['expires_at'])
        session['me'] = webex_api_connector.get_own_details()
    
    except Exception as e:
        print(e)
        return redirect(url_for('login'))

    return redirect(url_for('meeting'))


@app.route("/meeting", methods=["GET","POST"])
def meeting():

    token = session.get("token", None)
    expires_at = session.get("expires_at", None)
    host_data = session.get("me", None)

    if token == None or Webex_API_Connector.is_token_valid(expires_at) == False or host_data == None:
        return redirect(url_for('login'))

    host_name = host_data['displayName'] 
    webex_api_connector = Webex_API_Connector(token, expires_at)    
    device_data_and_bookings, locations_list = get_device_data_and_bookings(webex_api_connector)

    if request.method == 'POST':
        
        try:
            title = request.form.get("title")
            start_date = request.form.get("start_date")
            end_date = request.form.get("end_date")
            device_id = request.form.get("device_select")
            device_display_name, device_email  = retrieve_device_name_email(device_id, device_data_and_bookings)
            host_email = host_data['emails'][0]
            legal_external_person_email = request.form.get("external_select")
            legal_external_person_display_name = retrieve_legal_external_person_name(legal_external_person_email)
            meeting = webex_api_connector.create_meetings(title, start_date, end_date, legal_external_person_email, legal_external_person_display_name, host_email, device_email, device_display_name)
            
            meeting_sip_address = meeting['sipAddress']
            updated_bookings_for_device = wait_for_meeting_to_be_available_on_device(webex_api_connector, device_id, meeting_sip_address)

            device_data_and_bookings = update_booking_data(device_data_and_bookings, device_id, updated_bookings_for_device)

            return render_template('meeting.html', created = True, host_name=host_name, external_persons=external_persons, phonebook_devices=device_data_and_bookings, locations_list=locations_list)
            
        except Exception as e:
            return render_template('meeting.html', error=True, errormessage=e, errorcode="", created = False, host_name=host_name, external_persons=external_persons, phonebook_devices=device_data_and_bookings, locations_list=locations_list)

    else:
        return render_template('meeting.html', created = False, host_name=host_name,  external_persons=external_persons, phonebook_devices=device_data_and_bookings, locations_list=locations_list)



def get_device_data_and_bookings(webex_api_connector):

    phonebook_devices = webex_api_connector.get_tagged_devices()
    workspaces = webex_api_connector.get_workspaces()
    workspace_locations = webex_api_connector.get_workspace_locations()

    phone_book_with_workspace_email = append_workspaces_email_to_device_data(phonebook_devices, workspaces)
    phone_book_with_workspace_email_and_bookings = append_bookings_to_device_data(webex_api_connector, phone_book_with_workspace_email)
    phone_book_with_workspace_location, locations_list = append_location_data_to_device_data(phone_book_with_workspace_email_and_bookings, workspace_locations)

    return phone_book_with_workspace_location, locations_list


def append_workspaces_email_to_device_data(phonebook_devices, workspaces):

    for device in phonebook_devices:

        device_sip_urls = device["sipUrls"]
        workspace_email  = return_workspace_email(workspaces, device_sip_urls)
        device["workspaceEmail"] = workspace_email

    return phonebook_devices


def return_workspace_email(workspaces, device_sip_urls):

    for workspace in workspaces:
        workspace_sip = workspace["sipAddress"]
        if workspace_sip in device_sip_urls:
            return workspace['calendar']['emailAddress']


def append_bookings_to_device_data(webex_api_connector, extended_phone_book):
    
    for device in extended_phone_book:
        device_id = device['id']
        bookings = webex_api_connector.get_booking_list_xapi(device_id)
        if bookings['result']['ResultInfo']['TotalRows'] != 0:
            device.update([("bookings", bookings['result']['Booking'])])
        else:
            device.update([("bookings", [])])

    return extended_phone_book


def append_location_data_to_device_data(extended_phone_book, workspace_locations):
    
    locations_list = []
    for device in extended_phone_book:
        device_workspace_location_id = device['workspaceLocationId']
        location_name  = return_workspace_location_data(device_workspace_location_id, workspace_locations)
        device["locationName"] = location_name
        locations_list.append(location_name) if location_name not in locations_list else locations_list

    return extended_phone_book, locations_list


def return_workspace_location_data(device_workspace_location_id, workspace_locations):
    
    for location in workspace_locations:
        workspace_location_id = location["id"]
        if workspace_location_id == device_workspace_location_id:
            return location['displayName']


def retrieve_device_name_email(device_id, phonebook_devices):

    for device in phonebook_devices:
        if device['id'] == device_id:
            device_display_name = device['displayName']
            device_email = device['workspaceEmail'] 
            return device_display_name, device_email


def retrieve_legal_external_person_name(external_person_email):
    
    global external_persons

    for external_person in external_persons:
        email = external_person['email']
        if email == external_person_email:
            display_name = external_person['name']
            return display_name


def wait_for_meeting_to_be_available_on_device(webex_api_connector, device_id, meeting_sip_address):
    
    while True:
        bookings = webex_api_connector.get_booking_list_xapi(device_id)
        
        if bookings['result']['ResultInfo']['TotalRows'] != 0:
            for booking in bookings['result']['Booking']:
                for call in booking['DialInfo']['Calls']['Call']:
                    booking_call_number = call['Number']
                    if booking_call_number == meeting_sip_address:
                        print("New Booking available on device.")
                        return bookings['result']['Booking']
        
        time.sleep(5)



def update_booking_data(device_data_and_bookings, device_id_for_update, updated_bookings_for_device):
    
    for device in device_data_and_bookings: 

        device_id = device['id']
        if device_id_for_update == device_id:
            device['bookings'] = updated_bookings_for_device

    return device_data_and_bookings


if __name__ == "__main__":

    CLIENT_ID = os.environ['CLIENT_ID'] 
    CLIENT_SECRET = os.environ['CLIENT_SECRET']
    REDIRECT_URI = os.environ['REDIRECT_URI']  
    AUTHORIZATION_BASE_URL = os.environ['AUTHORIZATION_BASE_URL']
    AUTH_TOKEN_URL = os.environ['AUTH_TOKEN_URL']
    SCOPE = json.loads(os.environ['SCOPE']) 
    
    app.run(port='5001', debug=True)

