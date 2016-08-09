CARBON_SERVER = 'dashboard.entrymissing.net'
CARBON_PORT = 2003

monitors_back = [{'monitor': 'EMailCollector',
             'ts_name': 'data.mail',
             'frequency': 60*10}]

monitors = [{'monitor': 'PingCollector',
             'ts_name': 'data.ping',
             'frequency': 20,
             'config': {'ping_targets': ['192.168.0.1', '8.8.8.8',
                                         'google.com', 'spiegel.de',
                                         'scripts.mit.edu', 'mail.caltech.edu'],
                        'num_pings': 5}}]
