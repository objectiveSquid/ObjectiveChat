from .client_stuff import ServerSideClient
from shared.config import SERVER_CONFIG
from .db_handler import DBWrapper

import logging
import socket
import sys


class Server:
    def __init__(self) -> None:
        self.__logger = logging.getLogger("Server")

        self.__logger.debug("Initializing server socket")
        self.__create_and_bind_socket(
            SERVER_CONFIG["connection"]["listen_address"],
            SERVER_CONFIG["connection"]["listen_port"],
        )
        self.__logger.info("Initialized server socket")

        self.__running = False
        self.__clients: list[ServerSideClient] = []
        self.__db_wrapper = DBWrapper()
        self.__logger.debug("Ensuring database tables")
        self.__db_wrapper.ensure_tables()
        self.__logger.debug("Ensured database tables")

    def run(self) -> None:
        self.__running = True

        self.__logger.info(
            "Now accepting connections on %s:%s", *self.__sock.getsockname()
        )
        while self.__running:
            try:
                new_client_sock = self.__sock.accept()[0]
            except OSError:
                self.stop()
                break

            self.__logger.info(
                "New client connection from %s:%s", *new_client_sock.getpeername()
            )
            new_client_sock.setblocking(False)
            new_client = ServerSideClient(new_client_sock, self)
            new_client.start()
            self.__clients.append(new_client)

        self.__logger.info("Stopping server")
        self.__logger.debug("Stopping all client threads")
        for client in self.__clients:
            client.stop(self.__send_quit)

    def stop(self, send_quit: bool = True) -> None:
        self.__send_quit = send_quit
        self.__running = False

    def __create_and_bind_socket(self, address: str, port: int) -> None:
        self.__sock = socket.socket()
        if sys.platform != "win32":
            self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__sock.bind((address, port))
        self.__sock.listen(SERVER_CONFIG["connection"]["accept_backlog"])
        self.__sock.setblocking(True)

    @property
    def clients(self) -> list[ServerSideClient]:
        return self.__clients

    @property
    def db_wrapper(self) -> DBWrapper:
        return self.__db_wrapper
