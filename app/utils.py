import yaml
from yaml.loader import SafeLoader
import pickle

import streamlit as st

from directories import APP_DIR, DATA_DIR


def load_config_file():
    filepath = APP_DIR / "text.yaml"
    config = load_yaml_file(filepath)
    return config


def load_yaml_file(filepath):
    with open(filepath) as file:
        obj = yaml.load(file, Loader=SafeLoader)
    return obj


def save_yaml_file(obj, filepath):
    with open(filepath, 'w') as file:
        yaml.dump(obj, file, default_flow_style=False)


def save_pickle_file(python_obj, filepath):
    with open(filepath, "wb") as pkl_file:
        pickle.dump(python_obj, pkl_file)


def load_pickle_file(filepath):
    with open(filepath, "rb") as pkl_file:
        return pickle.load(pkl_file)


def create_session_state_objects_if_they_dont_exist(objects):
    for key, value in objects.items():
        if key not in st.session_state:
            st.session_state[key] = value


def format_community_data_directory(community_name):
    directory = DATA_DIR / community_name
    directory.mkdir(parents=True, exist_ok=True)
    return directory