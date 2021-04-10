import os
import random
import smtplib
import ssl
import subprocess
from typing import Optional, Dict, List
import time

import uvicorn
from pymongo import *
from fastapi import Depends, FastAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

app = FastAPI()
router = InferringRouter()

pass_resets = {}

def get_collection():
    with open(r"../resources/mongodb.txt", "r") as pass_file:
        pass_text = pass_file.read()
    client = MongoClient(pass_text)
    db = client["tetris"]
    user_collection = db["users"]
    return user_collection

@cbv(router)
class Server:
    SERVERS_QUERY = {"_id": 0}
    SPRINTS = {20: 0, 40: 1, 100: 2, 1000: 3}

    def __init__(self):
        self.user_collection: Depends = Depends(get_collection)
        with open(r"../resources/password.txt", "r") as pass_file:
            self.email_pass = pass_file.read()

        with open(r"../resources/gmail.txt", "r") as email_file:
            self.email = email_file.read()

    @router.post("/users/friends/accept")
    def accept_friend(self, sender, recipient):
        receiving_user = self.user_by_username(recipient)
        sending_user = self.user_by_username(sender)

        received_requests = receiving_user["requests_received"]
        received_requests.remove(sender)
        received_friends = receiving_user["friends"]
        received_friends.append(sender)
        receiving_update = {
            "$set": {
                "requests_received": received_requests,
                "friends": received_friends,
            }
        }

        sent_requests = sending_user["requests_sent"]
        sent_requests.remove(recipient)
        sender_friends = sending_user["friends"]
        sender_friends.append(recipient)
        sending_update = {
            "$set": {"requests_sent": sent_requests, "friends": sender_friends}
        }

        self.user_collection.dependency().update_one(
            filter={"username": recipient}, update=receiving_update
        )
        self.user_collection.dependency().update_one(
            filter={"username": sender}, update=sending_update
        )

    # TODO: make friends list, make accepting and declining requests, check if triple / link works
    @router.post("/users/friends/remove")
    def remove_friend(self, sender, recipient):
        receiving_user = self.user_by_username(recipient)
        sending_user = self.user_by_username(sender)

        if sender in receiving_user["requests_received"]:
            received_requests = receiving_user["requests_received"]
            received_requests.remove(sender)
            receiving_update = {"$set": {"requests_received": received_requests}}

            sent_requests = sending_user["requests_sent"]
            sent_requests.remove(recipient)
            sending_update = {"$set": {"requests_sent": sent_requests}}

        else:
            receiving_friends = receiving_user["friends"]
            receiving_friends.remove(sender)
            receiving_update = {"$set": {"friends": receiving_friends}}

            sending_friends = sending_user["friends"]
            sending_friends.remove(recipient)
            sending_update = {"$set": {"friends": sending_friends}}

        self.user_collection.dependency().update_one(
            filter={"username": recipient}, update=receiving_update
        )
        self.user_collection.dependency().update_one(
            filter={"username": sender}, update=sending_update
        )

    @router.post("/users/friends/send")
    def send_friend_request(self, sender, recipient):
        receiving_user = self.user_by_username(recipient)
        sending_user = self.user_by_username(sender)

        received_requests = receiving_user["requests_received"]
        received_requests.append(sender)
        receiving_update = {"$set": {"requests_received": received_requests}}

        sent_requests = sending_user["requests_sent"]
        sent_requests.append(recipient)
        sending_update = {"$set": {"requests_sent": sent_requests}}

        self.user_collection.dependency().update_one(
            filter={"username": recipient}, update=receiving_update
        )
        self.user_collection.dependency().update_one(
            filter={"username": sender}, update=sending_update
        )

    # TODO test how much time this takes, and then implement it in the friends screen
    @router.get("/users/friends/profiles")
    def get_friends_profiles(self, username):
        user = self.user_by_username(username)
        friends = []
        for friend in user["friends"]:
            friends.append(self.get_user_profile(friend))
        return friends

    @router.get("/users/profile")
    def get_user_profile(self, username):
        return self.user_collection.dependency().find_one(
            {"username": username},
            {
                "username": 1,
                "sprint": 1,
                "apm": 1,
                "games": 1,
                "wins": 1,
                "marathon": 1,
                "friends": 1,
                "requests_received": 1,
                "requests_sent": 1,
                "_id": 0,
            },
        )

    @router.get("/users/apms")
    def get_apm_leaderboard(self):
        """Returns all users sorted by highest apm"""
        users = list(
            self.user_collection.dependency().find(
                {"type": "user"}, {"_id": 0, "username": 1, "apm": 1}
            )
        )
        return [
            user
            for user in sorted(users, key=lambda user: user["apm"])[::-1]
            if user["apm"] != 0
        ]

    @router.get("/users/marathons")
    def get_marathon_leaderboard(self):
        """Returns all users sorted by highest marathon score"""
        users = list(
            self.user_collection.dependency().find(
                {"type": "user"}, {"_id": 0, "username": 1, "marathon": 1}
            )
        )
        # Sort users by marathon score, discard any users without a marathon score
        return [
            user
            for user in sorted(users, key=lambda user: user["marathon"])[::-1]
            if user["marathon"] != 0
        ]

    @router.get("/users/sprints")
    def get_sprint_leaderboard(self, line_num):
        """Returns all users sorted by fastest sprint time"""
        users = list(
            self.user_collection.dependency().find(
                {"type": "user"}, {"_id": 0, "username": 1, "sprint": 1}
            )
        )
        print(users)
        line_index = self.SPRINTS[int(line_num)]

        def sprint_filter(user):
            return self.sprint_time_to_int(user["sprint"][line_index])

        # Sort the users, discard all without a score, and only save the relevant score
        # This line does too much but I like list comprehensions too much so i'll keep it lol
        sorted_users = [
            {"username": user["username"], f"{line_num}l": user["sprint"][line_index]}
            for user in sorted(users, key=sprint_filter)
            if user["sprint"][line_index] != "0"
        ]
        return sorted_users

    @router.post("/users/rooms/delete")
    def delete_room(self, room_name):
        self.user_collection.dependency().find_one_and_delete(
            filter={"type": "room", "name": room_name}
        )

    @router.post("/users/rooms/player-num")
    def update_player_num(self, ip, player_num):
        self.user_collection.dependency().find_one_and_update(
            {"ip": ip}, update={"$set": {"player_num": player_num}}
        )

    @router.post("/users/rooms")
    def create_room(self, room: Dict):
        self.user_collection.dependency().insert_one(room)

    @router.get("/users/rooms")
    def get_rooms(self):
        rooms = self.user_collection.dependency().find({"type": "room"}, {"_id": 0})
        return list(rooms)

    @router.post("/users/games")
    def add_game(self, username: str, win: bool):
        """Updates the game and win count for a user"""
        user = self.user_by_username(username)
        # Add a game played to the user's query
        new_query = {"games": user["games"] + 1}
        # Add a win to the user's query
        if win:
            new_query["wins"] = user["wins"] + 1
        self.user_collection.dependency().update_one(
            filter={"username": username}, update={"$set": new_query}
        )

    @router.post("/users/sprint")
    def update_sprint(self, username: str, cur_time: float, line_num: int):
        user = self.user_by_username(username)
        line_index = self.SPRINTS[line_num]

        sprints = user["sprint"]
        old_time = self.sprint_time_to_int(sprints[line_index])
        time_str = self.seconds_to_str(cur_time)

        sprints[line_index] = time_str
        update_query = {"$set": {"sprint": sprints}}
        # User scored a faster best time
        if old_time == 0 or cur_time < old_time:
            self.user_collection.dependency().update_one(
                filter={"username": username}, update=update_query
            )
            return True
        return False

    @router.post("/users/marathon")
    def update_marathon(self, username: str, score: int):
        user = self.user_by_username(username)

        update_query = {"$set": {"marathon": score}}
        old_score = user["marathon"]
        # User scored a higher score
        if old_score == 0 or old_score < score:
            self.user_collection.dependency().update_one(
                filter={"username": username}, update=update_query
            )
            return True
        return False

    @router.post("/users/apm")
    def update_apm(self, username: str, apm: float):
        user = self.user_by_username(username)
        games: list = user["apm_games"]

        if len(games) > 9:
            games = games[len(games) - 9 :]
        games.append(apm)
        # Calculate the avg of the past 10 games
        avg_apm = round(sum(games) / len(games), 3)

        update_query = {"$set": {"apm_games": games, "apm": avg_apm}}
        self.user_collection.dependency().update_one(
            filter={"username": username}, update=update_query
        )

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
        invite = user["invite"]
        self.user_collection.dependency().update_one(
            filter=user, update={"$set": {"invite": ""}}
        )
        return invite

    @router.get("/users/online")
    def player_online(self, username: str) -> bool:
        """Returns whether a player is online or not"""
        if self.username_exists(username):
            player = self.user_by_username(username)
            return player["online"]
        return False

    @router.post("/users/online")
    def update_online(self, username: str, online: bool):
        self.user_collection.dependency().find_one_and_update(
            filter={"username": username}, update={"$set": {"online": online}}
        )

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
        return self.user_by_username(username) is not None

    @router.get("/users")
    def user_matches_password(self, user_identifier: str, password: str) -> dict:
        """Returns whether a given user identifier matches a given password in the db"""
        return (
            self.user_collection.dependency().find_one(
                {"username": user_identifier, "password": password}, {"_id": 0}
            )
            or self.user_collection.dependency().find_one(
                {"email": user_identifier, "password": password}, {"_id": 0}
            )
            or {}
        )

    def user_by_username(self, username):
        return self.user_collection.dependency().find_one(
            {"username": username}, {"_id": 0}
        )

    @staticmethod
    def sprint_time_to_int(time_str):
        time_str = time_str.split(":")
        old_time = 0
        # Time str to secs
        for i in range(len(time_str)):
            old_time += float(time_str[-i - 1]) * 60 ** i
        return old_time

    @staticmethod
    def seconds_to_str(seconds):
        # From seconds to string
        time_format = "%S"
        if seconds >= 60:
            time_format = "%M:" + time_format
        if seconds >= 3600:
            time_format = "%H:" + time_format
        return (
            time.strftime(time_format, time.gmtime(seconds))
            + "."
            + str(seconds).split(".")[1][:3]
        )

    @router.post("/users/create/code")
    def user_create_code(self, user_email):
        global pass_resets
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as email_server:
            email_server.login(self.email, self.email_pass)
            generated_code = "".join(random.choices([str(i) for i in range(10)], k=6))
            pass_resets[user_email] = (generated_code, time.time())
            email_msg = f"From: {self.email}\nSubject: Register User\n\nRegistration code: {generated_code}"
            email_server.sendmail(self.email, user_email, email_msg)

    @router.get("/pass/new")
    def is_password_new(self, user_email, password):
        print(self.user_collection.dependency().find_one({"email": user_email, "password": password}))
        return self.user_collection.dependency().find_one({"email": user_email, "password": password}) is None

    @router.post("/pass/update")
    def update_user_email(self, user_email, password):
        self.user_collection.dependency().find_one_and_update({"email": user_email}, {"$set": {"password": password}})

    @router.post("/pass/reset")
    def send_reset_email(self, user_email):
        global pass_resets
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as email_server:
            email_server.login(self.email, self.email_pass)
            generated_code = "".join(random.choices([str(i) for i in range(10)], k=6))
            pass_resets[user_email] = (generated_code, time.time())
            email_msg = f"From: {self.email}\nSubject: Reset password\n\nPassword reset code: {generated_code}"
            email_server.sendmail(self.email, user_email, email_msg)

    @router.get("/pass/check")
    def check_pass_reset(self, user_email, code):
        global pass_resets
        return pass_resets[user_email][0] == str(code) and time.time() - pass_resets[user_email][1] < 15 * 60


app.include_router(router)


if __name__ == "__main__":
    # Run Server
    # os.chdir("./database")
    subprocess.call("uvicorn server:app --host 0.0.0.0 --port 8000")
    # uvicorn.run(app)
