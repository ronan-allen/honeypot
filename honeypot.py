#!/usr/bin/env python3
import socket
import datetime
import mysql.connector
from mysql.connector import Error
import requests
from ipwhois import IPWhois

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

def save_to_database(timestamp, content, source_ip, dest_ip, isp, source_country, abuse_email, latitude, longitude):
    connection = None
    try:
        connection = mysql.connector.connect(
            host='your_database_ip',
            user='your_database_user',
            password='your_database_password',
            database='your_database_name',
            allow_local_infile=True,
            auth_plugin='mysql_native_password'
        )
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
        print(f"Error: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    host = '0.0.0.0'
    port = 23
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print(f"Telnet capture script listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            dest_ip, dest_port = conn.getpeername()
            with conn:
                print(f"Connected by {addr}, destination IP: {dest_ip}")
                data_buffer = b''
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print(f"Received data (hex): {data.hex()}")
                    data_buffer += data
                    if b'\n' in data_buffer:
                        print(f"Received data (hex): {data_buffer.hex()}")
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
if __name__ == "__main__":
    main()
