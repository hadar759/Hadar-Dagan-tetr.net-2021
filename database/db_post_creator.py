import pygame


class DBPostCreator:
    @staticmethod
    def create_user_post(email: str, username: str, password: str, ip: str) -> dict:
        """Returns a db post with the given parameters"""
        return {
            "type": "user",
            "email": email,
            "username": username,
            "password": password,
            "ip": ip,
            "invite": "",
            "invite_ip": "",
            "invite_room": "",
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
            "DAS": 130,
            "ARR": 1,
            "skin": 0,
            "ghost": True,
            "fade": True,
            "music": True,
            "controls": {
                "down": pygame.K_DOWN,
                "right": pygame.K_RIGHT,
                "left": pygame.K_LEFT,
                "flip_clock": pygame.K_x,
                "flip_counterclock": pygame.K_z,
            },
        }

    @staticmethod
    def create_room_post(
        default,
        room_name,
        outer_ip: str,
        inner_ip: str,
        min_apm: int = 0,
        max_apm: int = 999,
        private: bool = False,
    ) -> dict:
        """Returns a db post with the given parameters"""
        return {
            "type": "room",
            "default": default,
            "name": room_name,
            "outer_ip": outer_ip,
            "inner_ip": inner_ip,
            "player_num": 0,
            "min_apm": min_apm,
            "max_apm": max_apm,
            "private": private,
        }
