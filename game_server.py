import socket
import time
from select import select
from typing import List


class GameServer:
    SERVER_PORT = 44444

    def __init__(self, server_ip):
        self.client_list = []
        self.writes_to = {}
        self.responses_list = []
        self.screen_dict = {}
        self.game_running = False
        self.server_socket = socket.socket()
        self.server_ip = server_ip

    def run(self):
        self.server_socket.bind((self.server_ip, self.SERVER_PORT))
        self.server_socket.listen(1)
        self.connect_players()
        while True:
            read_list, _, _ = select(self.client_list, self.client_list, [])
            self.handle_read(read_list)
            if len(self.responses_list) < 2:
                continue
            # Game was declined by one of the clients
            elif "declined" in self.responses_list:
                break
            else:
                # Notify each client of game start
                for client in self.client_list:
                    client.send("started".encode())
            # Pass information between the players
            while self.game_running:
                read_list, write_list, _ = select(
                    self.client_list, self.client_list, []
                )
                self.handle_read(read_list)
                self.handle_write(write_list)

    def handle_read(self, read_list: List[socket.socket]):
        """Handles reading from the clients"""
        for client in read_list:
            data = client.recv(1024)
            # Waiting for game start
            if not self.game_running:
                self.responses_list.append(data.decode())
            # Maybe a better more efficient way to do this? (don't want to decode all the time)
            if data.decode() == "over":
                self.game_over()
                return
            # GAME RUNNING - Send the
            else:
                self.screen_dict[self.writes_to[client]] = data

    def game_over(self):
        """End the game"""
        self.game_running = False
        self.responses_list = []
        self.screen_dict = {}
        for client in self.client_list:
            client.send("over".encode())

    def handle_write(self, write_list: List[socket.socket]):
        """Handles writing from the client"""
        # Send every client their foe's screen
        for client in write_list:
            foe_screen = self.screen_dict.get(client)
            # A screen is available to send
            if foe_screen:
                client.send(foe_screen)

    def connect_players(self):
        """Accept the 2 players"""
        initiator, addr = self.server_socket.accept()
        self.client_list.append(initiator)
        # Accept the invitee
        accepter, addr = self.server_socket.accept()
        self.client_list.append(accepter)

        self.writes_to[initiator] = accepter
        self.writes_to[accepter] = initiator


if __name__ == "__main__":
    server = GameServer("10.100.102.17")
    server.run()
