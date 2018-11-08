#!/usr/bin/env python3

import threading
import argparse
import socket
import json
import sys

import pprint


class Router:
    port = 55151        # porta padrão
    sock = None         # socket UDP
    running = None      # indica se roteador está executando
    linkTable = {}      # tabela de links
    routingTable = {}   # tabela de rotas

    host = ''           # endereço de IP do roteador
    tout = 0            # período de alterações
    updateTimer = None  # timer para envio de mensagens de update

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
        self.updateTimer = self.setTimer(self.controlPanel)
        self.updateTimer.start()

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
            self.sendTrace(cmd[1])

        elif cmd[0] == 'quit':
            self.running.clear()
            self.updateTimer.cancel()

        elif cmd[0] == 'log':
            print('links -->',end=" ")
            pprint.pprint(self.linkTable)
            print('rotas -->',end=" ")
            pprint.pprint(self.routingTable)

        else:
            print('Comando inválido')

    # adiciona novo vizinho à tabela de links
    def addLink(self, ip, weight):
        self.linkTable[ip] = {}
        self.linkTable[ip]['weight'] = int(weight)
        self.linkTable[ip]['ttl'] = 4

        self.addRoute(ip, ip, weight)

    # remove vizinho
    def rmvLink(self, ip):
        print('rmvLink deleted node', ip)
        del self.linkTable[ip]

        # testa se o ip está na tabela como destino
        if ip in self.routingTable:
            del self.routingTable[ip]

        # remove todos os caminhos que passavam por esse ip
        self.rmvRoute(ip)

    # adiciona um caminho à tabela de roteamento
    def addRoute(self, ip, hop, weight):
        self.routingTable[ip] = {}
        self.routingTable[ip]['hops'] = []
        self.routingTable[ip]['hops'].append(hop)

        self.routingTable[ip]['weight'] = int(weight)
        if ip != hop:
            self.routingTable[ip]['weight'] += self.linkTable[hop]['weight']

        self.routingTable[ip]['nextHop'] = 0

    # remove um caminho
    def rmvRoute(self, ip, safe=[]):
        change = False
        # remove todos os caminhos que eram possíveis via ip
        ips = []
        for i in self.routingTable:
            # testa se o gateway pode ser removido daquele ip
            if i not in safe:
                change = True
                if ip in self.routingTable[i]['hops']:
                    self.routingTable[i]['hops'].remove(ip)

            # caminho inviável
            if len(self.routingTable[i]['hops']) == 0:
                ips.append(i)

        # remove os nodos inalcançáveis
        for i in range(len(ips)):
            print('rmvRoute deleted node', ip)
            del self.routingTable[ips[i]]

        return change

    # atualiza um caminho existente
    def updateRoute(self, ip, hop, weight):
        weight += self.linkTable[hop]['weight']
        change = False

        # se custo é menor, substitui
        if self.routingTable[ip]['weight'] > weight:
            print('updateRoute deleted node', ip)
            change = True
            del self.routingTable[ip]
            self.addRoute(ip, hop, weight)
        # se custo é maior, ignora
        elif self.routingTable[ip]['weight'] < weight:
            return change
        # se custo é igual, adiciona gateway
        else:
            if hop not in self.routingTable[ip]['hops']:
                change = True
                self.routingTable[ip]['hops'].append(hop)

        return change

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
            msg['hops'] = []
            msg['hops'].append(self.host)

        return msg

    # envia mensagem de update
    def sendUpdate(self):
        updMsg = None
        for ip in self.linkTable:
            distances = self.buildDistanceDict(ip)
            updMsg = self.buildMessage('update', self.host, ip, dist=distances)
            debugPrint = updMsg
            updMsg = json.dumps(updMsg)
            pkg = bytes(updMsg, 'ascii')
            if updMsg != None:
                print("Update sent: ", end='')
                pprint.pprint(debugPrint)
            self.sock.sendto(pkg, (ip, self.port))

        # self.updateTimer.cancel()
        # self.updateTimer = self.setTimer(self.sendUpdate)
        # self.updateTimer.start()

        # # diminui o ttl dos vizinhos
        # self.controlLinks()

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
        # acha o próximo hop usando balanceamento de cargas
        hop = self.findNextHop(ip)

        # envia mensagem
        msg = json.dumps(msg)
        pkg = bytes(msg, 'ascii')
        self.sock.sendto(pkg, (hop, self.port))

    # thread que controla recebimento de comandos via teclado
    def cliThread(self):
        while self.running.isSet():
            line = input('~ ')
            self.parseLinkCommand(line)

    # trata as mensagens recebidas
    def parseMessage(self, data, sourceAddr):
        msg = json.loads(data.decode())
        if msg['type'] == 'update':
            print("Update received: ", end='')
            pprint.pprint(msg)
            # Pega os IPs e pesos do vetor distances da msg de update
            for ip, weight in msg['distances'].items():
                # Já está na tabela de roteamento
                if ip in self.routingTable:
                    # Ve se o link existe na tabela
                    if sourceAddr[0] in self.linkTable:
                        currentWeight = int(self.linkTable[sourceAddr[0]]['weight'])
                        knownWeight = self.routingTable[ip]['weight']
                        if (weight + currentWeight) < knownWeight:
                            self.routingTable[ip]['weight'] = int(weight) + currentWeight
                            self.routingTable[ip]['hops'] = []
                            self.routingTable[ip]['hops'].append([sourceAddr[0]]['weight'])
                        elif (weight + currentWeight) == knownWeight:
                            hopIPs = []
                            for hopIP in self.routingTable[ip]['hops']:
                                hopIPs.append(hopIP)
                            if sourceAddr[0] not in hopIPs:
                                self.routingTable[ip]['hops'].append(sourceAddr[0])
                # Não está na tabela de roteamento
                else:
                    self.routingTable[ip] = {}
                    self.routingTable[ip]['weight'] = int(weight) + int(self.linkTable[sourceAddr[0]]['weight'])
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

        # mensagem do tipo dados
        elif msg['type'] == 'data':
            if msg['destination'] == self.host:
                # esse nó é o destino, mensagem recebida.
                print("Mensagem recebida:", msg['payload'])
            else:
                self.forwardMessage(msg)

        elif msg['type'] == 'trace':
            # esse nó é o destino do trace
            if msg['destination'] == self.host:

                traceBack = self.buildMessage('data', self.host, msg['source'], json.dumps(msg))
                self.forwardMessage(traceBack)
            # esse não é o nó destino, encaminha o trace
            else:
                msg['hops'].append(self.host)
                self.forwardMessage(msg)

    # envia mensagem de trace
    def sendTrace(self, ip):
        update = self.buildMessage('trace', self.host, ip)
        self.sock.sendto(json.dumps(update).encode(), (self.findNextHop(ip), self.port))

    # faz o balanceamento de cargas
    def findNextHop(self, dest):
        # separa por qual gateway deve passar a mensagem
        nextHop = self.routingTable[dest]['nextHop']
        # separa o gateway pelo qual essa mensagem vai passar
        hop = self.routingTable[dest]['hops'][nextHop]

        # incrementa o hop para o balanceamento de cargas
        self.routingTable[dest]['nextHop'] += 1
        # se passou o número de gateways da lista, reseta contador
        if self.routingTable[dest]['nextHop'] > len(self.routingTable[dest]['hops']) - 1:
            self.routingTable[dest]['nextHop'] = 0

        return hop

    # thread que controla recebimento de mensagens de update
    def recvThread(self):
        while self.running.isSet():
            try:
                data, sourceAddr = self.sock.recvfrom(1024)
                self.parseMessage(data, sourceAddr)
            except BlockingIOError:
                pass

    def controlPanel(self):
        self.sendUpdate()
        self.controlLinks()

        self.updateTimer = self.setTimer(self.controlPanel)
        self.updateTimer.start()

    # controla os vizinhos baseado no ttl
    def controlLinks(self):
        # diminui o ttl de cada vizinho
        rmv = []
        for ip in self.linkTable:
            self.linkTable[ip]['ttl'] -= 1

            if self.linkTable[ip]['ttl'] == 0:
                rmv.append(ip)

        # remove vizinhos que estouraram o ttl
        for ip in rmv:
            self.rmvLink(ip)

    # retorna um objeto Timer
    def setTimer(self, fn, argList=[]):
        timer = threading.Timer(self.tout, fn, argList)
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
