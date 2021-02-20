import json

from requests import post, get


class ServerCommunicator:
    def __init__(self, server_ip: str, server_port: str):
        self.server_ip = server_ip
        self.server_port = server_port
        self.SERVER_DOMAIN = f"http://{self.server_ip}:{self.server_port}"

    @staticmethod
    def bool_to_string(condition: bool):
        return str(condition).lower()

    def get_invite_ip(self, username: str) -> str:
        return get(f"{self.SERVER_DOMAIN}/users/invite-ip?username={username}").text.replace('"', "")

    def dismiss_invite(self, invitee: str):
        post(f"{self.SERVER_DOMAIN}/users/invites?inviter={''}&invitee={invitee}&invite_ip={''}")

    def get_invite(self, username: str) -> str:
        """Return the current invite for the user"""
        return get(f"{self.SERVER_DOMAIN}/users/invites?username={username}").text.replace('"', '')

    def invite_user(self, inviter: str, invitee: str, invite_ip: str):
        """Invites a given player to a given server ip"""
        post(f"{self.SERVER_DOMAIN}/users/invites?inviter={inviter}&invitee={invitee}&invite_ip={invite_ip}")

    def update_online(self, username: str, online: bool):
        """Changes the online state of a given player"""
        post(f"{self.SERVER_DOMAIN}/users/online?user_identifier={username}&online={self.bool_to_string(online)}")

    def is_online(self, foe_name: str) -> bool:
        """Returns whether a given player is online"""
        return get(f"{self.SERVER_DOMAIN}/users/online?username={foe_name}").text == "true"

    def finished_server(self, server_ip: str):
        """Returns the server to the database after use"""
        post(f"{self.SERVER_DOMAIN}/users/servers?server_ip={server_ip}")

    def get_free_server(self) -> str:
        """Returns a random server ready for use"""
        return get(f"{self.SERVER_DOMAIN}/users/servers").text

    def update_outer_ip(self, user_identifier: str, password: str, outer_ip: str):
        """Updates the outer ip of a given user after a login"""
        post(f"{self.SERVER_DOMAIN}/users/outer-ip?user_identifier={user_identifier}&password={password}&ip={outer_ip}")

    def update_local_ip(self, user_identifier: str, password: str, local_ip: str):
        """Updates the local ip of a given user after a login"""
        post(
            f"{self.SERVER_DOMAIN}/users/local-ip?user_identifier={user_identifier}&password={password}&local_ip={local_ip}")

    def create_user(self, db_post: dict):
        """Adds a new user to the database"""
        post(f"{self.SERVER_DOMAIN}/users", data=json.dumps(db_post))

    def estimated_document_count(self) -> int:
        """Returns num of queries in the database. Mainly used for testing"""
        return int(get(f"{self.SERVER_DOMAIN}/users/len").text)

    def user_identifier_exists(self, user_identifier: str) -> bool:
        """Returns whether a user with a given user identifier exists in the database"""
        return get(f"{self.SERVER_DOMAIN}/users/find?user_identifier={user_identifier}").text == "true"

    def username_exists(self, username: str) -> bool:
        """Returns whether a user with a given username exists in the database"""
        return get(f"{self.SERVER_DOMAIN}/users/find?username={username}").text == "true"

    def email_exists(self, email: str) -> bool:
        """Returns whether a user with a given email exists in the database"""
        return get(f"{self.SERVER_DOMAIN}/users/find?email={email}").text == "true"

    def get_user(self, user_identifier: str, password: str) -> dict:
        """Returns a dict of a user in the database with the given user_identifier and password"""
        resp = get(
            f"{self.SERVER_DOMAIN}/users?user_identifier={user_identifier}&password={password}")
        # Load the user's information onto a tuple
        return json.loads(resp.text)
