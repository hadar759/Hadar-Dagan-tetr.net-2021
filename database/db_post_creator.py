class DBPostCreator:
    @staticmethod
    def create_user_post(
        user_number: int, email: str, username: str, password: str, ip: str
    ) -> dict:
        """Returns a db post with the given parameters"""
        return {
            "type": "user",
            "email": email,
            "username": username,
            "password": password,
            "ip": ip,
            "invite": "",
            "invite_ip": "",
            "online": True,
            "sprint": ["0", "0", "0", "0"],
            "marathon": 0,
            "apm_games": [],
            "apm": 0.0,
            "wins": 0,
            "games": 0,
            "friends": [],
            "requests_received": [],
            "requests_sent": [],
        }

    @staticmethod
    def create_room_post(
        estimated_document_count,
        default,
        room_name,
        ip: str,
        min_apm: int = 0,
        max_apm: int = 999,
        private: bool = False,
    ) -> dict:
        """Returns a db post with the given parameters"""
        return {
            "type": "room",
            "default": default,
            "name": room_name,
            "ip": ip,
            "player_num": 0,
            "min_apm": min_apm,
            "max_apm": max_apm,
            "private": private,
        }
