CARBON_SERVER = 'dashboard.entrymissing.net'
CARBON_PORT = 2003

monitors = [{'monitor': 'EMailCollector',
             'ts_name': 'data.mail',
             'frequency': 60*10,
             'config': {'email': 'entrymissing@gmail.com',
                        'prefix': '.private'}},
            {'monitor': 'PingCollector',
             'ts_name': 'data.ping',
             'frequency': 60*5,
             'config': {'ping_targets': ['192.168.0.1', 'google.com', 'spiegel.de',
                                         'scripts.mit.edu', 'mail.caltech.edu'],
                        'num_pings': 5}}]
