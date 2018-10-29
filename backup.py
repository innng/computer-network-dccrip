# rotas != link
# rotas: destino, gateway, peso
# link: destino, peso

# add 127.0.1.1 20 <-- arquivo
# add 127.0.1.1 30 <-- cli

# link = {
#   '127.0.1.21': {
#       'weight': 4
#       't': threading.Timer(4*pi, function=self.rmvLink)
#   }
# }

# links['127.0.1.1']['timer'] = self.setTimer(..)

# route = {
#   '127.0.1.21': {
#       'gateway': ['127.0.1.2'],
#       'weight': 5
#   }
# }

# x = .3
# ip: .5, hop: [.3, .6], w: 1
# ip: .3, hop: [.4], w: 2
# ip: .4, hop: [.1, .2], w: 3
# ip: .6, hop: [.3], w: 4

# 'distances': {
#   .5: 1,
#   .4, 3
# }


# Update
# {
    # 'destination': '127.0.1.3',
    # 'source': '127.0.1.1',
    # 'type': 'update',
    # 'distances': {
        # '127.0.1.2': 2,
        # '127.0.1.1': 0,
        # '127.0.1.4': 4
    # }
# }

# Routing Table ?
# {
#     '127.0.1.2': {
#         'hop': ['127.0.1.2']
#         'weight': 2,
#         'nextHop': 0
#         },
# }

# LinkTable (tabela com o endereço e distancia do
# roteador atual dos links)
# {
    # '127.0.1.1': 7,
    # '127.0.1.3': 3,
# }
