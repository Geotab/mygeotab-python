# -*- coding: utf-8 -*-

import os
import getpass
from mygeotab import api


def main():
    # Get credentials
    username = input("Username: ")              # myuser@example.com
    password = getpass.getpass("Password: ")    # password
    database = input("Database: ")              # demo
    server = input("Server: ")                  # my.geotab.com
    port = input("Port: ")

    # Get path to private key/certificate from environment variables
    key_path = os.environ["MYGEOTAB_CERTIFICATE_KEY"]
    cert_path = os.environ["MYGEOTAB_CERTIFICATE_CER"]

    if not key_path or not cert_path:
        print("MyGeotab key or certificate not provided")
        exit(1)

    cert = (cert_path, key_path)
    session = api.API(username=username, password=password, database=database, server=server, cert=cert)

    try:
        session.authenticate()
    except api.MyGeotabException as exception:
        print(f"AUTH ERROR: {exception}")
        exit(1)

    # Create new session using authenticated session to the target server and port
    if ':' not in session.credentials.server:
        credentials = session.credentials
        credentials.server = f"{credentials.server}:{port}"
        session = api.API.from_credentials(credentials)

    # Send requests
    # ...


if __name__ == "__main__":
    main()
