import time
from typing import Optional, Dict

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
    def __init__(self):
        self.user_collection: Depends = Depends(get_collection)

    @router.get("/users/len")
    def get_document_count(self) -> int:
        return self.user_collection.dependency().estimated_document_count()

    @router.post("/users/ip")
    def update_ip(self, user_identifier: str, password: str, ip: str):
        user = self.user_matches_password(user_identifier, password)

        old_query = {"ip": user["ip"]}
        new_query = {"$set": {"ip": ip}}

        self.user_collection.dependency().update_one(old_query, new_query)

    @router.post("/users")
    def create_user(self, user_field: Dict):
        """Adds a user to the db"""
        self.user_collection.dependency().insert_one(user_field)

    @router.get("/users/find")
    def user_exists(self, user_identifier: Optional[str] = None, email: Optional[str] = None, username: Optional[str] = None) -> bool:
        """Returns whether a user exists in the db"""
        if email:
            user_by_email = self.email_exists(email)
            return user_by_email

        if username:
            user_by_username = self.username_exists(username)
            return user_by_username

        if user_identifier:
            return self.email_exists(user_identifier) or self.username_exists(user_identifier)

    def email_exists(self, email: str) -> bool:
        """Returns whether a user with a given email exists in the db"""
        return self.user_collection.dependency().find_one({"email": email}) is not None

    def username_exists(self, username: str) -> bool:
        """Returns whether a user with a given username exists in the db"""
        return self.user_collection.dependency().find_one({"username": username}) is not None

    @router.get("/users")
    def user_matches_password(self, user_identifier: str, password: str) -> dict:
        """Returns whether a given user identifier matches a given password in the db"""
        return self.user_collection.dependency().find_one(
            {"username": user_identifier, "password": password}
        ) or self.user_collection.dependency().find_one(
            {"email": user_identifier, "password": password}
        )


app.include_router(router)


if __name__ == '__main__':
    # Run Server
    uvicorn.run(app)
