from typing import Optional, Dict, List

import uvicorn
from pymongo import MongoClient
from fastapi import Depends, FastAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

app = FastAPI()
router = InferringRouter()


def get_collection():
    # TODO change this from being hardcoded
    client = MongoClient(
        "mongodb+srv://hadar759:noamhadar126@tetr-net.kcot4.mongodb.net/tetr-net?retryWrites=true&w=majority"
    )
    db = client["tetris"]
    collection = db["users"]
    return collection


@cbv(router)
class Server:
    SERVERS_QUERY = {"_id": 0}

    def __init__(self):
        self.user_collection: Depends = Depends(get_collection)

    @router.get("/users/invite-ip")
    def get_invite_ip(self, username):
        # Get the user
        user = self.user_collection.dependency().find_one({"username": username})
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
        user = self.user_collection.dependency().find_one({"username": username})
        return user["invite"]

    @router.post("/users/online")
    def update_online(self, user_identifier: str, online: bool):
        """Updates the player online status"""
        # The given identifier is a username
        if self.username_exists(user_identifier):
            query = {"username": user_identifier}
        # The given identifier is an email
        else:
            query = {"email": user_identifier}
        # Switch the player's online state (if he was offline, they will log in and be online, and vice versa)
        new_query = {"$set": {"online": online}}

        self.user_collection.dependency().update_one(filter=query, update=new_query)

    @router.get("/users/online")
    def player_online(self, username: str) -> bool:
        """Returns whether a player is online or not"""
        if self.username_exists(username):
            player = self.user_collection.dependency().find_one({"username": username})
            return player["online"]
        return False

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

    @router.get("/users/len")
    def get_document_count(self) -> int:
        """Returns the number of documents in the collection. Mainly used for checking server status."""
        return self.user_collection.dependency().estimated_document_count()

    @router.post("/users/outer-ip")
    def update_outer_ip(self, user_identifier: str, password: str, ip: str):
        """Updates the outer ip of a user on a new connection"""
        user = self.user_matches_password(user_identifier, password)

        new_query = {"$set": {"ip": ip}}

        self.user_collection.dependency().update_one(
            filter={"username": user["username"]}, update=new_query
        )

    @router.post("/users/local-ip")
    def update_local_ip(self, user_identifier: str, password: str, local_ip: str):
        """Updates the local ip of a user on a new connection"""
        user = self.user_matches_password(user_identifier, password)

        # old_query = {"local_ip": user["local_ip"]}
        # new_query = {"$set": {"local_ip": local_ip}}

        self.user_collection.dependency().update_one(old_query, new_query)

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
            self.user_collection.dependency().find_one({"username": username})
            is not None
        )

    @router.get("/users")
    def user_matches_password(self, user_identifier: str, password: str) -> dict:
        """Returns whether a given user identifier matches a given password in the db"""
        return self.user_collection.dependency().find_one(
            {"username": user_identifier, "password": password}
        ) or self.user_collection.dependency().find_one(
            {"email": user_identifier, "password": password}
        )


app.include_router(router)


if __name__ == "__main__":
    # Run Server
    uvicorn.run(app)
