import configparser
import yaml

from crawling.io.path_definition import get_file


def _load_yaml(file):

    with open(file, 'r') as f:
        loaded_yaml = yaml.full_load(f)
    return loaded_yaml


def set_config():
    """
    Get all the credentials from the credential file

    Returns:
        a dictionary containing credential to different servers
    """

    config = configparser.ConfigParser()
    config.read(get_file("config/credentials.ini"))

    return {"INSTAGRAM": config['INSTAGRAM']}
