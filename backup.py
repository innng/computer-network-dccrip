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

# def setTimer(self, tout, func, arg=None):
#     time = threading.Timer(tout, function=func, args=arg)
#     return time

# links['127.0.1.1']['timer'] = self.setTimer(..)

# route = {
#   '127.0.1.21': {
#       'gateway': ['127.0.1.2'],
#       'weight': 5
#   }
# }
    # inicia a execução do roteador
    def start(self):
        # envia primeiras mensagens de update
        self.sendUpdate()

        # Enviar updates
        # updateMsg = threading.Thread(target=self.setUpdates)
        # updateMsg.start()

        # while True:
        #     events, _, _ = select.select([sys.stdin, self.sock], [], [])

        #     for event in events

        # Receber comandos
        # cli = threading.Thread(target=self.cliThread)
        # cli.start()

        # Receber mensagens
        # recv = threading.Thread(target=self.get)
        # recv.start()

        # Gerenciar tempo de vida das rotas quem não manda updates por 4
        # periodos some e as rotas são recalculadas
        # routeTimeout = threading.Thread(target=self.routeTimeout)
        # routeTimeout.start()

        # cli.join()
        # recv.join()
        # updateMsg.join()

    # constroi as mensagens
    def buildMsg(self, src, dest, tp, pl=None, dist=None, hp=None):
        msg = {
            'type': tp,
            'source': src,
            'destination': dest
        }

        if tp == 'data':
            msg.update({'payload': pl})
        elif tp == 'update':
            msg.update({'distances': dist})
        elif tp == 'trace':
            hp.append(self.host)
            msg.update({'hops': hp})

        return msg

    # adiciona roteador à tabela de rotas
    def addRoute(self, ip, gw, w=1):
        pass

    # remove roteador da tabela de rotas
    def rmvRoute(self, ip):
        pass

    # atualiza roteador na lista de rotas
    def updRoute(self, ip, gw, w=1):
        pass

    # envia mensagens via socket
    def send(self):
        pass

    # recebe mensagens via socket
    def get(self):
        pass

    # recebe comandos via stdin
    def cliThread(self):
        pass

    # envia mensagens de update aos roteadores vizinhos
    def sendUpdate(self):
        pass
        self.updTimer = self.setTimer(self.sendUpdate)
        # self.updTimer.start()

    # trata os updates recebidos
    def setUpdates(self):
        pass
