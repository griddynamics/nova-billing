# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Nova Billing
#    Copyright (C) GridDynamics Openstack Core Team, GridDynamics
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Session Handling for SQLAlchemy backend."""

import sqlalchemy.exc
import sqlalchemy.orm
import time

import nova.exception
from nova import flags
from nova import log as logging


FLAGS = flags.FLAGS
flags.DEFINE_string('billing_sql_connection',
              'sqlite:////var/lib/nova/nova_billing.sqlite',
              'connection string for billing sql database')


LOG = logging.getLogger("nova_billing.db.sqlalchemy.session")

_ENGINE = None
_MAKER = None


def get_session(autocommit=True, expire_on_commit=False):
    """Return a SQLAlchemy session."""
    global _ENGINE, _MAKER

    if _MAKER is None or _ENGINE is None:
        _ENGINE = get_engine()
        _MAKER = get_maker(_ENGINE, autocommit, expire_on_commit)

    session = _MAKER()
    session.query = nova.exception.wrap_db_error(session.query)
    session.flush = nova.exception.wrap_db_error(session.flush)
    return session


def get_engine():
    """Return a SQLAlchemy engine."""
    connection_dict = sqlalchemy.engine.url.make_url(FLAGS.billing_sql_connection)

    engine_args = {
        "pool_recycle": FLAGS.sql_idle_timeout,
        "echo": False,
    }

    if "sqlite" in connection_dict.drivername:
        engine_args["poolclass"] = sqlalchemy.pool.NullPool

    engine = sqlalchemy.create_engine(FLAGS.billing_sql_connection, **engine_args)
    ensure_connection(engine)
    return engine


def ensure_connection(engine):
    remaining_attempts = FLAGS.sql_max_retries
    while True:
        try:
            engine.connect()
            return
        except sqlalchemy.exc.OperationalError:
            if remaining_attempts == 0:
                raise
            LOG.warning('SQL connection failed (%(connstring)s). '
                          '%(attempts)d attempts left.',
                           {'connstring': FLAGS.billing_sql_connection,
                            'attempts': remaining_attempts})
            time.sleep(FLAGS.sql_retry_interval)
            remaining_attempts -= 1


def get_maker(engine, autocommit=True, expire_on_commit=False):
    """Return a SQLAlchemy sessionmaker using the given engine."""
    return sqlalchemy.orm.sessionmaker(bind=engine,
                                       autocommit=autocommit,
                                       expire_on_commit=expire_on_commit)
