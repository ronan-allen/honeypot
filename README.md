# Honey Pot
## What is this? 
This is a small honeypot project that will listen for (currently telnet) traffic and output details about that session and the source IP address to a database.  
I pull the data from that database for a [Grafana](https://grafana.com/) instance to then create visualizations.

# Current Capabilities
- Capture Telnet traffic (Port 23)
- Capture data input into the telent session
- Gather metadata about the source IP
    - ISP
    - Country
    - Coordinates
    - Abuse Contact
- Output to MySQL Database

# Goals
- Add more Metadata variables
- Compatibility with multiple protocols (SSH, RDP, etc)
- Ability to notice port scans (not legitimate sessions)
- Allow script to create database, tables, columns as necessary.
- Capture the destination IP that the source is intended to. (Allows for multiple entrypoints)
