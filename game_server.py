import pickle
import socket
import threading
import time
from select import select
from typing import List

from requests import get


class GameServer:
    def __init__(self, listen_ip: str, port: int, client_list: List[socket.socket]):
        self.client_list: List[socket.socket] = client_list
        self.data_dict = {}
        self.players = {}
        self.game_running = True

        self.server_socket = socket.socket()
        self.listen_ip = listen_ip
        self.port = port
        self.winner = ""

    def run(self):
        self.server_socket.bind((self.listen_ip, self.port))
        self.server_socket.listen(1)
        # Connect all the clients playing
        self.connect_clients()
        # Pass information between the players
        while self.game_running:
            read_list, write_list, _ = select(self.client_list, self.client_list, [])
            self.handle_read(read_list)
            self.handle_write(write_list)
        self.server_socket.close()
        return self.winner

    def handle_read(self, read_list: List[socket.socket]):
        """Handles reading from the clients"""
        for client in read_list:
            data = client.recv(25600)
            try:
                data = pickle.loads(data)
            except EOFError:
                print("data", data.decode())
                self.game_running = False
                continue

            # Game ended, someone won
            if data[0] == "W":
                self.data_dict = {}
                for other_client in self.client_list:
                    if other_client is client:
                        continue
                    other_client.send(pickle.dumps(["Win", 0, 0]))
                    self.winner = self.players[other_client]
                self.game_over()
                return

            # Send the screen from one client to another
            else:
                for other_client in self.client_list:
                    if other_client is client:
                        continue
                    self.data_dict[other_client] = pickle.dumps(data)

    def game_over(self):
        """End the game"""
        self.game_running = False

    def handle_write(self, write_list: List[socket.socket]):
        """Handles writing from the client"""
        # Send every client their foe's screen
        for client in write_list:
            foe_data = self.data_dict.get(client)
            # A screen is available to send
            if foe_data:
                self.data_dict.pop(client)
                client.send(foe_data)

    def connect_clients(self):
        players = len(self.client_list)
        for _ in range(players):
            client, addr = self.server_socket.accept()
            name = client.recv(1024).decode()
            client.send("ok".encode())
            self.players[client] = name
            self.client_list.append(client)
            self.client_list = [
                sock for sock in self.client_list if sock.getsockname()[1] == self.port
            ]


def get_outer_ip():
    return get("https://api.ipify.org").text


def get_inner_ip():
    return socket.gethostbyname(socket.gethostname())


if __name__ == "__main__":
    outer_ip = get_outer_ip()
    inner_ip = get_inner_ip()
    print("server starts on", outer_ip, inner_ip)
    server = GameServer(outer_ip, inner_ip, True, "test room")
    # Add the room to the database
    # server.server_communicator.create_room(DBPostCreator.create_db_post(ip))
    server.run()
