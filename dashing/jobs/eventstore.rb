require 'rest-client'
require 'json'

SCHEDULER.every '3s' do
  url = 'http://52.211.202.77/streams/newstream'
  response = RestClient.get(url)
  json = JSON.parse(response)
  events = [ { label: 'marcus', value: 'hej' }, { label: 'robert', value: 'ho' } ]
  send_event('cd_list', { items: events })
end