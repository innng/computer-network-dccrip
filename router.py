#!/usr/bin/env python3

import threading
import argparse
import select
import socket
import sys

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


class Router:
    # porta padrão
    port = 55151
    # endereço de IP do roteador
    host = ''
    # período de alterações
    tout = 0
    # socket UDP
    sock = None
    # timer para envio de mensagens de update
    updTimer = None
    # evento para controlar execução
    running = None
    # tabela de links
    linkingTable = {}
    # tabela de rotas
    routingTable = {}

    # inicializa roteador
    def __init__(self, args):
        self.host = args.addr
        self.tout = args.timeout

        try:
            # cria socket UDP
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

            # associa o socket ao endereço de IP
            self.sock.bind((self.host, self.port))
        except socket.error as error_msg:
            self.logExit(error_msg)

        if args.config:
            self.startupConfig(args.config)

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

    # recebe comandos via arquivo
    def startupConfig(self, filename):
        with open(filename, 'r') as fp:
            lines = fp.read().splitlines()

        for ln in lines:
            self.parseCommand(ln)

    # extrai informações de comandos do arquivo e da cli
    def parseCommand(self, line):
        cmd = line.split(' ')
        cmd = [x for x in cmd if len(x) > 0]

        if cmd[0] == 'add':
            if cmd[1] not in self.linkingTable:
                if len(cmd) == 3:
                    self.addLink(cmd[1], int(cmd[2]))
                else:
                    self.addLink(cmd[1])
            else:
                print('IP já conhecido')
        elif cmd[0] == 'del':
            if cmd[1] in self.linkingTable:
                self.rmvLink(cmd[1])
            else:
                print('IP não conhecido')
        elif cmd[0] == 'trace':
            pass
        elif cmd[0] == 'quit':
            sys.exit()
        elif cmd[0] == 'debug':
            pass
        else:
            print('Comando inválido')

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

    # adiciona roteador à tabela de links
    def addLink(self, ip, weight=1):
        self.linkingTable[ip] = {}
        self.linkingTable[ip]['weight'] = weight
        self.linkingTable[ip]['timer'] = self.setTimer(self.rmvLink, [ip], 4)
        self.linkingTable[ip]['timer'].start()

    # remove roteador da tabela de links
    def rmvLink(self, ip):
        del self.linkingTable[ip]

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

    # retorna um objeto timer
    def setTimer(self, func, arg=[], mult=1):
        timer = threading.Timer(mult * self.tout, function=func, args=arg)

        return timer

    # tratamento de erros
    def logExit(self, error_msg):
        self.sock.close()
        sys.exit(error_msg)


def main():
    # recebe parâmetros por linha de comando
    parser = argparse.ArgumentParser('Parâmetros do roteador')
    parser.add_argument('--addr',
                        dest='addr',
                        type=str,
                        required=True,
                        help='IP do roteador'
                        )
    parser.add_argument('--update-period',
                        dest='timeout',
                        type=float,
                        required=True,
                        help='Perí­odo entre envio de mensagens'
                        )
    parser.add_argument('--startup-commands',
                        dest='config',
                        type=str,
                        required=False,
                        help='Arquivo de comandos'
                        )
    args = parser.parse_args()

    # configura e inicia roteador
    router = Router(args)
    router.start()


if __name__ == '__main__':
    main()
