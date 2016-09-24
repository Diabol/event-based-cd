from flask import Flask
from flask import request
import json
import requests

app = Flask(__name__)

# Adapted event example/spec that's inserted into the event store
# """
# [
#   {
#     "eventId": "fbf5a1a1-b4a3-4dfe-a01f-ec52c34e16ed",
#     "eventType": "event-CD",
#     "data": {
#       "date": "",
#       "status": "" [ok,fail,in-progress],
#       "source": "" [scm repo uri],
#       "source-revision": "",
#       "image": "",
#       "event": "", [commit,build,deploy,test]
#       "msg": message,
#       "link": "" [event source link]
#
#     }
#   }
# ]
# """


@app.route("/", methods=['POST'])
def events():
    json_data = json.loads(request.data)
    msg = json.loads(json_data['Message'])

    # TODO: Decide how to handle 'unknown' message types
    store_event = {
        'eventId': json_data['MessageId'],
        'eventType': 'event-cd'
    }

    event_data = {
        'date': json_data['Timestamp']  # TODO: This is the time for the queue msg, not necessarily the event time!
    }

    if 'MessageAttributes' in json_data and 'X-Github-Event' in json_data['MessageAttributes']:
        print('Received github commit event')
        event_data['event'] = 'commit'
        event_data['source'] = msg['repository']['url']
        event_data['source_revision'] = msg['after']
        event_data['link'] = msg['head_commit']['url']
        event_data['status'] = 'ok'
    else:
        # Default case
        print('Received {} event'.format(json_data['Subject']))
        event_data['event'] = json_data['Subject']
        event_data['status'] = msg['status']
        event_data['source'] = msg['source']
        event_data['source_revision'] = msg['source_revision']
        event_data['image'] = msg['image']

    if 'msg' in msg:
        event_data['msg'] = msg

    store_event['data'] = event_data

    print('Storing event: {}'.format(store_event))
    send_to_eventstore(store_event)
    print('Event stored, returning')

    return "OK"


def send_to_eventstore(event):
    url = 'http://127.0.0.1:2113/streams/cd-events-ng'
    headers = {'Content-Type': 'application/vnd.eventstore.events+json'}
    r = requests.post(url, data=json.dumps([event]), headers=headers)
    if r.status_code != requests.codes.created:
        print('Failed to store event: {}'.format(r))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
