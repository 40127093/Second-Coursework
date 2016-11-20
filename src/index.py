import ConfigParser
import logging

from logging.handlers import RotatingFileHandler
from flask import (Flask, url_for, g, render_template, flash, redirect)

import models

app = Flask(__name__)


@app.before_request
def before_request():
  """Connect to the database before each request."""
  g.db = models.DATABASE
  g.db.connect()


@app.after_request
def after_request(response):
  """Close the database connection after each request."""
  g.db.close()
  return response


@app.route("/")
def root():
  this_route = url_for('.root')
  app.logger.info("Logging a test message from " + this_route)
  return "Hello!"

@app.route("/myprofile/")
def profile():
  this_route = url_for('.profile')
  app.logger.info("Logging a test message from " + this_route)
  return "This is my profile!"

# parsing configuration details from an external file

def init (app):
  config = ConfigParser.ConfigParser()
  try:
    config_location = "etc/defaults.cfg"
    config.read(config_location)

    app.config['DEBUG'] = config.get("config", "debug")
    app.config['ip_address'] = config.get("config", "ip_address")
    app.config['port'] = config.get("config", "port")
    app.config['url'] = config.get("config", "url")

    app.config['log_file'] = config.get("logging", "name")
    app.config['log_location'] = config.get("logging", "location")
    app.config['log_level'] = config.get("logging", "level")

  except:
    print "Could not read configuration file from: " , config_location


# setting up a logging feature to record action logs into a text file    

def logs(app):
  log_pathname = app.config['log_location']+ app.config['log_file']
  file_handler = RotatingFileHandler(log_pathname, maxBytes=1024*1024*10 ,
  backupCount=1024)
  file_handler.setLevel( app.config['log_level'])
  formatter = logging.Formatter("%(levelname)s | %(asctime)s | %(module)s | %(funcName)s | %(message)s")
  file_handler.setFormatter(formatter)
  app.logger.setLevel(app.config['log_level'])
  app.logger.addHandler(file_handler)


# initialisation function

if __name__ == "__main__":
  init(app)
  logs(app)
  app.run(
    host = app.config['ip_address'],
    port = int(app.config['port']))
