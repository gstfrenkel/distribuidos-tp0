import socket
import logging
import signal
import sys

from common.utils import Bet, store_bets

OK = b'0'
ERR = b'1'

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.clients = []

        signal.signal(signal.SIGTERM, self.__handle_exit_signal)
        signal.signal(signal.SIGINT, self.__handle_exit_signal)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while True:
            client_sock = self.__accept_new_connection()
            self.clients.append(client_sock)
            self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            socket_name = client_sock.getpeername()
            while True:
                b = bytes()
                bytes_read = 0

                batch_size = int.from_bytes(client_sock.recv(2), "big")
                if not batch_size:
                    break

                while bytes_read < batch_size:
                    b += client_sock.recv(batch_size - bytes_read)
                    bytes_read = len(b)

                bets_decoded = b.decode('utf-8').strip().split(';')
                try:
                    bets = [Bet.__from_string__(bet) for bet in bets_decoded]
                    store_bets(bets)
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets_decoded)}')
                    client_sock.send(OK)
                except:
                    logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets_decoded)}')
                    client_sock.send(ERR)
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            logging.info(f"action: conexión_cerrada | result: success | client: {socket_name}")
            client_sock.close()
            self.clients.remove(client_sock)

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def __handle_exit_signal(self, signum, frame):
        """
        Gracefully shuts down server and its open connections.
        """
        logging.info(f'action: signal_received | result: success | signal: {signum}')
        for client in self.clients:
            client.close() 
            logging.info('action: closed_client | result: success')
        sys.exit(0)
