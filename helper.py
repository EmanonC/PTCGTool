import models
from flask import request


class CardUploader:
    def __init__(self, form, db, uid):
        self.form = form
        self.db = db
        self.uid = uid

    def setForm(self, form):
        self.form = form

    def UpoladCard(self):
        for i in range(3):
            SetCode = self.form.get('SetCode' + str(i))
            # SetNumber = self.form.get('SetNumber' + str(i))
            CardNumber = self.form.get('CardNumber' + str(i))
            NumberofCards = self.form.get('NumberofCards' + str(i))
            StorePlace = self.form.get('StorePlace' + str(i))
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

class staData:
    def __init__(self):
        self.__SetName = ['Sun & Moon', 'Guardians Rising', 'Burning Shadows', 'Crimson Invasion',
           'Ultra Prism', 'Forbidden Light', 'Celestial Storm', 'Lost Thunder', 'Team Up',
           'Unbroken Bonds', 'Unified Minds']
        self.__SetCode = ['SUM', 'GRI', 'BUS', 'CIN', 'UPR', 'FLI', 'CES', 'LOT', 'TEU', 'UNB', 'UNM']
        self.__SetRank=[_ for _ in range(len(self.__SetName))]


        # print(self.__SetCode)
    def getContextforAdding(self):
        mid=zip(self.__SetRank,self.__SetCode,self.__SetName)
        mid=sorted(mid,reverse=True)
        self.__SetRank,self.__SetCode,self.__SetName=list(zip(*mid))
        context={
            'nofRow': [_ for _ in range(5)],
            'Sets':[{'SetCode':self.__SetCode[i],'SetName':self.__SetName[i]} for i in range(len(self.__SetRank))]
        }
        return context

