import os
import subprocess
from typing import Optional, Dict, List
import time

import uvicorn
from pymongo import MongoClient
from fastapi import Depends, FastAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

app = FastAPI()
router = InferringRouter()


def get_collection():
    with open(r"./mongodb.txt", "r") as pass_file:
        pass_text = pass_file.read()
    client = MongoClient(
        pass_text
    )
    db = client["tetris"]
    collection = db["users"]
    return collection


@cbv(router)
class Server:
    SERVERS_QUERY = {"_id": 0}

    def __init__(self):
        self.user_collection: Depends = Depends(get_collection)

    @router.post("/users/rooms/player-num")
    def update_player_num(self, ip, player_num):
        self.user_collection.dependency().find_one_and_update({"ip": ip}, update={"$set": {"player_num": player_num}})

    @router.post("/users/rooms")
    def create_room(self, room: Dict):
        self.user_collection.dependency().insert_one(room)

    @router.get("/users/rooms")
    def get_rooms(self):
        rooms = self.user_collection.dependency().find({"type": "room"})
        return list(rooms)

    @router.post("/users/games")
    def add_game(self, username: str, win: bool):
        """Updates the game and win count for a user"""
        user = self.user_by_username(username)
        # Add a game played to the user's query
        new_query = {"$set": {"games": user["games"] + 1}}
        # Add a win to the user's query
        if win:
            new_query["wins"] = user["wins"] + 1
        self.user_collection.dependency().update_one(filter={"username": username}, update=new_query)

    @router.post("/users/sprint")
    def update_sprint(self, username: str, cur_time: float):
        user = self.user_by_username(username)

        user_time = user["40l"].split(":")
        old_time = 0
        # Time str to secs
        for i in range(len(user_time)):
            old_time += float(user_time[-i - 1]) * 60 ** i

        # From seconds to string
        time_format = "%S"
        if cur_time >= 60:
            time_format = "%M:" + time_format
        if cur_time >= 3600:
            time_format = "%H:" + time_format
        time_str = time.strftime(time_format, time.gmtime(cur_time)) + "." + str(cur_time).split(".")[1][:3]

        update_query = {"$set": {"40l": time_str}}
        # User score a faster best time
        if old_time == 0 or cur_time < old_time:
            self.user_collection.dependency().update_one(filter={"username": username}, update=update_query)
            return True
        return False

    @router.post("/users/marathon")
    def update_marathon(self, username: str, score: int):
        user = self.user_by_username(username)

        update_query = {"$set": {"marathon": score}}
        old_score = user["marathon"]
        # User scored a higher score
        if old_score == 0 or old_score < score:
            self.user_collection.dependency().update_one(filter={"username": username}, update=update_query)
            return True
        return False

    @router.post("/users/apm")
    def update_apm(self, username: str, apm: float):
        user = self.user_by_username(username)
        games: list = user["apm_games"]

        if len(games) > 9:
            games = games[len(games) - 9:]
        games.append(apm)
        # Calculate the avg of the past 10 games
        avg_apm = round(sum(games) / len(games), 3)

        update_query = {"$set": {"apm_games": games, "apm": avg_apm}}
        self.user_collection.dependency().update_one(filter={"username": username}, update=update_query)

    @router.post("/users/connection")
    def on_connection(self, username: str, ip: str):
        new_query = {"$set": {"ip": ip, "invite": "", "invite_ip": "", "online": True}}
        self.user_collection.dependency().update_one(
            filter={"username": username}, update=new_query
        )

    @router.get("/users/invite-ip")
    def get_invite_ip(self, username: str):
        # Get the user
        user = self.user_by_username(username)
        return user["invite_ip"]

    @router.post("/users/invites")
    def handle_invite(self, inviter: str, invitee: str, invite_ip: str):
        # Set up the new query for update:
        new_query = {"$set": {"invite": inviter, "invite_ip": invite_ip}}

        self.user_collection.dependency().update_one(
            filter={"username": invitee}, update=new_query
        )

    @router.get("/users/invites")
    def get_invite(self, username: str) -> str:
        user = self.user_by_username(username)
        return user["invite"]

    @router.get("/users/online")
    def player_online(self, username: str) -> bool:
        """Returns whether a player is online or not"""
        if self.username_exists(username):
            player = self.user_by_username(username)
            return player["online"]
        return False

    @router.post("/users/online")
    def update_online(self, username: str, online: bool):
        self.user_collection.dependency().find_one_and_update(filter={"username": username},
                                                              update={"$set": {"online": online}})

    @router.get("/users/servers")
    def get_free_server(self) -> str:
        """Returns a free server to service the client. Updates the queries accordingly."""
        servers_field = self.user_collection.dependency().find_one({"_id": 0})

        free_servers = servers_field["free_servers"]
        busy_servers = servers_field["busy_servers"]

        if len(free_servers) == 0:
            return "No server available, play a default room please."

        # Get one server from the list
        chosen_server = free_servers[0]
        busy_servers.append(chosen_server)
        # Remove the choosen server from the list
        free_servers = free_servers[1:]

        # Setup new queries for update
        new_query = {
            "$set": {"free_servers": free_servers, "busy_servers": busy_servers}
        }

        # Update the servers lists
        self.user_collection.dependency().update_one(
            filter=self.SERVERS_QUERY, update=new_query
        )

        print(free_servers)
        print(busy_servers)
        # Return the server's ip
        return chosen_server

    @router.post("/users/servers")
    def finished_using_server(self, server_ip: str):
        """Appends a server the client finished using to the free servers list"""
        servers_field = self.user_collection.dependency().find_one(self.SERVERS_QUERY)
        free_servers = servers_field["free_servers"]
        busy_servers = servers_field["busy_servers"]

        # Setup new query for update
        free_servers.append(server_ip)
        busy_servers.remove(server_ip)
        new_query = {
            "$set": {"free_servers": free_servers, "busy_servers": busy_servers}
        }

        print(free_servers)
        print(busy_servers)

        self.user_collection.dependency().update_one(
            filter=self.SERVERS_QUERY, update=new_query
        )

    @router.post("/users/outer-ip")
    def update_outer_ip(self, user_identifier: str, password: str, ip: str):
        """Updates the outer ip of a user on a new connection"""
        user = self.user_matches_password(user_identifier, password)

        new_query = {"$set": {"ip": ip}}

        self.user_collection.dependency().update_one(
            filter={"username": user["username"]}, update=new_query
        )

    @router.get("/users/len")
    def get_document_count(self) -> int:
        """Returns the number of documents in the collection. Mainly used for checking server status."""
        return self.user_collection.dependency().estimated_document_count()

    @router.post("/users")
    def create_user(self, user_field: Dict):
        """Adds a user to the db"""
        self.user_collection.dependency().insert_one(user_field)

    @router.get("/users/find")
    def user_exists(
        self,
        user_identifier: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
    ) -> bool:
        """Returns whether a user exists in the db"""
        if email:
            user_by_email = self.email_exists(email)
            return user_by_email

        if username:
            user_by_username = self.username_exists(username)
            return user_by_username

        if user_identifier:
            return self.email_exists(user_identifier) or self.username_exists(
                user_identifier
            )

    def email_exists(self, email: str) -> bool:
        """Returns whether a user with a given email exists in the db"""
        return self.user_collection.dependency().find_one({"email": email}) is not None

    def username_exists(self, username: str) -> bool:
        """Returns whether a user with a given username exists in the db"""
        return (
            self.user_by_username(username)
            is not None
        )

    @router.get("/users")
    def user_matches_password(self, user_identifier: str, password: str) -> dict:
        """Returns whether a given user identifier matches a given password in the db"""
        return self.user_collection.dependency().find_one(
            {"username": user_identifier, "password": password}
        ) or self.user_collection.dependency().find_one(
            {"email": user_identifier, "password": password}
        ) or {}

    def user_by_username(self, username):
        return self.user_collection.dependency().find_one({"username": username})


app.include_router(router)


if __name__ == "__main__":
    # Run Server
    subprocess.call("uvicorn server:app --host 0.0.0.0 --port 8000")
    #uvicorn.run(app)
