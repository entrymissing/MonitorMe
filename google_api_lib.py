import collections
import functools
import httplib2
import os

from apiclient import discovery
from apiclient import errors
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime
import time
import dateutil.parser
import socket
import private_keys


class memoized(object):
   '''Decorator. Caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned
   (not reevaluated).
   '''
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      if not isinstance(args, collections.Hashable):
         # uncacheable. a list, for instance.
         # better to not cache than blow up.
         return self.func(*args)
      if args in self.cache:
         return self.cache[args]
      else:
         value = self.func(*args)
         self.cache[args] = value
         return value
   def __repr__(self):
      '''Return the function's docstring.'''
      return self.func.__doc__
   def __get__(self, obj, objtype):
      '''Support instance methods.'''
      return functools.partial(self.__call__, obj)

#try:
#    import argparse
#    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
#except ImportError:
#    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = ('https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/gmail.readonly')
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
                                   'google-api.json')

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

@memoized
def connect_to_api(name, version):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build(name, version, http=http)
    
    return service

def combined_time_for_query(num_days = 7, query = 'Social', calendar_name = 'Tracking'):
  service = connect_to_api('calendar', 'v3')
  
  # Find the right calendar
  calendar_id = get_calendar_by_name(service, calendar_name)

  # Compute some timestamps
  now = datetime.datetime.utcnow()
  ndays = now - datetime.timedelta(hours = 24*num_days)
  # 'Z' indicates UTC time
  now = now.isoformat() + 'Z'
  ndays = ndays.isoformat() + 'Z'

  # Get all location entries between 3 days ago and yesterday
  eventsResult = service.events().list(
      calendarId=calendar_id, timeMin=ndays, timeMax=now, q=query, singleEvents=True,
      orderBy='startTime').execute()
  events = eventsResult.get('items', [])
  duration = 0
  for event in events:
    startTs = event['start'].get('dateTime', event['start'].get('date'))
    startTs = dateutil.parser.parse(startTs).timestamp()
    endTs = event['end'].get('dateTime', event['end'].get('date'))
    endTs = dateutil.parser.parse(endTs).timestamp()
    duration += (endTs - startTs)
   
  return duration
    
    
def time_spent_at_locations(num_days = 7, calendar_name = 'Tracking'):
  service = connect_to_api('calendar', 'v3')
  
  # Find the right calendar
  calendar_id = get_calendar_by_name(service, calendar_name)

  # Compute some timestamps
  now = datetime.datetime.utcnow()
  ndays = now - datetime.timedelta(hours = 24*num_days)
  # 'Z' indicates UTC time
  now = now.isoformat() + 'Z'
  ndays = ndays.isoformat() + 'Z'

  # Get all location entries between 3 days ago and yesterday
  eventsResult = service.events().list(
      calendarId=calendar_id, timeMin=ndays, timeMax=now, q='Location', singleEvents=True,
      orderBy='startTime').execute()
  events = eventsResult.get('items', [])

  data = collections.defaultdict(int)
  openTrack = False
  for event in events:
    # Get time as timestamp
    curTs = event['start'].get('dateTime', event['start'].get('date'))
    curTs = dateutil.parser.parse(curTs).timestamp()
    curState = event['summary'].split()[-1]
    curLocation = event['summary'].split()[-2]
    
    if openTrack:
      data[openLocation] += (curTs-openTs)
      openTrack = False
    
    if curState == 'entered':
      openTrack = True
      openTs = curTs
      openLocation = curLocation

  return data


def count_calendar_events_days(query, num_days = 7, calendar_name = 'Tracking'):
  service = connect_to_api('calendar', 'v3')
  
  # Find the right calendar
  calendar_id = get_calendar_by_name(service, calendar_name)

  # Compute some timestamps
  now = datetime.datetime.utcnow()
  ndays = now - datetime.timedelta(hours = 24*num_days)
  # 'Z' indicates UTC time
  now = now.isoformat() + 'Z'
  ndays = ndays.isoformat() + 'Z'

  # Get all location entries between 3 days ago and yesterday
  eventsResult = service.events().list(
      calendarId=calendar_id, timeMin=ndays, timeMax=now, q=query, singleEvents=True,
      orderBy='startTime').execute()
  events = eventsResult.get('items', [])
  return len(events)
  
  
