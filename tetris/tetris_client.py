import socket
from tetris.tetris_game import TetrisGame


class TetrisClient:
    """The tetris server"""

    DST_PORT = 44444

    def __init__(self, tetris_game: TetrisGame, server_ip: str):
        self.client_socket = socket.socket()
        self.tetris_game = tetris_game
        self.server_ip = server_ip

    def connect_to_server(self):
        """Connects the socket to a server"""
        self.client_socket.connect((self.server_ip, self.DST_PORT))

    def run(self):
        """Setup and start the socket and the tetris game"""
        self.connect_to_server()
        self.client_socket.send(str(0).encode())
        self.tetris_game.client_socket = self.client_socket
        self.tetris_game.run()
