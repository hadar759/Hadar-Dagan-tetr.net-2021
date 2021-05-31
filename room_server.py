import pickle
import socket
import threading
import time
from select import select
from typing import List

from requests import get

from database.db_post_creator import DBPostCreator
from database.server_communicator import ServerCommunicator
from game_server import GameServer


class RoomServer:
    SERVER_PORT = 44444

    def __init__(
        self,
        outer_ip: str,
        inner_ip: str,
        default: bool,
        room_name: str,
        min_apm: int = 0,
        max_apm: int = 999,
        private: bool = False,
        admin="",
    ):
        self.client_list: List[socket.socket] = []
        self.players = {}
        self.reversed_players = {}
        self.players_wins = {}
        self.ready_clients = []
        self.responses_list = []
        self.games: List[GameServer] = []
        self.data_dict = {}
        self.game_running = False
        self.room_name = room_name
        self.admin = admin
        self.default = default
        self.current_game_port = self.SERVER_PORT + 2

        self.server_socket = socket.socket()
        self.outer_ip = outer_ip
        self.inner_ip = inner_ip
        self.min_apm = min_apm
        self.max_apm = max_apm
        self.private = private
        self.server_communicator = ServerCommunicator()

        self.create_server_db()

    def create_server_db(self):
        """Add the room to the database"""
        self.server_communicator.create_room(
            DBPostCreator.create_room_post(
                self.default,
                self.room_name,
                self.outer_ip,
                self.inner_ip,
                self.min_apm,
                self.max_apm,
                self.private,
            )
        )

    def run(self):
        try:
            # listen_ip = get_inner_ip() if self.default else self.outer_ip
            listen_ip = self.inner_ip
            self.server_socket.bind((listen_ip, self.SERVER_PORT))
            self.server_socket.listen(1)
            # Always accept new clients
            threading.Thread(target=self.connect_clients, daemon=True).start()
            threading.Thread(target=self.check_winners, daemon=True).start()
            while True:
                if not self.client_list:
                    continue
                read_list, write_list, _ = select(
                    self.client_list, self.client_list, []
                )
                self.handle_read(read_list)
                self.handle_write(write_list)
                if len(self.ready_clients) < 2:
                    continue
                else:
                    # Start the game
                    game_server = GameServer(listen_ip, self.current_game_port, self.ready_clients)
                    self.games.append(game_server)
                    threading.Thread(target=game_server.run).start()

                    # time.sleep(2)
                    time_at_start = str(time.time())
                    # Notify each client of game start
                    for client in self.ready_clients:
                        # self.notify_client_of_game_start(client, time_at_start, self.current_game_port)
                        threading.Thread(
                            target=self.notify_client_of_game_start,
                            args=(
                                client,
                                time_at_start,
                                self.current_game_port
                            ),
                        ).start()

                    self.current_game_port += 1

                    self.ready_clients = []
                    # self.client_list = new_clients

        except Exception as e:
            print("bruhhh", e)
            # Delete the server from the db
            self.server_communicator.delete_server_by_ip(self.outer_ip, self.inner_ip)
            self.create_server_db()
            self.run()

    def check_winners(self):
        while True:
            games_to_remove = []
            for game in self.games:
                if game.winner:
                    self.players_wins[game.winner] += 1
                    print(self.players_wins)
                    games_to_remove.append(game)
                    for client in self.client_list:
                        client.send(f"Win%{game.winner}".encode())
            for game in games_to_remove:
                self.games.remove(game)

    def remove_server(self):
        self.server_communicator.remove_room(self.room_name)

    @staticmethod
    def notify_client_of_game_start(client, time_at_start, server_port):
        client.send(f"Started%{time_at_start},{server_port}".encode())

    def handle_read(self, read_list: List[socket.socket]):
        """Handles reading from the clients"""
        for client in read_list:
            data = client.recv(25600)

            try:
                data = data.decode()
            # Info from the last game
            except UnicodeDecodeError:
                print("skipped")
                continue

            self.handle_message(data, client)

    def handle_message(self, data, client):
        # The client pressed the ready button
        if data[0: len("Ready%")] == "Ready%":
            if client in self.ready_clients:
                self.ready_clients.remove(client)
            else:
                self.ready_clients.append(client)

        # Client disconnected
        elif data == "disconnect":
            closed = False
            # This was the admin
            if self.players[client] == self.admin:
                self.remove_server()
                closed = True
            self.client_list.remove(client)
            player_name = self.players[client]
            self.players.pop(client)
            if client in self.ready_clients:
                self.ready_clients.remove(client)
            self.players_wins.pop(player_name)

            for other_client in self.client_list:
                text_to_send = "closed" if closed else f"!{player_name}"
                other_client.send(text_to_send.encode())
            if closed:
                quit()
            # Update the removed player in the database
            threading.Thread(target=self.update_player_num).start()
            return

        elif data == self.players[client]:
            return

        # Send the message to every client
        for other_client in self.client_list:
            self.data_dict[other_client] = data.encode()

    def handle_write(self, write_list: List[socket.socket]):
        """Handles writing from the client"""
        # Send every client their foe's screen
        for client in write_list:
            foe_data = self.data_dict.get(client)
            # A screen is available to send
            if foe_data:
                self.data_dict.pop(client)
                if foe_data.decode() != "got info":
                    client.send(foe_data)

    def connect_clients(self):
        while True:
            client, addr = self.server_socket.accept()
            if client in self.client_list:
                continue

            # Send the client the player name list
            client.send(pickle.dumps(self.players_wins))
            # Receive ok/declination from client
            msg = ""
            ok = client.recv(1024).decode()
            if ok[0 : len("Declined%")] == "Declined%":
                msg = f"{ok[len('Declined%'):]} declined an invitation"
            # The client declined an invitation
            if msg:
                self.handle_message(msg, client)
                return

            # Send the client all ready players
            ready_players = [self.players[client] for client in self.ready_clients]
            client.send(pickle.dumps(ready_players))

            # Add the client to the relevant lists
            self.client_list.append(client)
            name = client.recv(1024).decode()
            self.players[client] = name
            self.reversed_players[name] = client
            self.players_wins[name] = 0

            for client in self.client_list:
                client.send(name.encode())

            threading.Thread(target=self.update_player_num).start()

    def update_player_num(self):
        print(len(self.client_list))
        self.server_communicator.update_player_num(
            self.outer_ip, self.inner_ip, len(self.client_list)
        )


def get_outer_ip():
    return get("https://api.ipify.org").text


def get_inner_ip():
    return socket.gethostbyname(socket.gethostname())


if __name__ == "__main__":
    outer_ip = get_outer_ip()
    inner_ip = get_inner_ip()
    print("server starts on", outer_ip, inner_ip)
    server = RoomServer(outer_ip, inner_ip, True, "Default room")
    server.run()
