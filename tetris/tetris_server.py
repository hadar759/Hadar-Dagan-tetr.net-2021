"""
Hadar Dagan
31.5.2020
v1.0
"""
import socket
from tetris.tetris_game import TetrisGame


class TetrisServer:
    LISTEN_IP = "0.0.0.0"
    LISTEN_PORT = 25565

    def __init__(self, tetris_game: TetrisGame):
        self.server_socket = socket.socket()
        self.tetris_game = tetris_game
        self.client_socket = None

    def initialize_socket(self):
        """Bind the server to an IP and a port and start listening"""
        self.server_socket.bind((self.LISTEN_IP, self.LISTEN_PORT))
        self.server_socket.listen(2)

    def run(self):
        """Setup and start the socket and the tetris game"""
        self.initialize_socket()
        self.client_socket, client_address = self.server_socket.accept()
        self.client_socket.send(str(0).encode())
        self.tetris_game.client_socket = self.client_socket
        self.tetris_game.run()
