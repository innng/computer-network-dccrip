#!/usr/bin/env python3

import argparse
import socket
import json
import sys


def main():
    # testa número mínimo de argumentos
    if len(sys.argv) < 4:
        sys.exit('Incorrect number of parameters!')

    # recebe parâmetros por linha de comando
    parser = argparse.ArgumentParser('Parâmetros do roteador')
    parser.add_argument('--addr', type=str, required=True,
                        help='IP do roteador')
    parser.add_argument('--update-period', type=float, required=True,
                        help='Período entre envio de mensagens de update')
    parser.add_argument('--startup-commands', type=str,
                        required=False, help='Arquivo de comandos')

    args = parser.parse_args()
    print(args)


# classe que trata todos aspectos do roteador
class Router:
    # socket
    sock = None
    # endereço de IP do roteador
    host = None
    # peso das arestas
    weight = None
    # tabela de rotas conhecidas
    routes = None
    # porta padrão
    port = 55151

    # inicializa roteador
    def __init__(self, h, w):
        pass

    # envia mensagens via socket
    def send(self):
        pass

    # recebe mensagens via socket
    def get(self):
        pass

    # monta mensagem em formato JSON
    def message(self, d, t, pl=None, dist=None, hp=None):
        msg = {'source': self.host,
               'destination': d,
               'type': t
               }

        if t is 'data':
            msg.update({'payload': pl})
        elif t is 'update':
            msg.update({'distances': dist})
        elif t is 'trace':
            hp.append(self.host)
            msg.update({'hops': hp})

        return msg

    # calcula rotas mais curtas
    def calcRoutes(self):
        pass

    # tratamento de erros
    def logExit(self, msg):
        self.sock.close()
        sys.exit(msg)


if __name__ == "__main__":
    main()
