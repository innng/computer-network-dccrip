#!/usr/bin/env python3

import argparse
import json
import math
import socket
import sys
import threading
import time


class Router:

    port = 55151        # porta padrão
    sock = None         # socket UDP
    running = None      # indica se roteador está executando
    linkTable = {}      # tabela de links
    routingTable = {}   # tabela de rotas

    updateTimer = None  # timer para envio de mensagens de update
    host = ''           # endereço de IP do roteador
    tout = 0            # período de alterações

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
            elif cmd[1] not in self.linkTable:
                self.addLink(cmd[1], cmd[2])
            else:
                print('Vizinho já existe')

        elif cmd[0] == 'del':
            if len(cmd) != 2:
                print('Comando inválido')
            elif cmd[1] in self.linkTable:
                self.rmvLink(cmd[1])
            else:
                print('Vizinho não existe')

        elif cmd[0] == 'trace':
<<<<<<< HEAD
            self.sendTrace(cmd[1])
=======
            if len(cmd) != 2:
                print('Comando inválido')
            msg = self.buildMessage('trace', self.host, cmd[1])
            self.sendMessage(msg, cmd[1])
>>>>>>> bb072be2b1b7a4aae4506bb17c28efddd7a3933f

        elif cmd[0] == 'quit':
            self.running.clear()
            self.updateTimer.cancel()

            for ip in self.linkTable:
                self.linkTable[ip]['timer'].cancel()

        elif cmd[0] == 'log':
            print('links -->', self.linkTable)
            print('rotas -->', self.routingTable)
        else:
            print('Comando inválido')

<<<<<<< HEAD

=======
>>>>>>> bb072be2b1b7a4aae4506bb17c28efddd7a3933f
    # adiciona novo vizinho à tabela de links
    def addLink(self, ip, weight):
        self.linkTable[ip] = {}
        self.linkTable[ip]['weight'] = int(weight)
        self.linkTable[ip]['timer'] = self.setTimer(self.rmvLink, [ip], 4)
        self.linkTable[ip]['timer'].start()

        self.addRoute(ip, ip, weight)


    # remove vizinho
    def rmvLink(self, ip):
        self.linkTable[ip]['timer'].cancel()
        del self.linkTable[ip]

        self.rmvRoute(ip)


    # adiciona um caminho à tabela de roteamento
    def addRoute(self, ip, hop, weight):
        self.routingTable[ip] = {}
        self.routingTable[ip]['hops'] = []
        self.routingTable[ip]['hops'].append(hop)
        if ip != hop: #? ip = hop sempre "self.addRoute(ip, ip, weight)"
            self.routingTable[ip]['weight'] = int(weight) + self.linkTable[hop]['weight']
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
            del self.routingTable[ips[i]] #  Distancia infinita (não há rota)

        #? Mandar Update aqui?


    # atualiza um caminho existente
    def updateRoute(self, ip, hop, weight):
        weight += self.linkTable[hop]['weight']

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

<<<<<<< HEAD

    # constroi mensagens
    def buildMessage(self, tp, src, dest, pl=None, dist=None):
=======
    # constroi mensagem inicial
    def buildMessage(self, tp, src, dest, pl=None, dist=None, hops=[]):
>>>>>>> bb072be2b1b7a4aae4506bb17c28efddd7a3933f
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
            hops.append(self.host)
            msg.update({'hops': hops})

        return msg


    # envia mensagem de update
    def sendUpdate(self):
        for ip in self.linkTable:
            distances = self.buildDistanceDict(ip)
            updMsg = self.buildMessage('update', self.host, ip, dist=distances)
            self.sendMessage(updMsg, ip)

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

        # descarta mensagem se não existe caminho para o destinatário
        if ip not in self.routingTable:
            return

        # separa por qual gateway deve passar a mensagem
        nextHop = self.routingTable[ip]['nextHop']
        # separa o gateway pelo qual essa mensagem vai passar
        hop = self.routingTable[ip]['hops'][nextHop]

        # incrementa o hop para o balanceamento de cargas
        self.routingTable[ip]['nextHop'] += 1
        # se passou o número de gateways da lista, reseta contador
        if self.routingTable[ip]['nextHop'] > len(self.routingTable[ip]['hops']):
            self.routingTable[ip]['nextHop'] = 0

        self.sendMessage(msg, hop)

    # envia uma mensagem para um destinatário
    def sendMessage(self, msg, ip):
        msg = json.dumps(msg)
        pkg = bytes(msg, 'ascii')
        self.sock.sendto(pkg, (ip, self.port))


    # thread que controla recebimento de comandos via teclado
    def cliThread(self):
        while self.running.isSet():
            line = input('~ ')
            self.parseLinkCommand(line)


    # trata as mensagens recebidas
    def parseMessage(self, data, sourceAddr):
        msg = json.loads(data.decode())

        if msg['type'] == 'update':
            # Pega os IPs e pesos do vetor distances da msg de update
            for ip, weight in msg['distances'].items():
                # Já está na tabela de roteamento
                if ip in self.routingTable:
                    # Ve se o link existe na tabela
                    if sourceAddr[0] in self.linkTable:
                        currentWeight = int(self.linkTable[sourceAddr[0]])
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
                # Não está na tabela de roteamento
                else:
                    self.routingTable[ip] = {}
                    self.routingTable[ip]['weight'] = int(weight) + int(self.linkTable[sourceAddr[0]])
                    self.routingTable[ip]['hops'] = []
                    self.routingTable[ip]['hops'].append(sourceAddr[0])

                #? update TTL /\/\/\/\/\/\/\ não entendi como é pra fazer sem aquele segundo campo com o 4
        elif msg['type'] == 'data':
            if msg['destination'] == self.host:
                # Esse nó é o destino, mensagem recebida.
                print("Mensagem recebida:", msg['payload'])
            else:
                self.forwardMessage(msg) #? Não era simplesmene enviar pro nextHop como mensagem comum?
        elif msg['type'] == 'trace':
            # Esse nó é o destino do trace
            if msg['destination'] == self.host:
                traceBack = {'type': 'data', 'source': self.host, 'destination': msg['source'], 'payload': msg}
                self.forwardMessage(traceBack)
            # Esse não é o nó destino, encaminha o trace
            else:
                msg['hops'].append(self.host)
                self.forwardMessage(msg)


    def sendTrace(self, ip):
        update = {'type': 'trace', 'source': self.host, 'destination': ip, 'hops': []}
        update['hops'].append(update['source'])
        self.sock.sendto(json.dumps(update).encode(), (self.findNextHop(ip), self.port))


    #? Confere essa função pfvr \/
    def findNextHop(self, destination):
        nextHops = self.routingTable[destination]['hops']
        # Se tiver mais de um hop possível faz o balanceamento de carga
        # alternando entre os hops
        if len(nextHops) > 1:
            nextHop = nextHops[self.routingTable[destination]['nextHop']]
            self.routingTable[destination]['nextHop'] += 1
            if self.routingTable[destination]['nextHop'] > len(nextHops) - 1:
                self.routingTable[destination]['nextHop'] = 0
            return nextHop[0]

        else:
            return nextHops[0] #? ou seria nextHops[0][0] ??


    # thread que controla recebimento de mensagens de update
    def recvThread(self):
        while self.running.isSet():
            try:
                data, sourceAddr = self.sock.recvfrom(1024)
                self.parseMessage(data, sourceAddr)
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
