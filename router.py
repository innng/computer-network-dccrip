#!/usr/bin/env python3

import threading
import argparse
import socket
import sys


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
    links = {}
    # tabela de rotas
    routingTable = {}

    # inicializa o roteador
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

        self.running = threading.Event()

        if args.startup:
            self.startupFile(args.startup)

    # inicia a execução do roteador
    def start(self):
        # envia primeira mensagem de update com os links do arquivo de startup
        if len(self.links) > 0:
            self.sendUpdate()

        # inicia a thread que recebe comandos do prompt
        cli = threading.Thread(target=self.cliThread)
        # cli.start()

        # inicia a thread que espera por mensagens
        get = threading.Thread(target=self.getThread)
        # get.start()

        # evento que avisa que o roteador está rodando
        self.running.set()

    # extrai configs do arquivo
    def startupFile(self, filename):
        with open(filename, 'r') as fp:
            lines = fp.read().splitlines()

        for ln in lines:
            self.parseLinkCommand(ln)

    # extrain informações sobre vizinhos
    def parseLinkCommand(self, cmd):
        cmd = cmd.split(' ')
        cmd = [x for x in cmd if len(x) > 0]

        if cmd[0] == 'add':
            if cmd[1] not in self.links:
                self.addLink(cmd[1], cmd[2])
            else:
                print('Vizinho já existe')
        elif cmd[0] == 'del':
            if cmd[1] in self.links:
                self.rmvLink(cmd[1])
            else:
                print('Vizinho não existe')
        elif cmd[0] == 'trace':
            pass
        elif cmd[0] == 'quit':
            sys.exit()
        elif cmd[0] == 'debug':
            pass
        else:
            print('Comando inválido')

    # thread que roda a cli
    def cliThread(self):
        while self.running.is_set:
            line = input('~ ')
            self.parseLinkCommand(line)

    # adiciona novo vizinho à lista de links
    def addLink(self, ip, weight):
        self.links[ip] = {}
        self.links[ip]['weight'] = int(weight)
        self.links[ip]['timer'] = self.setTimer(self.rmvLink, [ip], 4)
        self.links[ip]['timer'].start()

        if self.running.is_set:
            self.sendUpdate()

    # remove vizinho
    def rmvLink(self, ip):
        del self.links[ip]

    # constroi mensagens
    def buildMessage(self, tp, src, dest, pl=None, dist=None):
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
            pass

        return msg

    # constroi dicionário de distâncias das mensagens de update, usando split horizon
    def buildDistDict(self, ip):
        dist = {}

        for key in self.links:
            if key != ip:
                dist[key] = self.links[key]['weight']

        return dist

    # envia mensagem de update
    def sendUpdate(self):
        for ip in self.links:
            distances = self.buildDistDict(ip)
            updMsg = self.buildMessage('update', self.host, ip, dist=distances)

            pkg = bytes(updMsg, 'ascii')
            self.sock.sendto(pkg, (ip, self.port))

        self.updTimer.cancel()
        self.updTimer = self.setTimer(self.sendUpdate)
        self.updTimer.start()

    # thread que espera por pacotes
    def getThread(self):
        while self.running.is_set:
            pass

    # atualiza tabela de roteamento
    def updateTable(self):
        pass

    # retorna um objeto Timer
    def setTimer(self, fn, argList=[], multiplier=1):
        timer = threading.Timer(self.tout * multiplier, fn, argList)

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
                        dest='startup',
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
