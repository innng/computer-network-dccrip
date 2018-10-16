import socket


def main():
    print()


class ClientSocket:
    sock = None
    addr = None

    def __init__(self, hp):
        # separa IP e porto
        aux = hp.split(':')
        host = aux[0]
        port = int(aux[1])
        # salva informações em tupla
        self.addr = (host, port)

        try:
            # abre socket para comunicação via UDP
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as error_msg:
            self.logExit(error_msg)

    # envia mensagem em bytes para addr
    def send(self, data):
        try:
            self.sock.sendto(data, self.addr)
        except socket.error as error_msg:
            self.logExit(error_msg)

    # recebe um tamanho fixo de bytes
    def get(self, bytes):
        try:
            msg, address = self.sock.recvfrom(bytes)
        except socket.error as error_msg:
            self.logExit(error_msg)

        return msg

        # fecha socket
    def closeSocket(self):
        self.sock.close()

    # tratamento de erros
    def logExit(self, msg):
        self.sock.close()
sys.exit(msg)

if __name__ == "__main__":
    main()