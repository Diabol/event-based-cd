require 'rest-client'
require 'json'

SCHEDULER.every '3s' do
  url = 'http://52.211.202.77/streams/cd-events'
  streamResponse = RestClient.get(url, headers={Accept: "application/json"})
  streamJson = JSON.parse(streamResponse)
  #print "streamJson: #{streamJson}\n"
  entries = streamJson['entries']
  #print "entries: #{entries}\n"
  events = Array.new
  entries.each { |entry|
    id = entry['id'].sub(/:2113/, '')
    #print "id: #{id}\n"
    response = RestClient.get(id, headers={Accept: "application/json"})
    #print "response #{id}: #{response}\n"
    json = JSON.parse(response)
    json.default  = ''
    #print "json: #{id}: #{json}\n"
    source = json['source'].sub(/http:\/\/github.com/, '')
    rev = json['source_revision'][0..6]
    image = json['image'][/.*\/(.*:.*)/, 1]
    events.push( {
      label: json['event'] + ': ' + source + ' ' + rev + ' ' + image,
      value: json['status'] + ': ' + json['msg'] + ' ' + json['link'] + ' ' + json['date']
    } )
  }
  #print "#{events}\n"
  send_event('cd_list', { items: events })
end