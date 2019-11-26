import models
from PTCGSpider import SPSet, SPCard
from flask import request, render_template, url_for
import pickle
import sys
from werkzeug.security import generate_password_hash, check_password_hash


class Uploader:
    def __init__(self, form, db, uid):
        self.form = form
        self.db = db
        self.uid = uid

    def setForm(self, form):
        self.form = form


class CardUploader(Uploader):
    def UpoladCard(self):
        for i in range(5):
            SetCode = self.form.get('SetCode' + str(i))
            # SetNumber = self.form.get('SetNumber' + str(i))
            CardNumber = self.form.get('CardNumber' + str(i))
            NumberofCards = self.form.get('NumberofCards' + str(i))
            StorePlace = int(self.form.get('StorePlace' + str(i)))
            PullFrom = self.form.get('Pull' + str(i))

            if SetCode and CardNumber and NumberofCards and StorePlace:
                dbSet = models.Set.query.filter_by(set_code=SetCode).first()
                dbCard = models.Card.query.filter_by(set_id=dbSet.id, card_number=CardNumber).first()

                dbCollectedCards = models.CollectedCards(
                    pull_from=PullFrom, store_at=StorePlace,
                    number_of_cards=int(NumberofCards), card_id=dbCard.id, owner_id=self.uid
                )
                self.db.session.add(dbCollectedCards)
                self.db.session.commit()


class StackCreater(Uploader):
    def CreateStack(self):
        Type = self.form.get('Type')
        StackName = self.form.get('stack_name')
        dbStorePlace = models.StorePlace(type=Type, name=StackName)
        self.db.session.add(dbStorePlace)
        self.db.session.commit()


class staData:
    def __init__(self):
        pass
        # print(self.__SetCode)

    def getContextforAdding(self):
        stacks = models.StorePlace.query.filter_by().all()
        context = {}
        StoredStacks = []
        if stacks:
            for stack in stacks:
                StoredStacks.append({'id': stack.id, 'name': stack.name})
            context.update({'Stacks': StoredStacks})
        else:
            context.update({'Stacks': [{'id': 0, 'name': 'Create a Stack First'}]})

        self.__SetName = ['Sun & Moon', 'Guardians Rising', 'Burning Shadows', 'Crimson Invasion',
                          'Ultra Prism', 'Forbidden Light', 'Celestial Storm', 'Lost Thunder', 'Team Up',
                          'Unbroken Bonds', 'Unified Minds', 'Cosmic Eclipse']
        self.__SetCode = ['SUM', 'GRI', 'BUS', 'CIN', 'UPR', 'FLI', 'CES', 'LOT', 'TEU', 'UNB', 'UNM', 'CEC']
        self.__SetRank = [_ for _ in range(len(self.__SetName))]
        mid = zip(self.__SetRank, self.__SetCode, self.__SetName)
        mid = sorted(mid, reverse=True)
        self.__SetRank, self.__SetCode, self.__SetName = list(zip(*mid))
        context.update({
            'nofRow': [_ for _ in range(5)],
            'Sets': [{'SetCode': self.__SetCode[i], 'SetName': self.__SetName[i]} for i in range(len(self.__SetRank))]
        })
        return context

    def getType(self):
        context = {
            'Types': ['Card Box', 'Deck', 'Binder']
        }
        return context


class DBtool:
    def __init__(self, db):
        self.db = db


class SMSet(DBtool):
    def UploadSingleSet(self, SetIndex):
        self.SetIndex = SetIndex
        self.getSMSetbydat()
        self.__UploadSMSet()

    def getSMSetbySpider(self):

        sys.setrecursionlimit(15000)
        self.SMSet = SPSet(self.SetIndex)
        self.SMSet.getAllCards()
        path = 'static/PTCGdata/'
        f = open(path + str(self.SetIndex) + '.dat', 'wb')
        pickle.dump(self.SMSet, f)
        f.close()

    def getSMSetbydat(self):
        path = 'static/PTCGdata/'
        f = open(path + str(self.SetIndex) + '.dat', 'rb')
        self.SMSet = pickle.load(f)
        f.close()
        print('Finish Pickle load {}'.format(self.SetIndex))

    def __UploadSMSet(self):
        SMSet = self.SMSet
        SetIndex = self.SetIndex
        db = self.db
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
            dbCard.fromset = dbSet
            dbCard.set_number = dbSet.set_ind
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


class SearchTool(DBtool):
    def __init__(self, db):
        super().__init__(db)
        self.CardPerPage = 10

    def __search_by_user(self, uid):
        user = models.User.query.filter_by(id=uid).first()
        UserCollectedCards = []
        for card in user.cards:
            card_info = models.Card.query.filter_by(id=card.card_id).first()
            set_info = models.Set.query.filter_by(id=card_info.set_id).first()
            store_info = models.StorePlace.query.filter_by(id=card.store_at).first()
            ctt = {
                'card_name': card_info.card_name,
                'set_name': set_info.set_name,
                'number': card.number_of_cards,
                'store_place': store_info.name,
                'store_place_type': store_info.type,
            }
            UserCollectedCards.append(ctt)
        return UserCollectedCards

    def __ButtonMaker(self, PageNumber, NofPages, ViewFunctionName):
        Buttons = []
        st = max(0, PageNumber - 4)
        ed = min(PageNumber+3, NofPages)
        PageLinks = []
        PageClass = []
        PageNumbers = [(_ + 1) for _ in range(st, ed)]
        # while PageNumbers[-1] < NofPages:
        #     PageNumbers.append(PageNumbers[-1] + 1)
        # while len(PageNumbers) < 9 and PageNumbers[0] > 0:
        #     PageNumbers = [PageNumbers[0] - 1] + PageNumbers
        for PageNumberi in PageNumbers:
            PageLinks.append(url_for(ViewFunctionName, page=PageNumberi))
            if PageNumberi != PageNumber:
                PageClass.append('btn-outline-primary')
            else:
                PageClass.append('btn-primary')

        for i in range(len(PageClass)):
            ctt = {
                'text': PageNumbers[i],
                'href': PageLinks[i],
                'class': PageClass[i],
            }
            Buttons.append(ctt)
        return Buttons

    def get_user_cards(self, uid, PageNumber):
        cards = self.__search_by_user(uid)
        N = len(cards)
        NofPages = N // self.CardPerPage
        if N % self.CardPerPage > 0:
            NofPages += 1
        Buttons = self.__ButtonMaker(PageNumber, NofPages, 'preview')
        context = {
            'Buttons': Buttons,
        }
        if PageNumber * self.CardPerPage > N:
            context.update({
                'Cards': cards[(NofPages - 1) * self.CardPerPage:N]
            })
        else:
            context.update({
                'Cards': cards[(PageNumber - 1) * self.CardPerPage:PageNumber * self.CardPerPage]
            })
        return context


class FormandDbtool:
    def __init__(self, form, db):
        self.form = form
        self.db = db


class SignUpHelper(FormandDbtool):
    def SignUp(self):
        form = self.form
        db = self.db
        username = form.get('username')
        password = form.get('password')
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
        return (username, candidate_user.id)
