#!/usr/bin/env python3

import argparse
import socket
import sys


class Router:
    # porta padrão
    port = 55151
    # endereço de IP do roteador
    host = ''
    # tamanho do temporizador entre mensagens de update
    tout = 0
    # socket UDP
    sock = None
    # tabela de rotas
    linkTable = {}

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
            self.setInitialConfig(args.config)

    # recebe input via stdin
    def commandLine(self):
        string = input('~ ')
        self.parseCommand(string)

    # extrai topologia do arquivo
    def setInitialConfig(self, filename):
        with open(filename, 'r') as fp:
            lines = fp.read().splitlines()

            for ln in lines:
                self.parseCommand(ln)

    # extrai informações de comandos do arquivo e stdin
    def parseCommand(self, command):
        cmd = command.split(' ')
        cmd = [x.strip() for x in cmd if len(x) > 0]

        if cmd[0] == 'add':
            if cmd[1] not in self.linkTable:
                if len(cmd) == 3:
                    self.addLink(cmd[1], cmd[2])
                else:
                    self.linkTable(cmd[1])
            else:
                print('IP já existe!')

        elif cmd[0] == 'del':
            if cmd[1] in self.linkTable:
                self.rmvLink(cmd[1])

        elif cmd[0] == 'trace':
            print()

        elif cmd[0] == 'quit':
            sys.exit()

        elif cmd[0] == 'debug':
            print()

        else:
            print('Comando inválido')

    # inicia execução do roteador
    def start(self):
        while True:
            self.commandLine()
            print(self.linkTable)

    def buildMessage(self, s, d, t, pl=None, dist=None, hp=None):
        msg = {
            'type': t,
            'source': s,
            'destination': d
        }

        if t == 'data':
            msg.update({'payload': pl})
        elif t == 'update':
            msg.update({'distances': dist})
        elif t == 'trace':
            hp.append(self.host)
            msg.update({'hops': hp})

        return msg

    # adiciona um novo link
    def addLink(self, d, w=1, gw=None):
        self.linkTable[d] = {}
        if gw:
            self.linkTable[d]['gateway'] = list(gw)
        else:
            self.linkTable[d]['gateway'] = list()
        self.linkTable[d]['weight'] = w

    # remove um link
    def rmvLink(self, d):
        del self.linkTable[d]

    # atualiza link
    def updLink(self, d, gw, w=1):
        if self.linkTable[d]['weight'] < w:
            self.linkTable['gateway'] = list(gw)
            self.linkTable['weight'] = w

        elif self.linkTable[d]['weight'] > w:
            return
        else:
            self.linkTable['gateway'].append(gw)


def main():
    # recebe parâmetros por linha de comando
    parser = argparse.ArgumentParser('Parâmetros do roteador')
    parser.add_argument('--addr', dest='addr', type=str,
                        required=True, help='IP do roteador')
    parser.add_argument('--update-period', dest='timeout', type=float,
                        required=True, help='Período entre envio de mensagens')
    parser.add_argument('--startup-commands', dest='config',
                        type=str, required=False, help='Arquivo de comandos')
    args = parser.parse_args()

    # configura e inicia roteador
    router = Router(args)
    router.start()


if __name__ == '__main__':
    main()
