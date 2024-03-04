from configparser import ConfigParser
from pathlib import Path

from pkg_resources import resource_filename

def get_config():
    """Gets config from prod and will overwrite specific prod keys with local file for specific configuration"""
    config = ConfigParser()
    ncbi_config = Path(
        resource_filename("loading", str(Path("config") / "config.ini"))
    )
    config.readfp(open(ncbi_config))
    return config
