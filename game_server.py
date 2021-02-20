import socket
import time


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("10.100.102.17", 44444))
    sock.listen(1)
    while True:
        # Accept the inviter
        inviter, addr = sock.accept()
        # Accept the invitee
        invitee, addr = sock.accept()
        # Receive whether the game is accepted or declined
        data = invitee.recv(1024)
        # Notify the inviter of the invitee's choice
        print(data.decode())
        inviter.send(data)
        if data.decode() == "declined":
            continue
        while True:
            pass


if __name__ == '__main__':
    main()
