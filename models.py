from exts import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class StorePlace(db.Model):
    __tablename__ = 'store_place'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200))
    type=db.Column(db.String(200))


class CollectedCards(db.Model):
    __tablename__ = 'collected_cards'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pull_from = db.Column(db.String(200))

    number_of_cards = db.Column(db.Integer, nullable=False)

    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))

    store_at  = db.Column(db.Integer, db.ForeignKey('store_place.id'))
    store_palce = db.relationship('StorePlace', backref=db.backref('storedcards'))

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref=db.backref('cards'))




class Set(db.Model):
    __tablename__ = 'set'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    set_name = db.Column(db.String(200), nullable=False)
    set_code = db.Column(db.String(200), nullable=False)
    set_ind=db.Column(db.String(20), nullable=False)
    series = db.Column(db.String(200), nullable=False)
    release_data = db.Column(db.DATE)


class Card(db.Model):
    __tablename__ = 'card'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    card_number = db.Column(db.String(200), nullable=False)

    card_name = db.Column(db.String(200), nullable=True)
    card_type = db.Column(db.String(200), nullable=True)
    card_subtype = db.Column(db.String(200), nullable=True)
    card_rarity = db.Column(db.String(200), nullable=True)

    is_standard = db.Column(db.Integer)

    set_id = db.Column(db.Integer, db.ForeignKey('set.id'))
    fromset = db.relationship('Set', backref=db.backref('cards'))


class CardText(db.Model):
    __tablename__ = 'card_text'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text, nullable=False)

    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))
    fromcard = db.relationship('Card', backref=db.backref('TrEnTexts'))

class MoveText(db.Model):
    __tablename__ = 'move_text'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    energy_cost = db.Column(db.String(200), nullable=False)
    move_name = db.Column(db.String(200), nullable=False)
    move_damage = db.Column(db.String(20), nullable=True)
    move_text = db.Column(db.Text, nullable=True)


    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))
    fromcard = db.relationship('Card', backref=db.backref('moves'))

class PokemonStats(db.Model):
    __tablename__ = 'pokemon_stats'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    pokemon_type = db.Column(db.String(200), nullable=True)
    weakness = db.Column(db.String(200), nullable=True)
    resistance = db.Column(db.String(200), nullable=True)
    retreat = db.Column(db.String(200), nullable=True)
    hp = db.Column(db.Integer, nullable=True)

    ability_name = db.Column(db.String(200), nullable=True)
    ability_text = db.Column(db.Text, nullable=True)

    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))
    fromcard = db.relationship('Card', backref=db.backref('stats'))
