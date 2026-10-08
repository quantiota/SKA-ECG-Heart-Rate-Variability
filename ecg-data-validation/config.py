"""Configuration for ECG data validation."""
import os

# QuestDB ILP (line protocol) — ingestion path, 9009
ILP_CONFIG = {
    'host': os.getenv('QDB_ILP_HOST', os.getenv('QDB_PG_HOST', 'localhost')),
    'port': int(os.getenv('QDB_ILP_PORT', '9009')),
}

# QuestDB pg-wire — queries and DDL, 8812
QDB_CONFIG = {
    'dbname': os.getenv('QDB_PG_NAME', 'qdb'),
    'user': os.getenv('QDB_PG_USER', 'admin'),
    'password': os.getenv('QDB_PG_PASSWORD', 'quest'),
    'host': os.getenv('QDB_PG_HOST', 'localhost'),
    'port': os.getenv('QDB_PG_PORT', '8812'),
}

# ECG Stream Configuration
ECG_CONFIG = {
    'data_dir': os.getenv('ECG_DATA', 'data'),
    'records': 'records.txt',        # the record IDs to stream, in order
    'dataset': 'autonomic-aging-cardiovascular/1.0.0',
    'channel': 'ECG1',               # one fixed lead for every record
    'window_s': 900,                 # first 15 min — the length every record has
    # The recording was sampled at 1000 Hz, so the stream runs at the same rate:
    # 1 sample = 1 ms, the true clock of the signal. One 15-minute window
    # therefore takes 15 minutes, and the 30 records 7.5 hours.
    'rate_hz': 1000.0,               # samples/s — native sampling rate
    'packet_steps': 1000,            # one packet per second
    'max_steps': None,               # None = every record, whole window
}

# Logging Configuration
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s %(levelname)s %(message)s',
    'file': 'logs/ecg_validation.log',
}
