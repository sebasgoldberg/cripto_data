# Installation

## Prerequisites

### Postgres (optional)
```
sudo apt-get install postgresql
sudo apt-get install python-psycopg2
sudo apt-get install libpq-dev
```

## cripto_data
```
git clone https://github.com/sebasgoldberg/cripto_data.git
cd cripto_data
pip install -r requirements.txt
./manage.py migrate
```

# Config

## Settings

`cp cripto_data/settings.template.py cripto_data/settings.py` and mofify the following as required:
- SECRET_KEY
- DATABASES
- X_CMC_PRO_API_KEY

# Execution

## Services

### Quote Latest 

In `cripto_data/fetch_data/templates/fetch_data` there are a daemon script template and a systemd service template.
Use them to create the corresponding service to register the latest prices in the database.

