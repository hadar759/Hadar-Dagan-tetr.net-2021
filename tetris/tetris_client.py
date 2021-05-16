import pickle
import socket
from tetris.tetris_game import TetrisGame


class TetrisClient:
    """The tetris server"""

    DST_PORT = 44444

    def __init__(
        self, tetris_game: TetrisGame, server_ip: str, client_socket: socket.socket
    ):
        # self.client_socket = socket.socket()
        self.client_socket = client_socket
        self.tetris_game = tetris_game
        self.server_ip = server_ip

    def connect_to_server(self):
        """Connects the socket to a server"""
        self.client_socket.connect((self.server_ip, self.DST_PORT))

    def run(self):
        """Setup and start the socket and the tetris game"""
        # self.connect_to_server()
        data = pickle.dumps([[], 0, self.tetris_game.user["skin"]])
        self.client_socket.send(data)
        self.tetris_game.server_socket = self.client_socket
        self.tetris_game.run()
