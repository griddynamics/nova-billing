from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

from nova_billing.heart import app


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)
