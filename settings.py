CARBON_SERVER = 'dashboard.entrymissing.net'
CARBON_PORT = 2003

monitors = [{'monitor': 'EMailCollector',
             'ts_name': 'test.mail',
             'frequency': 3},
             {'monitor': 'RandomCollector',
             'ts_name': 'test.random',
             'frequency': 6}]