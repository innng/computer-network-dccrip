#!/usr/bin/env python3

import struct
import socket
import sys
import argparse
import threading
import time
import json
import math
import os

class Router(object):

    """docstring for Router"""

    # Enlaces físicos
    links = {}

    # Tabela de roteamento
    routingTable = {}

    running = True
    UDP_PORT = 55151
    sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM, 0) # UDP

    lock = threading.Lock()

    def __init__(self, addr, period, startup):
        super(Router, self).__init__()
        self.addr = addr
        self.period = period
        self.startup = startup

    def start(self):
        # Start router threads
        
        # CLI Thread
        try:
            cliT = threading.Thread(target=self._cliThread, args=())
            cliT.start()
        except:
            print("Error: unable to start CLI thread")  

        # # Thread to receive messsages
        try:
            recT = threading.Thread(target=self._recThread, args=())
            recT.start()
        except:
            print("Error: unable to start REC thread")

        # Thread to send update messages
        try:
            updT = threading.Thread(target=self._updThread, args=())
            updT.start()
        except:
            print("Error: unable to start UPD thread")

        # Thread to manage route timeout
        try:
            tmoT = threading.Thread(target=self._tmoThread, args=())
            tmoT.start()
        except:
            print("Error: unable to start UPD thread")

    def addLink(self, destinationAddr, weight):
        self.links[destinationAddr] = weight
        self.routingTable[destinationAddr] = {}
        self.routingTable[destinationAddr]['weight'] = int(weight)
        self.routingTable[destinationAddr]['hops'] = []
        self.routingTable[destinationAddr]['hops'].append([destinationAddr, 4]) #TTL
        self.routingTable[destinationAddr]['nextHop'] = 0

    def removeLink(self, destinationAddr):
        del self.links[destinationAddr]
        #print (self.routingTable)
        for hop in list(self.routingTable.get(destinationAddr)['hops']):
            if(hop[0] == destinationAddr):
                self.routingTable.get(destinationAddr)['hops'].remove(hop)
        
        if(len(self.routingTable.get(destinationAddr)['hops']) == 0): # Removeu a única rota disponível
            self.routingTable.get(destinationAddr)['weight'] = math.inf

        self.sendUpdate()

        #print (self.routingTable)

    def _processInput(self, inputString):
        inputParts = inputString.split(' ')
        if(inputParts[0] == "add"):
            self.addLink(inputParts[1], inputParts[2])
            

        elif(inputParts[0] == "del"):
            self.removeLink(inputParts[1])
            
        elif(inputParts[0] == "trace"):
            self._sendTrace(inputParts[1])
        elif(inputParts[0] == "quit"):
            os._exit(1)
        else:
            print("Invalid command. Please, try again.")                

    def _sendTrace(self, destination):
        UDP_MESSAGE = {}
        UDP_MESSAGE['type'] = 'trace'
        UDP_MESSAGE['source'] = self.addr
        UDP_MESSAGE['destination'] = destination
        UDP_MESSAGE['hops'] = []
        UDP_MESSAGE['hops'].append(self.addr)
        self.sock.sendto(json.dumps(UDP_MESSAGE).encode(), (self._nextHop(destination), self.UDP_PORT))

    def _cliThread(self):
        # Command Line Interface

        # Le arquivo se especificado
        if(self.startup != None):
            file = open(self.startup, 'r')
            for line in file:
                print("> ", line)
                self._processInput(line)

        inputString = ""
        while(inputString != "quit"):
            inputString = input('> ')
            self._processInput(inputString)
            

        self.running = False

        return

    def _nextHop(self, destination):
        nextHops = self.routingTable[destination]['hops']
        if(len(nextHops) > 1): # Load balancing
            nextHop = nextHops[self.routingTable[destination]['nextHop']]
            self.routingTable[destination]['nextHop'] += 1
            if(self.routingTable[destination]['nextHop'] > len(nextHops)-1):
                self.routingTable[destination]['nextHop'] = 0 # Volta para a primeira rota
            return nextHop[0]

        else:
            return nextHops[0][0]


    def _recThread(self):
        
        self.sock.bind((self.addr, self.UDP_PORT))

        while self.running :
            data, source_addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
            json_data = json.loads(data.decode())
            
            if(json_data['type'] == 'update'):
                #print("Update from ", source_addr)
                # Atualizar tabela de roteamento
                for key,value in json_data['distances'].items():
                    if(key in self.routingTable):
                        #Verifica se o link existe
                        if(source_addr[0] in self.links):
                            if(value + int(self.links[source_addr[0]]) < self.routingTable[key]['weight']):
                                self.routingTable[key]['weight'] = int(value) + int(self.links[source_addr[0]])
                                self.routingTable[key]['hops'] = []
                                self.routingTable[key]['hops'].append([source_addr[0], 4])
                            elif(value + int(self.links[source_addr[0]]) == self.routingTable[key]['weight']):
                                hopsAddr = []
                                for hop in self.routingTable[key]['hops']:
                                    hopsAddr.append(hop[0])
                                if(source_addr[0] not in hopsAddr):
                                    self.routingTable[key]['hops'].append([source_addr[0], 4])
                    else: 
                        self.routingTable[key] = {}
                        self.routingTable[key]['weight'] = int(value) + int(self.links[source_addr[0]])
                        self.routingTable[key]['hops'] = []
                        self.routingTable[key]['hops'].append([source_addr[0], 4])
                #Reseta TTL
                for key,value in json_data['distances'].items():
                    routingTableRow = self.routingTable[key]
                    for hop in routingTableRow['hops']:
                        if(hop[0] == source_addr[0]):
                            hop[1] = 4

                # print("routingTable:")
                # print(self.routingTable)
            elif(json_data['type'] == 'data'):
                if(json_data['destination'] == self.addr): # Pacote chegou ao destino
                    print("# Mensagem recebida por ", json_data['source'])
                    print(json_data['payload'])
                else: # Encaminha
                    nextHop = self._nextHop(json_data['destination'])
                    #print("Fowrading message from ", source_addr[0], " to ", nextHop)
                    self.sock.sendto(json.dumps(json_data).encode(), (nextHop, self.UDP_PORT))
            elif(json_data['type'] == 'trace'):
                if(json_data['destination'] == self.addr): # Trace chegou ao destino
                    #print("Received trace")
                    #print(json_data)
                    # Envia o pacote de trace de volta para o solicitante 
                    UDP_MESSAGE = {}
                    UDP_MESSAGE['type'] = 'data'
                    UDP_MESSAGE['source'] = self.addr
                    UDP_MESSAGE['destination'] = json_data['source']
                    UDP_MESSAGE['payload'] = json_data
                    nextHop = self._nextHop(json_data['source'])
                    self.sock.sendto(json.dumps(UDP_MESSAGE).encode(), (nextHop, self.UDP_PORT))
                else: # Ecaminha trace
                    nextHop = self._nextHop(json_data['destination'])
                    #print("Fowrading trace to ", json_data['destination'])
                    json_data['hops'].append(self.addr)
                    self.sock.sendto(json.dumps(json_data).encode(), (nextHop, self.UDP_PORT))


    def sendUpdate(self):
        UDP_MESSAGE = {}
        UDP_MESSAGE['type'] = 'update'
        UDP_MESSAGE['source'] = self.addr
        for neighbour in self.links.keys():
            UDP_MESSAGE['distances'] = {}
            UDP_MESSAGE['destination'] = neighbour
            for key, value in self.routingTable.items():
                if(key != neighbour): # Split horizon
                    UDP_MESSAGE['distances'][key] = value['weight']
            UDP_MESSAGE['distances'][self.addr] = 0
            self.sock.sendto(json.dumps(UDP_MESSAGE).encode(), (neighbour, self.UDP_PORT))

    def _updThread(self):
        while(self.running):            
            self.sendUpdate()
            time.sleep(int(self.period))

    def _tmoThread(self):
        
        while(self.running):
            time.sleep(int(self.period))            
            with self.lock:
                for key, value in self.routingTable.items():
                    for item in list(value['hops']):
                        ttl = int(item[1])
                        item[1] = ttl - 1    

                        if(item[1] == 0): # Timeout na rota
                            value['hops'].remove(item)
                            value['weight'] = math.inf
                            if(item[0] in self.links):
                                del self.links[item[0]]
                # print("Timeout checked")
                # print(self.routingTable)
            

def main():
    
    # Read arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', help="IPv4 address to listen on (usually inside 127.0.1.0/24)", required=True)
    parser.add_argument('--update-period', help="Period between updates [2.0]", required=True)
    parser.add_argument('--startup', help="File to read startup commands from")

    args = parser.parse_args()

    router = Router(args.addr, args.update_period, args.startup)
    router.start()

    #print(args)    

if __name__ == '__main__':
    main()
