require 'rest-client'
require 'json'

SCHEDULER.every '4s' do
  url = 'http://52.211.202.77/streams/cd-events-ng'
  streamResponse = RestClient.get(url, headers={Accept: "application/json"})
  streamJson = JSON.parse(streamResponse)
  #print "streamJson: #{streamJson}\n"
  entries = streamJson['entries']
  #print "entries: #{entries}\n"
  
  events = Array.new
  latest_rev = ''
  send_event('pl-build', {})
  send_event('pl-stage', {})
  send_event('pl-prod', {})
  entries.each { |entry|
    id = entry['id'].sub(/:2113/, '')
    #print "id: #{id}\n"
    response = RestClient.get(id, headers={Accept: "application/json"})
    #print "response #{id}: #{response}\n"
    json = JSON.parse(response)
    json.default  = ''
    #print "json: #{id}: #{json}\n"
    source = json['source'].sub(/https?:\/\/github.com\//, '')
    rev = json['source_revision'][0..6]
    image = json['image'][/.*\/(.*:.*)/, 1]
    image = '' if image.nil?
    event = json['event']
    status = json['status']
    events.push( {
      label: event + ': ' + source + ' ' + rev + ' ' + image,
      value: status + ': ' + json['msg'] + ' ' + json['link'] + ' ' + json['date']
    } )
    if entries[0] == entry then
      latest_rev = json['source_revision'][0..6]
    end
    if rev == latest_rev then
      if event == 'built_image' then
        send_event('pl-build', { criticals: status == 'ok' ? 0 : 1, warnings: 0 })
      end
      if event == 'verified_test' then
        send_event('pl-stage', { criticals: status == 'ok' ? 0 : 1, warnings: 0 })
      end
      if event == 'verified_prod' then
        send_event('pl-prod', { criticals: status == 'ok' ? 0 : 1, warnings: 0 })
      end
    end
  }
  #print "#{events}\n"
  send_event('cd_list', { items: events })
  send_event('hash', { text: latest_rev })
end