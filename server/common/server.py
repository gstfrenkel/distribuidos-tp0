import socket
import logging
import signal
import sys
from collections import defaultdict
from multiprocessing import Barrier, Process, Condition, Queue, active_children
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

        self.recv_barrier = Barrier(listen_backlog + 1)
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
        winners_queue = Queue()

        Process(target = self.__get_winners, args=(winners_queue,)).start()

        while True:
            client_sock = self.__accept_new_connection()
            handler = Process(target = self.__handle_client_connection, args=(client_sock, winners_queue,))
            handler.start()
            
    def __handle_client_connection(self, client_sock, winners_queue):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        signal.signal(signal.SIGTERM, self.__handle_process_exit_signal)

        try:
            agency = int.from_bytes(client_sock.recv(1), "big")
            self.clients[agency] = client_sock

            self.__recv_bets(client_sock, agency)

            self.recv_barrier.wait()

            self.__send_results(client_sock, agency, winners_queue)
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")

    def __recv_bets(self, client_sock, agency):
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

    def __send_results(self, client_sock, agency, winners_queue):
        winners = winners_queue.get()

        b = b''.join(int(bet.document).to_bytes(4, "big", signed=False) for bet in winners if bet.agency == agency)
        winners_len = len(b)
        b = winners_len.to_bytes(2, "big", signed=False) + b

        bytes_to_send = winners_len + 2
        bytes_sent = 0
        while bytes_to_send > bytes_sent:
            try:
                bytes_sent += client_sock.send(b[bytes_sent:])
            except:
                logging.error(f"action: ganadores_enviados | result: fail | client: {agency}")
                break

        try:
            client_sock.recv(1)
            logging.info(f"action: conexión_cerrada | result: success | client: {agency}")
        except Exception as e:
            logging.error(f"action: conexión_cerrada | result: fail | client: {agency} | error: {e}")
            pass
        finally:
            client_sock.close()
            del self.clients[agency]

    def __get_winners(self, winners_queue):
        signal.signal(signal.SIGTERM, self.__handle_process_exit_signal)

        while True:
            self.recv_barrier.wait()

            winners = [bet for bet in load_bets() if has_won(bet)]

            logging.info('action: sorteo | result: success')

            self.recv_barrier = Barrier(self.listen_backlog + 1)

            for _ in range(self.listen_backlog):
                winners_queue.put(winners)

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
        for p in active_children():
            p.terminate()
        for client in self.clients.values():
            client.close()
            logging.info('action: closed_client | result: success')
        sys.exit(0)

    def __handle_process_exit_signal(self, signum, frame):
        sys.exit(0)
