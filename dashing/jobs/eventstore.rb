# :first_in sets how long it takes before the job is first run. In this case, it is run immediately

SCHEDULER.every '3s' do
  events = [ { label: 'marcus', value: 'hej' }, { label: 'robert', value: 'ho' } ]
  send_event('cd_list', { items: events })
end