import models
from PTCGSpider import SPSet, SPCard
from flask import request
import pickle
import sys

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
            StorePlace =int( self.form.get('StorePlace' + str(i)))
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
                          'Unbroken Bonds', 'Unified Minds']
        self.__SetCode = ['SUM', 'GRI', 'BUS', 'CIN', 'UPR', 'FLI', 'CES', 'LOT', 'TEU', 'UNB', 'UNM']
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

class tool:
    def __init__(self,db):
        self.db=db


class SMSet(tool):
    def UploadSingleSet(self,SetIndex):
        self.SetIndex = SetIndex
        self.getSMSetbySpider()
        self.__UploadSMSet()

    def getSMSetbySpider(self):

        sys.setrecursionlimit(15000)
        self.SMSet = SPSet(self.SetIndex)
        self.SMSet.getAllCards()
        path='static/PTCGdata/'
        f = open(path+str(self.SetIndex)+'.dat', 'wb')
        pickle.dump(self.SMSet, f)
        f.close()

    def getSMSetbydat(self):
        path = 'static/PTCGdata/'
        f = open(path + str(self.SetIndex) + '.dat', 'rb')
        self.SMSet=pickle.load(f)
        f.close()
        print('Finish Pickle load {}'.format(self.SetIndex))

    def __UploadSMSet(self):
        SMSet = self.SMSet
        SetIndex=self.SetIndex
        db=self.db
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
# data=[1,2,3,4]
# path = 'static/PTCGdata/'
# f = open(path + '2' + '.dat', 'wb')
# pickle.dump(data, f)
# f.close()
#
# f = open(path + '1' + '.dat', 'rb')
# d = pickle.load(f)
# f.close()
# print(d)