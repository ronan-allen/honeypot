#!/usr/bin/env python3
import socket
import datetime
import mysql.connector
from mysql.connector import Error
import requests
from ipwhois import IPWhois
import configparser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_ipinfo(ip_address):
    url = f'http://ipinfo.io/{ip_address}/json'
    response = requests.get(url)
    data = response.json()
    isp = data.get('org', 'Unknown')
    latitude, longitude = data.get('loc', '0,0').split(',')
    timezone_info = data.get('timezone', 'Unknown')
    country = timezone_info.split('/')[0] if '/' in timezone_info else 'Unknown'
    return isp, latitude, longitude, country

def get_abuse_email(ip_address):
    try:
        url = f'https://wq.apnic.net/apnic-bin/whois.pl?do_search=Search&searchtext={ip_address}'
        response = requests.get(url)
        response_text = response.text
        start_index = response_text.find('abuse-mailbox:')
        if start_index != -1:
            end_index = response_text.find('\n', start_index)
            if end_index != -1:
                return response_text[start_index + len('abuse-mailbox:'):end_index].strip()
        return 'Unknown'
    except Exception as e:
        print(f"Error getting abuse email: {e}")
        return 'Unknown'

def parse_telnet(data):
    return (data,)

def get_db_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        db_config = {
            'host': config['mysql']['host'],
            'database': config['mysql']['database'],
            'user': config['mysql']['user'],
            'password': config['mysql']['password']
        }
    except KeyError as e:
        logging.error(f"Database configuration error: Missing {e} in config.ini")
        raise
    return db_config

def setup_database():
    db_config = get_db_config()
    connection = None
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = connection.cursor()

        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        cursor.execute(f"USE {db_config['database']}")

        # Define table schema
        table_schema = {
            'id': 'INT AUTO_INCREMENT PRIMARY KEY',
            'timestamp': 'DATETIME',
            'content': 'BLOB',
            'source_ip': 'VARCHAR(45)',
            'dest_ip': 'VARCHAR(45)',
            'isp': 'VARCHAR(255)',
            'source_country': 'VARCHAR(255)',
            'abuse_email': 'VARCHAR(255)',
            'latitude': 'VARCHAR(255)',
            'longitude': 'VARCHAR(255)'
        }

        # Create table if it doesn't exist
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS telnet_data (
            {', '.join([f'{column} {definition}' for column, definition in table_schema.items()])}
        )
        """
        cursor.execute(create_table_query)
        connection.commit()

        # Check and update schema if necessary
        cursor.execute("DESCRIBE telnet_data")
        existing_columns = {column[0] for column in cursor.fetchall()}
        for column, definition in table_schema.items():
            if column not in existing_columns:
                cursor.execute(f"ALTER TABLE telnet_data ADD COLUMN {column} {definition}")
                connection.commit()

    except Error as e:
        print(f"Error setting up database: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def save_to_database(timestamp, content, source_ip, dest_ip, isp, source_country, abuse_email, latitude, longitude):
    db_config = get_db_config()
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        insert_query = """INSERT INTO telnet_data (timestamp, content, source_ip, dest_ip, isp, source_country, abuse_email, latitude, longitude)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        abuse_email = get_abuse_email(source_ip)
        isp, latitude, longitude, source_country = get_ipinfo(source_ip)
        dest_ip = source_ip  # Keep dest_ip as source_ip
        record_to_insert = (timestamp, content, source_ip, dest_ip, isp, source_country, abuse_email, latitude, longitude)
        cursor.execute(insert_query, record_to_insert)
        connection.commit()
    except Error as e:
        logging.error(f"MySQL Error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    host = '0.0.0.0'
    port = 23
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.listen()
            logging.info(f"Telnet capture script listening on {host}:{port}")
            while True:
                conn, addr = s.accept()
                dest_ip, dest_port = conn.getpeername()
                with conn:
                    logging.info(f"Connected by {addr}, destination IP: {dest_ip}")
                    data_buffer = b''
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        logging.info(f"Received data (hex): {data.hex()}")
                        data_buffer += data
                        if b'\n' in data_buffer:
                            logging.info(f"Received data (hex): {data_buffer.hex()}")
                            parsed_data = parse_telnet(data_buffer)
                            abuse_email = get_abuse_email(addr[0])
                            isp, latitude, longitude, source_country = get_ipinfo(addr[0])
                            save_to_database(
                                datetime.datetime.now(),
                                parsed_data[0],
                                addr[0],
                                dest_ip,
                                isp,
                                source_country,
                                abuse_email,
                                latitude,
                                longitude
                            )
                            data_buffer = b''
    except Exception as e:
        logging.error(f"Unexpected error in main: {e}")

if __name__ == "__main__":
    main()
