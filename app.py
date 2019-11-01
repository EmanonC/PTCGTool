from flask import render_template, flash, request, redirect, url_for, session, jsonify, Flask
import models
from exts import db
from PTCGSpider import SPSet, SPCard
import config, datetime, pymysql
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import os
from helper import CardUploader, staData,StackCreater,SMSet

app = Flask(__name__)
app.config.from_object(config)

db.init_app(app=app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('user'))

    return render_template('index.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    # login page
    # verify the username and password provided by the user
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        candidate_user = models.User.query.filter_by(username=username).first()
        uid = candidate_user.id
        try:
            candidate_user.username
        except:
            return render_template('login.html', p=1)
        if check_password_hash(candidate_user.password, password + username):
            session['user'] = username
            session['uid'] = uid
            session.permanent = True
            # after 24 hours, users are required to reenter their usernames and passwords for security purposes
            app.permanent_session_lifetime = timedelta(minutes=1440)
            return redirect(url_for('user', username=username))
        else:
            flash('Invalid username or password')
            return render_template('login.html', p=1)
    else:
        return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # registration page
    # On the server side, check whether the username and password are valid or not.
    # username and password must be strings between 2 to 100 characters
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        context = {
            'username_valid': 0,
            'password_valid': 0,
            'pawconfirm_valid': 0,
            'username': username
        }

        flag = False
        if not 2 <= len(username) <= 100:
            context['username_valid'] = 1
            flag = True

        if password != confirm_password:
            context['password_valid'] = 1
            flag = True

        if not 2 <= len(password) <= 100:
            context['password_valid'] = 2
            flag = True

        # users are not allowed to have same username
        dup_user = models.User.query.filter_by(username=username).first()
        if dup_user:
            context['username_valid'] = 2
            flag = True

        if flag:
            return render_template('signup.html', **context)

        # Different users are allowed to have the same password
        # After using salt value for storing passwords, they will look completely different on the server(database)
        # even though they are the same
        password = generate_password_hash(password + username)
        candidate_user = models.User(username=username, password=password)
        db.session.add(candidate_user)
        db.session.commit()
        # two directories are created to store the images later uploaded by the user
        # log in
        session['user'] = username
        session['uid'] = candidate_user.id
        return redirect(url_for('user'))
    context = {
        'username_valid': -1,
        'password_valid': -1,
        'pawconfirm_valid': -1
    }
    return render_template('signup.html', **context)


@app.route('/user', methods=["GET", "POST"])
def user():
    # if the user are not logged in, redirect to the login page
    if 'user' not in session:
        return redirect(url_for('index'))
    username = session['user']
    return render_template('user.html', user=username)


@app.route('/uploadcard', methods=['GET', 'POST'])
def uploadcard():
    if 'user' not in session:
        return redirect(url_for('index'))
    uid = session['uid']

    if request.method == 'GET':
        data = staData()
        context = data.getContextforAdding()
        return render_template('add_cards.html', **context)

    else:
        context = {
            'form': request.form,
            'db': db,
            'uid': uid
        }
        cd = CardUploader(**context)
        cd.UpoladCard()
        data = staData()
        context = data.getContextforAdding()
        return render_template('add_cards.html', **context)


@app.route('/viewcards')
def preview():
    return 'Preview'

@app.route('/createstack', methods=["GET", "POST"])
def CreateStack():
    if 'user' not in session:
        return redirect(url_for('index'))
    uid = session['uid']
    data=staData()
    context=data.getType()
    if request.method == 'GET':
        return render_template('create_stacks.html',**context)
    else:
        context2 = {
            'form': request.form,
            'db': db,
            'uid': uid
        }
        cs=StackCreater(**context2)
        cs.CreateStack()
        return render_template('create_stacks.html',**context)

@app.route('/logout', methods=["GET", "POST"])
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


@app.route('/scripts')
def scripts():
    contex = {
        'msg': 'Scripts'
    }
    return render_template('scripts.html', **contex)


@app.route('/scripts/spider')
def UploadAll():
    k = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    # k=[1]
    Tool=SMSet(db=db)
    for i in k:
        Tool.UploadSingleSet(i)
    contex = {
        'msg': 'Success'
    }
    return render_template('scripts.html', **contex)







# @app.route('/mupload')
# def ManullyUpload():
#     SetName='Cosmic Eclipse'
#     SetCode='COE'
#     SetMax=236
#     SerInd=12
#     SetSeries = 'SM'
#     dbSet = models.Set(
#         set_name=SetName, set_code=SetCode,
#         set_ind=str(SerInd), series=SetSeries
#     )
#     db.session.add(dbSet)
#     db.session.commit()
#     for i in range(SetMax):
#         dbCard = models.Card(
#             card_number=str(i+1),  is_standard=1
#         )
#         dbCard.set_id = dbSet.id
#         db.session.add(dbCard)
#         db.session.commit()
#     return ('Success')


if __name__ == '__main__':
    app.run()
    # re = models.Card.query.filter(models.Card.set_id == '1').all()[0]
    # print(re.card_name)
