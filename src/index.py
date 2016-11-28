import ConfigParser
import logging
import warnings

# to avoid the generation of .pyc files
import sys

sys.dont_write_bytecode = True

from flask.exthook import ExtDeprecationWarning
warnings.simplefilter('ignore', ExtDeprecationWarning)

from logging.handlers import RotatingFileHandler
from flask import (Flask, url_for, g, render_template, flash, redirect, abort)
from flask.ext.bcrypt import check_password_hash
from flask.ext.login import (LoginManager, login_user, logout_user,
                             login_required, current_user)
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
  g.user = current_user


@app.after_request
def after_request(response):
  """Close the database connection after each request."""
  g.db.close()
  return response

@app.route("/myprofile/<username>")
@app.route("/myprofile")
@login_required
def profile(username=None):
  template='portfolio.html'
  if username and username != current_user.username:
    user = models.User.select().where(models.User.username**username).get()
    this_route = url_for('.profile')
    app.logger.info( current_user.username + " viewed " + username + "'s personal Profile page " + this_route)
  else:
    user=current_user
    this_route = url_for('.profile')
    app.logger.info( current_user.username  + " viewed his/her personal Profile page " + this_route)
  if username:
    template = 'portfolio.html'
  return render_template(template, user=user)  


@app.route("/about/<username>")
@app.route("/about")
@login_required
def about(username=None):
  template='about.html'
  if username and username != current_user.username:
     user = models.User.select().where(models.User.username**username).get()
     this_route = url_for('.about')
     app.logger.info( current_user.username + " viewed " + username + "'s personal About page " + this_route)
  else:
    user=current_user
    this_route = url_for('.about')
    app.logger.info( current_user.username  + " viewed his/her personal About Me page " + this_route)
  if username:
    template = 'about.html'
  return render_template(template, user=user)  


@app.route("/new_post", methods=('GET','POST'))
@login_required
def post(username=None):
  if username and username != current_user.username:
    user = models.User.select().where(models.User.username**username).get()
    this_route = url_for('.post')
    app.logger.info("Someone viewed the Post Feed section" + this_route)
  else:
    user=current_user
  form = forms.PostForm()
  if form.validate_on_submit():
    models.Post.create(user=g.user._get_current_object(),
                      content=form.content.data.strip())
    flash("Message posted!", "success")
    return redirect(url_for('root'))
  return render_template('post.html', form=form, user=user)  


@app.route("/")
def root():
  this_route = url_for('.root')
  app.logger.info("Someone visited the root page" + this_route)
  stream = models.Post.select().limit(100)
  return render_template('stream.html', stream=stream)


@app.route('/stream')
@app.route('/stream/<username>')
def stream(username=None):
  template='stream.html'
  if username and username != current_user.username:
    try:
       user = models.User.select().where(models.User.username**username).get()
    except models.DoesNotExist:
      abort(404)
    else:  
       stream=user.posts.limit(100)
  else:
    stream=current_user.get_stream().limit(100)
    user=current_user
  if username:
      template = 'user-stream.html'
  return render_template(template, stream=stream, user=user)    

@app.route('/post/<int:post_id>')
def view_post(post_id):
  posts = models.Post.select().where(models.Post.id == post_id)
  return render_template('stream.html', stream=posts)


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
    return redirect(url_for('profile'))
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
        return redirect(url_for('profile'))
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
  return redirect(url_for('login'))


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

@app.errorhandler(404)
def not_found(error):
  return render_template('404.html'), 404

@app.route('/follow/<username>')
@login_required
def follow(username):
  try:
      to_user = models.User.get(models.User.username**username)
  except:
      pass
  else:
       try:
           models.Relationship.create(
             from_user=g.user._get_current_object(),
             to_user=to_user
           )
       except models.IntegrityError:
           pass
       else:
           flash("You're now following {}!".format(to_user.username),"success")
  return redirect(url_for('stream',username=to_user.username))    

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
  try:
      to_user = models.User.get(models.User.username**username)
  except:
      pass
  else:
       try:
           models.Relationship.get(
             from_user=g.user._get_current_object(),
             to_user=to_user
           ).delete_instance()
       except models.IntegrityError:
           pass
       else:
           flash("You've unfollowed {}!".format(to_user.username),"success")
  return redirect(url_for('stream',username=to_user.username))    


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
