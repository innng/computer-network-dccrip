#!/usr/bin/env python3

import threading
import argparse
import socket
import json
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
    # indica se roteador está executando
    running = None
    # timer para envio de mensagens de update
    updateTimer = None
    # tabela de links
    linkingTable = {}
    # tabela de rotas
    routingTable = {}

    # inicializa o roteador
    def __init__(self, args):
        self.host = args.addr
        self.tout = args.timeout

        try:
            # cria socket UDP
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # associa o socket ao endereço de IP
            self.sock.bind((self.host, self.port))

            # coloca o socket em modo não-blocante
            self.sock.setblocking(False)
        except socket.error as error_msg:
            self.logExit(error_msg)

        # utiliza configuração do arquivo se este foi especificado
        if args.startup:
            self.startupFile(args.startup)

    # extrai configs do arquivo
    def startupFile(self, filename):
        with open(filename, 'r') as fp:
            lines = fp.read().splitlines()

        for ln in lines:
            self.parseLinkCommand(ln)

    # inicia execução do roteador
    def start(self):
        # cria thread que recebe comandos do prompt
        cli = threading.Thread(target=self.cliThread)
        # cria thread que espera por mensagens
        recvMsg = threading.Thread(target=self.recvThread)
        # cria evento que indica que roteador está executando
        self.running = threading.Event()

        # inicia threads
        self.running.set()
        cli.start()
        recvMsg.start()

        # inicia o primeiro temporizador para enviar mensagens de update
        self.updateTimer = self.setTimer(self.sendUpdate)
        self.updateTimer.start()

        self.updateRoute('127.0.1.4', '127.0.1.2', 2)
        self.updateRoute('127.0.1.4', '127.0.1.3', 1)
        self.updateRoute('127.0.1.2', '127.0.1.4', 2)
        self.updateRoute('127.0.1.3', '127.0.1.4', 1)

    # extraí informações sobre vizinhos
    def parseLinkCommand(self, cmd):
        cmd = cmd.split(' ')
        cmd = [x for x in cmd if len(x) > 0]

        if cmd[0] == 'add':
            if len(cmd) != 3:
                print('Comando inválido')
            elif cmd[1] not in self.linkingTable:
                self.addLink(cmd[1], cmd[2])
            else:
                print('Vizinho já existe')

        elif cmd[0] == 'del':
            if len(cmd) != 2:
                print('Comando inválido')
            elif cmd[1] in self.linkingTable:
                self.rmvLink(cmd[1])
            else:
                print('Vizinho não existe')

        elif cmd[0] == 'trace':
            pass

        elif cmd[0] == 'quit':
            self.running.clear()
            self.updateTimer.cancel()

            for ip in self.linkingTable:
                self.linkingTable[ip]['timer'].cancel()

        elif cmd[0] == 'log':
            print('links -->', self.linkingTable)
            print('rotas -->', self.routingTable)
        else:
            print('Comando inválido')

        # adiciona novo vizinho à tabela de links
    def addLink(self, ip, weight):
        self.linkingTable[ip] = {}
        self.linkingTable[ip]['weight'] = int(weight)
        self.linkingTable[ip]['timer'] = self.setTimer(self.rmvLink, [ip], 4)
        self.linkingTable[ip]['timer'].start()

        self.addRoute(ip, ip, weight)

    # remove vizinho
    def rmvLink(self, ip):
        self.linkingTable[ip]['timer'].cancel()
        del self.linkingTable[ip]

        self.rmvRoute(ip)

    # adiciona um caminho à tabela de roteamento
    def addRoute(self, ip, hop, weight):
        self.routingTable[ip] = {}
        self.routingTable[ip]['hops'] = []
        self.routingTable[ip]['hops'].append(hop)
        if ip != hop:
            self.routingTable[ip]['weight'] = int(weight) + self.linkingTable[hop]['weight']
        else:
            self.routingTable[ip]['weight'] = int(weight)
        self.routingTable[ip]['nextHop'] = 0

    # remove um caminho
    def rmvRoute(self, ip):
        # testa se o ip está na tabela como destino
        if ip in self.routingTable:
            del self.routingTable[ip]

        # remove todos os caminhos que eram possíveis via ip
        ips = []
        for i in self.routingTable:
            if ip in self.routingTable[i]['hops']:
                self.routingTable[i]['hops'].remove(ip)
            if len(self.routingTable[i]['hops']) == 0:
                ips.append(i)

        # remove os nodos inalcançáveis
        for i in range(len(ips)):
            del self.routingTable[ips[i]]

    # atualiza um caminho existente
    def updateRoute(self, ip, hop, weight):
        weight += self.linkingTable[hop]['weight']

        # se custo é menor, substitui
        if self.routingTable[ip]['weight'] > weight:
            del self.routingTable[ip]
            self.addRoute(ip, hop, weight)
        # se custo é maior, ignora
        elif self.routingTable[ip]['weight'] < weight:
            pass
        # se custo é igual, adiciona gateway
        else:
            self.routingTable[ip]['hops'].append(hop)

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

    # envia mensagem de update
    def sendUpdate(self):
        for ip in self.linkingTable:
            distances = self.buildDistanceDict(ip)
            updMsg = self.buildMessage('update', self.host, ip, dist=distances)

            updMsg = json.dumps(updMsg)
            pkg = bytes(updMsg, 'ascii')
            self.sock.sendto(pkg, (ip, self.port))

        self.updateTimer = self.setTimer(self.sendUpdate)
        self.updateTimer.start()

    # constroi dicionário de distâncias, usando split horizon
    def buildDistanceDict(self, ip):
        dist = {}

        for key in self.routingTable:
            if ip != key:
                if len(self.routingTable[key]['hops']) > 1 or ip not in self.routingTable[key]['hops']:
                    dist.update({key: self.routingTable[key]['weight']})

        return dist

    # encaminha uma mensagem fazendo balanceamento de carga
    def forwardMessage(self, msg):
        # separa o ip do destinatário
        ip = msg['destination']
        # separa por qual gateway deve passar a mensagem
        nextHop = self.routingTable[ip]['nextHop']
        # separa o gateway pelo qual essa mensagem vai passar
        hop = self.routingTable[ip]['hops'][nextHop]

        # incrementa o hop para o balanceamento de cargas
        self.routingTable[ip]['nextHop'] += 1
        # se passou o número de gateways da lista, reseta contador
        if self.routingTable[ip]['nextHop'] > len(self.routingTable[ip]['hops']):
            self.routingTable[ip]['nextHop'] = 0

        msg = json.dumps(msg)
        pkg = bytes(msg, 'ascii')
        self.sock.sendto(pkg, (hop, self.port))

    # thread que controla recebimento de comandos via teclado
    def cliThread(self):
        while self.running.isSet():
            line = input('~ ')
            self.parseLinkCommand(line)

    # thread que controla recebimento de mensagens de update
    def recvThread(self):
        while self.running.isSet():
            try:
                data, sourceAddr = self.sock.recvfrom(1024)
                msg = json.loads(data.decode())
            except BlockingIOError:
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
