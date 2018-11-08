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

# link = {
#   '127.0.1.21': {
#       'weight': 4
#       'ttl': 4
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


# thread que controla recebimento de mensagens de update
def recvThread(self):
    while self.running.isSet():
        data, sourceAddr = self.sock.recvfrom(1024)
        msg = json.loads(data.decode())

        # Ve qual o tipo da mensagem
        if msg['type'] == 'update':
            # Pega os IPs e pesos do vetor distances da msg de update
            for ip, weight in msg['distances'].items():
                if ip in self.routingTable:
                    # V? se o link existe na tabela
                    if sourceAddr[0] in self.linkingTable:
                        currentWeight = int(self.linkingTable[sourceAddr[0]])
                        knownWeight = self.routingTable[ip]['weight']

                        if (weight + currentWeight) < knownWeight:
                            self.routingTable[ip]['weight'] = weight + currentWeight
                            self.routingTable[ip]['hop'] = []
                            self.routingTable[ip]['hop'].append([sourceAddr[0]])
                        elif (weight + currentWeight) == knownWeight:
                            hopIPs = []
                            for hopIP in self.routingTable[ip]['hop']:
                                hopIPs.append(hopIP[0])
                            if sourceAddr[0] not in hopIPs:
                                self.routingTable[ip]['hop'].append(sourceAddr)
                    pass
                else:
                    pass
                # ////////////////////////
        elif msg['type'] == 'trace':
            pass
        elif msg['type'] == 'data':
            pass

#     '127.0.1.2': {
#         'hop': ['127.0.1.2']
#         'weight': 2,
#         'nextHop': 0
#     },

if sourceAddr[0] in self.linkTable:
    currentWeight = int(self.linkTable[sourceAddr[0]]['weight'])
    knownWeight = self.routingTable[ip]['weight']

    if (weight + currentWeight) < knownWeight:
        self.routingTable[ip]['weight'] = int(weight) + currentWeight
        self.routingTable[ip]['hops'] = []
        self.routingTable[ip]['hops'].append([sourceAddr[0]])
    elif (weight + currentWeight) == knownWeight:
        hopIPs = []
        for hopIP in self.routingTable[ip]['hops']:
            hopIPs.append(hopIP)
        if sourceAddr[0] not in hopIPs:
            self.routingTable[ip]['hops'].append(sourceAddr[0])

self.routingTable[ip] = {}
self.routingTable[ip]['weight'] = int(weight) + int(self.linkTable[sourceAddr[0]])
self.routingTable[ip]['hops'] = []
self.routingTable[ip]['hops'].append(sourceAddr[0])

update = {'type': 'trace', 'source': self.host, 'destination': ip, 'hops': []}
update['hops'].append(update['source'])


traceBack = {'type': 'data', 'source': self.host, 'destination': msg['source'], 'payload': msg}
