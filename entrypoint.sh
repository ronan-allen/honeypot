#!/bin/sh

echo "Starting the honeypot script."

# Generate the config.ini file dynamically based on environment variables
cat <<EOF > /app/config.ini
[mysql]
host = ${MYSQL_HOST:-your_default_host}
database = ${MYSQL_DB:-your_default_database}
user = ${MYSQL_USER:-your_default_user}
password = ${MYSQL_PASSWORD:-your_default_password}
EOF

# Run the Python script
python3 /app/main.py