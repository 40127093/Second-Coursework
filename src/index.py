import ConfigParser
import logging
import warnings

# to avoid the generation of .pyc files
import sys

sys.dont_write_bytecode = True

from flask.exthook import ExtDeprecationWarning
warnings.simplefilter('ignore', ExtDeprecationWarning)

from logging.handlers import RotatingFileHandler
from flask import (Flask, url_for, g, render_template, flash, redirect)
from flask.ext.bcrypt import check_password_hash
from flask.ext.login import (LoginManager, login_user, logout_user,
                             login_required)
import models
import forms

app = Flask(__name__)
app.secret_key = 'sefdewfewr43r535rewfwda!'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
  try:
    return models.User.get(models.User.id == userid)
  except models.DoesNotExist:
    return None


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
  app.logger.info("Someone visited the Home page " + this_route)
  return render_template('index.html')

@app.route("/myprofile/")
def profile():
  this_route = url_for('.profile')
  app.logger.info("Someone visited the Personal Profile page " + this_route)
  return "This is my profile!"

@app.route('/register', methods=('GET','POST'))
def register():
  this_route = url_for('.register')
  app.logger.info("Someone visited the Register page " + this_route)
  form = forms.RegisterForm()
  if form.validate_on_submit():
    flash("Yay, you registered!", "success")
    models.User.create_user(
      username=form.username.data,
      email=form.email.data,
      password=form.password.data
    )
    return redirect(url_for('root'))
  return render_template('register.html', form=form) 

@app.route('/login', methods=('GET','POST'))  
def login():
  this_route = url_for('.login')
  app.logger.info("Someone visited the Login page " + this_route)
  form = forms.LoginForm()
  if form.validate_on_submit():
    try:
      user = models.User.get(models.User.email == form.email.data)
    except models.DoesNotExist:
      flash("Your email or password doesn't match!", "error")
    else:
      if check_password_hash(user.password, form.password.data):
        login_user(user)
        flash("You've been loggen in!", "success")
        return "Hello!"
      else:
        flash("Your email or password doesn't match!", "error")
  return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
  this_route = url_for('.logout')
  app.logger.info("Someone requested to logout " + this_route)
  logout_user()
  flash("You've been logged out. Come back soon!","success")
  return redirect(url_for('root'))


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
  models.initialize()
  try:
    models.User.create_user(
       username='poisonphoebe',
       email='poisonphoebe@hotmail.com',
       password='password',
       admin=True
     )
  except ValueError:
    pass
  app.run(
    host = app.config['ip_address'],
    port = int(app.config['port']))
