import pickle
import socket
from tetris.tetris_game import TetrisGame


class TetrisClient:
    """The tetris server"""

    DST_PORT = 44444

    def __init__(
        self, tetris_game: TetrisGame, server_ip: str, server_port: int, username: str
    ):
        self.client_socket = socket.socket()
        self.tetris_game = tetris_game
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = username

    def connect_to_server(self):
        """Connects the socket to a server"""
        print(f"Connecting to {self.server_ip}:{self.server_port}")
        self.client_socket.connect((self.server_ip, self.server_port))
        self.client_socket.send(self.username.encode())

    def run(self):
        """Setup and start the socket and the tetris game"""
        self.connect_to_server()
        # print(self.client_socket.recv(1024).decode())
        self.client_socket.recv(1024)
        data = pickle.dumps([[], 0, self.tetris_game.user["skin"]])
        self.client_socket.send(data)
        print(self.client_socket.getpeername())
        self.tetris_game.server_socket = self.client_socket
        self.tetris_game.run()
        self.client_socket.close()
