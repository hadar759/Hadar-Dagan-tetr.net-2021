import json

from bottle import post, get


class ServerCommunicator:
    def __init__(self, server_ip: str, server_port: str):
        self.server_ip = server_ip
        self.server_port = server_port

    def update_outer_ip(self, user_identifier: str, password: str, outer_ip: str):
        post(f"http://{self.server_ip}:{self.server_port}/users/outer-ip?user_identifier={user_identifier}&password={password}&ip={outer_ip}")

    def update_local_ip(self, user_identifier: str, password: str, local_ip: str):
        post(
            f"http://{self.server_ip}:{self.server_port}/users/local-ip?user_identifier={user_identifier}&password={password}&local_ip={local_ip}")

    def create_user(self, db_post: dict):
        post(f"http://{self.server_ip}:{self.server_port}/users", data=json.dumps(db_post))

    def estimated_document_count(self) -> int:
        return int(get(f"http://{self.server_ip}:{self.server_port}/users/len").text)

    def user_identifier_exists(self, user_identifier: str) -> bool:
        """Returns whether a user with a given user identifier exists in the database"""
        return get(f"http://{self.server_ip}:{self.server_port}/users/find?user_identifier={user_identifier}").text == "true"

    def username_exists(self, username: str) -> bool:
        """Returns whether a user with a given username exists in the database"""
        return get(f"http://{self.server_ip}:{self.server_port}/users/find?username={username}").text == "true"

    def email_exists(self, email: str) -> bool:
        """Returns whether a user with a given email exists in the database"""
        return get(f"http://{self.server_ip}:{self.server_port}/users/find?email={email}").text == "true"

    def get_user(self, user_identifier: str, password: str) -> dict:
        """Returns a dict of a user in the database with the given user_identifier and password"""
        resp = get(
            f"http://{self.server_ip}:{self.server_port}/users?user_identifier={user_identifier}&password={password}")
        # Load the user's information onto a tuple
        return json.loads(resp.text)
