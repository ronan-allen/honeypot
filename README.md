# Honey Pot
### What is this? 
This is a small honeypot project that will listen for (currently telnet) traffic and output details about that session and the source IP address to a database.  
[Grafana](https://grafana.com/) then visualizes the data from this database to then view.

### Quick Note
I run this script as a service (honeypot.service)  
This requires honeypot.py to be in '~/opt/honeypot'  
Otherwise, the script will run fine standalone. 

## Current Capabilities
- Capture Telnet traffic (Port 23)
- Capture data input into the telent session
- Gather metadata about the source IP
    - ISP
    - Country
    - Coordinates
    - Abuse Contact
- Output to MySQL Database

## Goals
- Add more Metadata variables
- Compatibility with multiple protocols (SSH, RDP, etc)
- Ability to notice port scans (not legitimate sessions)
- Allow script to create database, tables, columns as necessary.
- Capture the destination IP that the source is intended to. (Allows for multiple entrypoints)

## How to Run

Follow these steps to clone the repository, build the Docker container, and run it with the necessary configurations.

1. **Clone the Repository**

   First, clone the repository to your local machine using the following command:

   ```bash 
   mkdir /opt/honeypot && cd /opt/honeypot
   git clone https://github.com/ronan-allen/honeypot.git
   cd honeypot
   ```

2. **Build the Docker Container**

   Build the Docker container using the Dockerfile included in the repository:

   ```bash
   docker build -t honeypot .
   ```

3. **Run the Docker Container**

   Run the Docker container:

   ```bash
   docker run -d \
   --name honeypot \
   -p 23:23 \
   --restart unless-stopped \
   honeypot
   ```

And yeah, check the database to make sure it's been created, and the table.