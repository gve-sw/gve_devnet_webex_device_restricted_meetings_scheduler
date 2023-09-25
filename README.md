# GVE DevNet Webex Devices Restricted Meetings Scheduler

A sample app that restricts the scheduling of meetings based on tagged Webex devices and a predefined list of external persons (legal representative, no legal representative, e.g. lawyer or social workers). The app provides availability information for each workspace during the scheduling process to prevent overbooking. Filters based on the workspace location and external person role is provided.


## Contacts
* Ramona Renner


## Solution Components
* Webex Control Hub
* Webex Device/s
* Microsoft Office 365


## Workflow

![workflow](/IMAGES/workflow.png)


## High Level Design

![High level design of PoV](/IMAGES/high_level_design.png)


## Related Sandbox Environment

The [Cisco Webex Sandbox](https://devnetsandbox.cisco.com/RM/Diagram/Index/cf7eca30-b4e8-44be-a529-e25a1c078ab3?diagramType=Topology) demo instance provides developers with a full-featured sandbox Webex site (including admin access) designed to allow you to explore Webex functionality and develop proof-of-concept apps using the various Webex user/admin APIs and SDKs.


# Installation/Configuration

## Environment Setup

### Solutions and Devices

This sample code relies on Webex Control Hub and one or more Webex devices. All devices have to be configured with an email address, shared mode and associated with a workspace. While the email address needs to be set up as a room resource in O365, and the Webex O365 calendar integration set up to share the calendar information for these devices with Webex. Further details about the deployment of the cloud-based hybrid calendar for Office 365 can be found [here](https://www.cisco.com/c/en/us/td/docs/voice_ip_comm/cloudCollaboration/spark/hybridservices/calendarservice/cmgt_b_deploy-spark-hybrid-calendar-service/cmgt_b_deploy-spark-hybrid-calendar-service_chapter_0111.html). When an invitation is sent to the device's email address, all meeting details and connection options are embedded behind the green Join button.


### Tag Webex Devices and Associate Location Data

This sample code automatically retrieves the list of devices to add to the meeting schedular from Webex Control Hub. Thereby, the app displays all devices with a specific tag, e.g. **phonebook**. Add the mentioned tag to each device based on the instructions at [Group Devices with Tags](https://help.webex.com/en-us/article/n57ehgbb/Group-Devices-with-Tags).

Furthermore, the location and email of all workspaces is automatically retrieved via the Webex API. Please define the mentioned values accordingly in Webex Control Hub as described under [Create a Workspace and Add Services for a Webex Room Device or a Cisco Webex Board](https://help.webex.com/en-us/article/1mqb9cb/Add-Shared-Devices-and-Services-to-a-Workspace#id_137803), [Add a single location](https://help.webex.com/en-us/article/ajh6iy/Locations-in-Control-Hub#task-template_ebbb42a3-5e2e-4e62-820a-3c9c854ef247) and [Add a workspace to a location](https://help.webex.com/en-us/article/ajh6iy/Locations-in-Control-Hub#task-template_25c727e4-4b6f-4584-b279-2f01c98750b9).


### Register an Webex OAuth Integration

**OAuth Integrations**: Integrations are how you request permission to invoke the Webex REST API on behalf of a Webex Teams user. To do this securely, the API supports the OAuth2 standard, which allows third-party integrations to get a temporary access token for authenticating API calls. 

To register an integration with Webex Teams:
1. Log in to **developer.webex.com**
2. Click on your avatar at the top of the page and then select **My Webex Apps**
3. Click **Create a New App**
4. Click **Create an Integration** to start the wizard
5. Fill in the following fields of the form:
   * **Will this integration use a mobile SDK?**: No
   * **Integration name**
   * **Icon**
   * **App Hub Description**
   * **Redirect URI(s)**: http://localhost:5001/callback
   * **Scopes**: Select "spark:all","spark-admin:devices_read","spark:xapi_statuses","spark:xapi_commands","spark-admin:devices_write","spark:devices_read","spark:devices_write","spark-admin:workspaces_read","spark-admin:workspaces_write", "meeting:admin_schedule_write", "meeting:admin_schedule_read", "meeting:participants_write", "meeting:participants_read", "spark-admin:workspace_locations_read"
6. Click **Add Integration**
7. After successful registration, you'll be taken to a different screen containing your integration's newly created Client ID and Client Secret and more. Copy the secret, ID and OAuth Authorization URL and store it safely. Please note, that the Client Secret will only be shown once for security purposes

  > To read more about Webex Integrations & Authorization and to find information about the different scopes, you can find information [here](https://developer.webex.com/docs/integrations)


## Set up the Sample App

8. Make sure you have [Python 3.8.10](https://www.python.org/downloads/) and [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed.

9. (Optional) Create and activate a virtual environment for the project ([Instructions](https://docs.python.org/3/tutorial/venv.html))   

10. Access the created virtual environment folder
    ```
    cd [add name of virtual environment here] 
    ```

11. Clone this GitHub repository into the local folder:  
    ```
    git clone [add GitHub link here]
    ```
    * For GitHub link: 
      In GitHub, click on the **Clone or download** button in the upper part of the page > click the **copy icon**  
      ![/IMAGES/giturl.png](/IMAGES/giturl.png)
  * Or simply download the repository as zip file using 'Download ZIP' button and extract it

12. Access the downloaded folder:  
    ```
    cd gve_devnet_webex_device_restricted_meetings_scheduler
    ```

13. Install all dependencies:
    ```
    pip3 install -r requirements.txt
    ```

14. Fill in the settings.py file to provide the external persons for the scheduler. Each person is defined by one dictionary with name, email and role (representative or no_representative) within the list.
  
  ```python
    
  external_persons = [
      {
        'name': 'John Doe (Lawyer)',
        'email': 'placeholder_email1@cisco.com',
        'role': 'representative'
      },
      {
        'name': 'Jane Schmoe (Social Worker)',
        'email': 'placeholder_email2@cisco.com',
        'role': 'no_representative'
      }
  ]
  ```

15. Fill in your variables in the .env file. Feel free to leave the variable without note as is (for testing purpose): 

  ```python
    CLIENT_ID=[Add client ID from step 7] 
    CLIENT_SECRET=[Add client secret from step 7] 

    REDIRECT_URI=http://localhost:5001/callback
    AUTHORIZATION_BASE_URL=[Add first part of the OAuth Authorization URL from step 7, e.g. https://webexapis.com/v1/authorize]
    AUTH_TOKEN_URL=[Add first part of the OAuth Authorization URL and replace the string "authorize" with "access_token" from step 7, e.g. https://webexapis.com/v1/access_token]
    SCOPE=["spark:all","spark-admin:devices_read","spark:xapi_statuses","spark:xapi_commands","spark-admin:devices_write","spark:devices_read","spark:devices_write","spark-admin:workspaces_read","spark-admin:workspaces_write", "meeting:admin_schedule_write", "meeting:admin_schedule_read", "meeting:participants_write", "meeting:participants_read", "spark-admin:workspace_locations_read"]

    TAG=Name of tag assigned to devices that should be part of the phonebook
  ```
> Note: Mac OS hides the .env file in the finder by default. View the demo folder for example with your preferred IDE to make the file visible.


# Usage

16. Start the flask application:   

```python3 app.py```

Navigate to http://localhost:5001 and follow the application workflow.


# Screenshots

![/IMAGES/screenshot.png](/IMAGES/screenshot.png)

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.