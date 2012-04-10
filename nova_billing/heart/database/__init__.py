from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

from nova_billing.heart import app
from nova_billing.utils import global_conf


app.config['SQLALCHEMY_DATABASE_URI'] = global_conf.heart_db_url
db = SQLAlchemy(app)
