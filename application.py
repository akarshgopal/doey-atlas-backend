import os
import json
from datetime import datetime,timedelta
import jwt
from random import randint, choice
import time

import dateutil.parser
from flask import Flask, request, make_response, \
    redirect, session, url_for, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from flask.views import MethodView

from operator import itemgetter
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError
from sqlalchemy.exc import IntegrityError

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from tempfile import mkdtemp
from config import *
from slots import *

#------------------------------------------------------------------Config App--------------------------------------
app = Flask(__name__, template_folder="../static", static_folder="../static/dist")
frontend_site="http://localhost:3000"

login_page = frontend_site + '/login'
home_page = frontend_site + '/doey'

cors = CORS(app, origins=frontend_site)
#app = Flask(__name__, static_folder="../static/dist", template_folder="../static")
#app._static_url_path = "../static/dist"
app.config.from_object(config['dev'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config["SESSION_FILE_DIR"] = mkdtemp()
#app.config["SESSION_PERMANENT"] = False          #forgets session after closing tab
#app.config["SESSION_TYPE"] = "filesystem"        #uses filesystem instead of cookies
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
db = SQLAlchemy(app)
#Session(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

#Set the key as an environment variable:
SECRET_KEY="\xf9'\xe4p(\xa9\x12\x1a!\x94\x8d\x1c\x99l\xc7\xb7e\xc7c\x86\x02MJ\xa0"

#------------------------------------------------------------------ USER Table model -----------------------------
class Users(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    email = db.Column(db.String(50),unique=True,nullable=False)
    name = db.Column(db.String(80),nullable=False)
    registered_on = db.Column(db.DateTime)
    contacts = db.Column(db.String)
    avatar = db.Column(db.String)

    def __init__(self, name,email,avatar):
        self.name=name
        self.email=email
        self.avatar=avatar
        #self.registered_on =  int(time.mktime(datetime.now().timetuple()) * 1000)

    def encode_auth_token(self, user_id):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.utcnow() + timedelta(days=0, seconds=15000),
                'iat': datetime.utcnow(),
                'sub': user_id
            }
            print("success")
            return jwt.encode(
                payload,
                SECRET_KEY,
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Decodes the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_token, SECRET_KEY)
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Expired'
        except jwt.InvalidTokenError:
            return None

#-----------------------------------------------------------------Tasks Table model---------------------------
class Tasks(db.Model):
    task_id = db.Column(db.String,primary_key=True)
    user = db.Column(db.Integer,unique=False,nullable=False)
    taskname = db.Column(db.String,unique=False, nullable=False)
    deadline = db.Column(db.BigInteger)
    start = db.Column(db.BigInteger)
    end = db.Column(db.BigInteger)
    duration = db.Column(db.BigInteger)
    status = db.Column(db.String)
    collaborators = db.Column(db.String)
    location = db.Column(db.String)
    owner = db.Column(db.Integer)
    priority = db.Column(db.Integer)
    subtasks = db.Column(db.String)
    repetition = db.Column(db.String)
    category = db.Column(db.String)

    def __init__(self,id,user,name,deadline,start_time,end_time,location='',priority=0,collaborators=[],subtasks=None):
        self.task_id = str(id)+str(user)
        self.user=user
        self.taskname=name
        self.deadline=deadline
        self.start=start_time
        self.end = end_time
        self.duration=0
        self.priority=priority
        self.subtasks=subtasks
        self.status=None
        self.repetition=None
        self.collaborators= '1'+','.join(str(e) for e in collaborators)
        self.owner = user
        self.location=location

db.create_all()


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

""" OAuth Session creation """

def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            state=state,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth

def get_username():
  user = Users.query.get(session["user_id"])
  username = user.name.split()[0]
  return username

#------------------------------------------------------------------------Login---------------------------------------
@app.route('/login', methods=["GET", "POST"])
def login():
    data = request.get_json(force=True)
    dataDict = data
    print(dataDict)
    if not dataDict:
        return 'Login Failed'
    user_data = data
    #name = user_data['name']
    email = user_data['email']
    avatar = user_data['provider_pic']
    user = Users.query.filter_by(email=email).first()
    if not user:
        try:
            name = user_data['name']
            user = Users(name,email,avatar)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            responseObject  = {
            'status':'fail',
            'message':'Some error occurred'
            }
            return make_response(jsonify(responseObject)),401
    auth_token = user.encode_auth_token(user.user_id)
    responseObject = {
    'status':'success',
    'message':'Successfully registered',
    'auth_token': auth_token.decode()
    }
    return make_response(jsonify(responseObject)),201

#------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/calendar/sync',methods=['POST','GET'])
def sync():
  if request.method == 'POST':
    global user_id
    auth_token = request.headers['Authorization']
    user_id = Users.decode_auth_token(auth_token)
    print("\nuser_id:",user_id,"\n")
    if not user_id:
      return 'Sync Failed:InvalidTokenError'
    #return 'sync authenticated'

  if 'credentials' not in session:
    return redirect('authorize')

  try:
    if not user_id:
        return 'Sync Failed:InvalidTokenError'
  except:
    return redirect(home_page)
  # Load credentials from the session.
  credentials = google.oauth2.credentials.Credentials(
      **session['credentials'])

  calendar = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

  #files = drive.files().list().execute()

  now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    #print('Getting the upcoming 10 events')
  # Save credentials back to session in case access token was refreshed.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  events = []
  session['credentials'] = credentials_to_dict(credentials)
  page_token = None
  while True:
    calendar_list = calendar.calendarList().list(pageToken=page_token).execute()

    for calendar_list_entry in calendar_list['items']:
        eventsResult = calendar.events().list(
              calendarId=calendar_list_entry['id'], timeMin=now, maxResults=20, singleEvents=True,
              orderBy='startTime').execute()

        for i in eventsResult.get('items', []):
            events.append(i)
        #print(calendar_list_entry['id'])
    page_token = calendar_list.get('nextPageToken')
    if not page_token:
        break

  for i in events:
    try:
        tasks = {'id':i['id'],'name':i['summary'],'start_time':datetime_to_milliseconds(i['start']['dateTime']),'end_time':datetime_to_milliseconds(i['end']['dateTime'])}
        print(i['start']['dateTime'],'\n',datetime_to_milliseconds(i['start']['dateTime']))
        db.session.add(Tasks(tasks['id'],user_id,tasks['name'],0,tasks['start_time'],tasks['end_time'],""))
        db.session.commit()
    except KeyError:                                                            #!!!! Task ID collision may lead to sync losses for two different users with same task ids!
        print('keyerror at:', i)
    except IntegrityError:
            db.session.rollback()
            # Don't stop the stream, just ignore the duplicate.
            print("Duplicate entry detected!")
  return redirect(home_page)


@app.route('/authorize')
def authorize():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

  flow.redirect_uri = url_for('oauth2callback', _external=True)

  authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

  # Store the state so the callback can verify the auth server response.
  session['state'] = state

  return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = session['state']

  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
  flow.redirect_uri = url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  session['credentials'] = credentials_to_dict(credentials)

  return redirect(url_for('sync'))

#------------------------------------------------------------------------Add----------------------------------------------------
@app.route('/add',methods=["POST"])
def add():
    auth_token = request.headers['Authorization']
    user_id = Users.decode_auth_token(auth_token)
    task = request.get_json(force=True)
    if not task['start']:
        task['start'] = 1000000000
    db.session.add(Tasks(task['task_id'],user_id,task['taskname'],task['deadline'],task['start'],task['end'],task['location']))
    db.session.commit()
    return "Task Successfully Added"

#------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/tasks',methods=['GET'])
def tasks():
    auth_token = request.headers['Authorization']
    user_id = Users.decode_auth_token(auth_token)

    tasklist = [i.__dict__ for i in Tasks.query.filter_by(user=user_id).order_by(Tasks.start)]
    tasklist = [i for i in tasklist if i['status'] not in ('deleted','complete')]
    index=0
    for i in tasklist:
        i.pop('_sa_instance_state')
        if i['status'] in ('complete','deleted'):
            tasklist.remove(i)
        try: i['subtasks']=i['subtasks'].split(',')
        except:
            i['subtasks']=[]
            print('subtask conversion error')
        index += 1
    tasks = sorted(tasklist, key=itemgetter('start'))
    return jsonify(tasks)

@app.route('/alltasks',methods=['GET'])
def history():
    auth_token = request.headers['Authorization']
    user_id = Users.decode_auth_token(auth_token)

    tasklist = [i.__dict__ for i in Tasks.query.filter_by(user=user_id).order_by(Tasks.start)]
    index=0
    for i in tasklist:
        i.pop('_sa_instance_state')

        try: i['subtasks']=i['subtasks'].split(',')
        except:
            i['subtasks']=[]
            print('subtask conversion error')
        index += 1
    tasks = sorted(tasklist, key=itemgetter('start'))
    return jsonify(tasks)
#-----------------------------------------------------------------------------------------------------------------------------------------------
@app.route("/update",methods=['POST'])
def update():
    data = request.get_json(force=True)
    auth_token = request.headers['Authorization']
    user_id = Users.decode_auth_token(auth_token)
    data = request.get_json(force=True)
    for i in range(len(data)):
        task = Tasks.query.filter_by(user=user_id,task_id=data[i]['task_id']).first()
        task.status = data[i]['status']
        #print(data[i]['subtasks'])
        list1 = data[i]['subtasks']
        str1 = ','.join(str(e) for e in list1)
        task.subtasks = str1
        db.session.commit()
    return "update success"

#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/slots',methods=['POST'])
def get_slots():
    auth_token = request.headers['Authorization']
    user_id = Users.decode_auth_token(auth_token)
    meeting_data = request.get_json(force=True)
    duration = meeting_data['duration']
    start = meeting_data['startSearch']
    end = meeting_data['endSearch']
    emails = meeting_data['emails']
    print(duration,start,end,emails)
    usertasks = [i.__dict__ for i in Tasks.query.filter_by(user=user_id).order_by(Tasks.start)]
    userlist = [Users.query.filter_by(email=i).first().user_id for i in emails]
    userlist_tasklist = [[i.__dict__ for i in Tasks.query.filter_by(user=j).order_by(Tasks.start)] for j in userlist]
    print([*userlist_tasklist,usertasks])
    free_slot_list = [get_free_slots(i,duration,start,end) for i in [*userlist_tasklist,usertasks]]

    meeting_slots = get_meeting_slot(free_slot_list,duration,start,end)
    if len(meeting_slots)>15:
        meeting_slots = meeting_slots[0:15]
    return jsonify(meeting_slots)

#-------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/getCollabs',methods=['POST'])
def get_collabs():
    auth_token = request.headers['Authorization']
    user_id = Users.decode_auth_token(auth_token)
    meeting_data = request.get_json(force=True)
    emails = meeting_data['emails']
    userlist=[]
    for i in emails:
        userlist.append([j.__dict__ for j in Users.query.filter_by(email=i)])

    for j in userlist:
        for i in j:
            i.pop('_sa_instance_state')
    if not len(userlist[-1]):
        raise ValueError('No user found')
        
    return jsonify(userlist)

def datetime_to_milliseconds(date_time):
    dtobj = dateutil.parser.parse(date_time)
    mill = int(time.mktime(dtobj.timetuple()) * 1000)
    #epoch = datetime.utcfromtimestamp(0)
    #mill = int(dtobj.strftime("%s"))*1000
    return mill

#turn off debug when deploying
if __name__ == '__main__':
    app.run(debug=True)
