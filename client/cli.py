from client.api import CampionatoAPI
from client.ui import menu_loop

PASSWORD = "mypass"  


def main():
    pwd = input("Password: ").strip()
    if pwd != PASSWORD:
        print("Password errata.")
        return

    api = CampionatoAPI(host="127.0.0.1", port=5000)
    menu_loop(api)


if __name__ == "__main__":
    main()
