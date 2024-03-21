import pkg_resources
import logging
import os
import warnings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from uta.exceptions import *
from uta import models


try:
    __version__ = pkg_resources.get_distribution(__package__).version
except pkg_resources.DistributionNotFound as e:
    warnings.warn(
        "can't get __version__ because %s package isn't installed" % __package__, Warning)
    __version__ = None


public_db_url = "postgresql://uta_public:uta_public@uta.invitae.com/uta"
default_db_url = os.environ.get("UTA_DB_URL", public_db_url)


def connect(db_url=default_db_url):
    """
    Connect to a UTA database instance and return a sqlalchemy Session.

    When called with an explicit db_url argument, that db_url is used for connecting.

    When called without an explicit argument, the function default is
    determined by the environment variable UTA_DB_URL if it exists, or
    bdi.sources.uta0.public_db_url.

    The format of the db_url is driver://user:pass@host/database (the same
    as that used by SQLAlchemy).  Examples:

    A remote public postgresql database:
        postgresql://uta_public:uta_public@uta.invitae.com/uta'

    A local postgresql database:
        postgresql://localhost/uta

    A local SQLite database:
        sqlite:////tmp/uta-0.0.5.db

    SQLite database snapshots are available at:
      `https://bitbucket.org/biocommons/uta/downloads`_
    """

    # TODO: Verify schema version

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    logger = logging.getLogger(__name__)
    logger.info("connected to " + db_url)

    return session


# <LICENSE>
# Copyright 2014 UTA Contributors (https://bitbucket.org/biocommons/uta)
##
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
##
# http://www.apache.org/licenses/LICENSE-2.0
##
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# </LICENSE>
