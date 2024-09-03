import socket
import logging
import signal
import sys
from collections import defaultdict
from common.utils import Bet, store_bets, load_bets, has_won

OK = b'0'
ERR = b'1'

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.listen_backlog = listen_backlog
        self.finished_clients = 0
        self.clients = {}

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
            self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            socket_name = client_sock.getpeername()

            self.__recv_bets(client_sock)
            self.finished_clients += 1

            if self.finished_clients != self.listen_backlog:
                return

            self.__send_results()
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        #finally:
        #    logging.info(f"action: conexión_cerrada | result: success | client: {socket_name}")
        #    client_sock.close()
        #    self.clients.remove(client_sock)

    def __recv_bets(self, client_sock):
        agency = int.from_bytes(client_sock.recv(1), "big")
        self.clients[agency] = client_sock
        client_sock.send

        while True:
            b = bytes()
            bytes_read = 0

            batch_size = int.from_bytes(client_sock.recv(2), "big")
            if batch_size == 0:
                return

            while bytes_read < batch_size:
                b += client_sock.recv(batch_size - bytes_read)
                bytes_read = len(b)

            bets_decoded = b.decode('utf-8').strip().split(';')
            try:
                bets = [Bet.__from_string__(agency, bet) for bet in bets_decoded]
                store_bets(bets)
                #logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets_decoded)}')
                client_sock.send(OK)
            except:
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets_decoded)}')
                client_sock.send(ERR)

    def __send_results(self):
        winners_by_agency = defaultdict(bytes)

        logging.info('action: sorteo | result: success')

        winners = [bet for bet in load_bets() if has_won(bet)]
        for bet in winners:
            winners_by_agency[bet.agency] += int(bet.document).to_bytes(4, "big", signed=False)

        for client_id, bets in winners_by_agency.items():
            client_sock = self.clients.get(client_id)

            bytes_to_send = len(bets)
            bytes_sent = 0

            b = bytes_to_send.to_bytes(2, "big", signed=False) + bets

            while bytes_to_send > bytes_sent:
                try:
                    bytes_sent += client_sock.send(b[bytes_sent:])
                except:
                    logging.error(f"action: ganadores_enviados | result: fail | client: {client_id}")
                    break

            try:
                client_sock.recv(1)
                logging.info(f"action: conexión_cerrada | result: success | client: {client_id}")
            except Exception as e:
                logging.error(f"action: conexión_cerrada | result: fail | client: {client_id} | error: {e}")
                pass
            finally:
                client_sock.close()
                del self.clients[client_id]

        self.finished_clients = 0


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
        for client in self.clients.values():
            client.close()
            logging.info('action: closed_client | result: success')
        sys.exit(0)
