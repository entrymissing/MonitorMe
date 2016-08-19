import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime
import time
import dateutil.parser
import socket
import private_keys

#try:
#    import argparse
#    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
#except ImportError:
#    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'MonitorMe'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def get_calendar_by_name(service, name):
    page_token = None
    while True:
      calendar_list = service.calendarList().list(pageToken=page_token).execute()
      for calendar_list_entry in calendar_list['items']:
        if calendar_list_entry['summary'] == name:
          return calendar_list_entry['id']
      page_token = calendar_list.get('nextPageToken')
      if not page_token:
        break
    return None

def connect_to_api():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    
    return service

def get_last_location(service, calendar_name = 'Tracking'):
  # Find the right calendar
  calendar_id = get_calendar_by_name(service, 'Tracking')

  # Compute some timestamps
  now = datetime.datetime.utcnow()
  yesterday = now - datetime.timedelta(hours = 24)
  ndays = now - datetime.timedelta(hours = 24*3)
  # 'Z' indicates UTC time
  yesterday = yesterday.isoformat() + 'Z'
  ndays = ndays.isoformat() + 'Z'
  
  # Get all location entries between 3 days ago and yesterday
  eventsResult = service.events().list(
      calendarId=calendar_id, timeMin=ndays, timeMax=yesterday, q='| Location', singleEvents=True,
      orderBy='startTime').execute()
  events = eventsResult.get('items', [])
  
  if not events:
    return False
  else:
    ts = 0
    for event in events:
      # Get time as timestamp
      newTs = event['start'].get('dateTime', event['start'].get('date'))
      newTs = dateutil.parser.parse(newTs).timestamp()
      
      # We are only looking for the latest location event
      if newTs > ts:
        ts = newTs
        lastState = event['summary'].split()[3]
        location = event['summary'].split()[2]
    
    # Return the timestamp 24h ago, the event and the location
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(hours = 24)
    return lastState, location, yesterday.timestamp()

#def main():
#  service = connect_to_api()
#  res = get_last_location(service)
#  print(res)

#if __name__ == '__main__':
#    main()