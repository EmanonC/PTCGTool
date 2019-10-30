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
        return render_template('add_cards.html')
    else:
        for i in range(3):
            SetNumber = request.form.get('SetNumber' + str(i))
            CardNumber = request.form.get('CardNumber' + str(i))
            NumberofCards = request.form.get('NumberofCards' + str(i))
            StorePlace = request.form.get('StorePlace' + str(i))
            PullFrom=request.form.get('Pull' + str(i))
            if SetNumber and CardNumber and NumberofCards and StorePlace:
                dbSet = models.Set.query.filter_by(set_ind = SetNumber).first()
                dbCard = models.Card.query.filter_by(set_id = dbSet.id,card_number = CardNumber).first()
                print(dbCard.card_name)

                dbCollectedCards = models.CollectedCards(
                    pull_from=PullFrom, store_at=StorePlace,
                    number_of_cards=int(NumberofCards), card_id=dbCard.id,owner_id=uid
                )
                db.session.add(dbCollectedCards)
                db.session.commit()
        return render_template('add_cards.html')



@app.route('/viewcards')
def preview():
    return 'Preview'


@app.route('/logout', methods=["GET", "POST"])
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/scripts')
def scripts():
    return render_template('scripts.html')

@app.route('/scripts/spider')
def UploadAll():
    k=[5,6,7,8,9,10,11]
    for i in k:
        UploadSMSet(i)

    re = models.Card.query.filter(models.Card.set_id == '1').all()
    print([i.card_name for i in re])


def UploadSMSet(SetIndex):
    SMSet = SPSet(SetIndex)
    SMSet.getAllCards()
    dbSet = models.Set(
        set_name=SMSet.DefaultName[int(SetIndex)], set_code=SMSet.DefaultCode[int(SetIndex)],
        set_ind=str(SetIndex), series='SM'
    )
    db.session.add(dbSet)
    db.session.commit()
    for card in SMSet.Cards:
        dbCard = models.Card(
            card_number=str(card.CardNumber), card_name=card.data.get('Name'), card_type=card.data.get('Type'),
            card_subtype=card.data.get('Subtype'), card_rarity=card.data.get('Rare'), is_standard=1
        )
        dbCard.set_id = dbSet.id
        db.session.add(dbCard)
        db.session.commit()

        if card.data.get('Type') == 'Pokemon':
            dbStats = models.PokemonStats(
                pokemon_type=card.data.get('PokemonType'), weakness=card.data.get('Weakness'),
                resistance=card.data.get('Resistance'), retreat=card.data.get('Retreat'),
                hp=int(card.data.get('Hp'))
            )
            if card.data.get('Ability'):
                dbStats.ability_name = card.data.get('AbilityName')
                dbStats.ability_text = card.data.get('AbilityText')
            dbStats.card_id = dbCard.id
            db.session.add(dbStats)
            db.session.commit()

            moves = card.data.get('Move')
            for move in moves:
                dbMoveText = models.MoveText(
                    energy_cost=move.get('EnergyCost'), move_name=move.get('MoveName'),
                    move_damage=move.get('Damage'), move_text=move.get('Text')
                )
                dbMoveText.card_id = dbCard.id
                db.session.add(dbMoveText)
                db.session.commit()
        else:
            dbCardText = models.CardText(
                text=card.data.get('Text')
            )
            dbCardText.card_id = dbCard.id
            db.session.add(dbCardText)
            db.session.commit()
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