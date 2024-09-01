import socket
import logging
import signal
import sys

from common.utils import Bet, store_bets

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
            s = ""

            while True:
                b = client_sock.recv(1024)
                if not b:
                    break

                s += b.decode('utf-8').strip()

                idx = s.find(';')
                if idx == -1:
                    continue                

                bet = Bet.__from_string__(s[:idx])
                store_bets([bet])
                s = s[idx+1:]
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
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