def get_last_location(calendar_name = 'Tracking'):
  service = connect_to_api('calendar', 'v3')
  
  # Find the right calendar
  calendar_id = get_calendar_by_name(service, calendar_name)

  # Compute some timestamps
  now = datetime.datetime.utcnow()
  yesterday = now - datetime.timedelta(hours = 24)
  ndays = now - datetime.timedelta(hours = 24*3)
  # 'Z' indicates UTC time
  yesterday = yesterday.isoformat() + 'Z'
  ndays = ndays.isoformat() + 'Z'
  
  # Get all location entries between 3 days ago and yesterday
  eventsResult = service.events().list(
      calendarId=calendar_id, timeMin=ndays, timeMax=yesterday, q='Location', singleEvents=True,
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
        lastState = event['summary'].split()[-1]
        location = event['summary'].split()[-2]
    
    # Return the timestamp 24h ago, the event and the location
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(hours = 24)
    return lastState, location, yesterday.timestamp()

def ListMessagesMatchingQuery(service, user_id, query=''):
  """List all Messages of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
    Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

  Returns:
    List of Messages that match the criteria of the query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate ID to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query,
                                         pageToken=page_token).execute()
      messages.extend(response['messages'])
    return messages
  except errors.HttpError as error:
    print('An error occurred: %s' % error)

def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    return message
  except errors.HttpError as error:
    print('An error occurred: %s' % error)

    
def get_gmail_length_of_query():
  service = connect_to_api('gmail', 'v1')
  
  data = []
  now = datetime.datetime.now().timestamp()
  
  mails = ListMessagesMatchingQuery(service, 'me', 'in:inbox')
  thread_ids = [m['threadId'] for m in mails]
  data.append(('inbox_size', len(set(thread_ids)), now))

  mails = ListMessagesMatchingQuery(service, 'me', 'in:sent newer_than:24h')
  thread_ids = [m['threadId'] for m in mails]
  data.append(('sent_last_24h', len(set(thread_ids)), now))

  mails = ListMessagesMatchingQuery(service, 'me', 'in:sent newer_than:12h')
  thread_ids = [m['threadId'] for m in mails]
  data.append(('sent_last_12h', len(set(thread_ids)), now))

  mails = ListMessagesMatchingQuery(service, 'me', 'in:sent newer_than:1h')
  thread_ids = [m['threadId'] for m in mails]
  data.append(('sent_last_1h', len(set(thread_ids)), now))

  return data
  
def get_oldest_inbox_mail():
  service = connect_to_api('gmail', 'v1')
  
  now = datetime.datetime.now().timestamp()
  
  mails = ListMessagesMatchingQuery(service, 'me', 'in:inbox')
  thread_age = {}

  if len(mails) == 0:
    return [('inbox_oldest', 0, now)]

  for m in mails:
    thread_id = m['threadId']
    msg = GetMessage(service, 'me', m['id'])
    age = now - (int(msg['internalDate'])/1000)
    if thread_id not in thread_age:
      thread_age[thread_id] = age
    else:
      if age < thread_age[thread_id]:
        thread_age[thread_id] = age

  return [('inbox_oldest', max(thread_age.values()), now)]
  
  
def main():
  #print(get_oldest_inbox_mail())
  #print(get_last_location())
  #print(count_calendar_events_days('Social', num_days = 7))
  #print(count_calendar_events_days('Social', num_days = 9))
  #print(time_spent_at_locations())
  #print(time_spent_at_locations(1))
  print(combined_time_for_query())
  print(combined_time_for_query(num_days=2))
if __name__ == '__main__':
  main()
