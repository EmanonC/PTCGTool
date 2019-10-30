import models
from flask import request

class CardUploader:
    def __init__(self,form,db,uid):
        self.form=form
        self.db=db
        self.uid=uid

    def setForm(self,form):
        self.form=form

    def UpoladCard(self):
        for i in range(3):
            Series = self.form.get('Series' + str(i))
            SetNumber = self.form.get('SetNumber' + str(i))
            CardNumber = self.form.get('CardNumber' + str(i))
            NumberofCards = self.form.get('NumberofCards' + str(i))
            StorePlace = self.form.get('StorePlace' + str(i))
            PullFrom = self.form.get('Pull' + str(i))

            if SetNumber and CardNumber and NumberofCards and StorePlace:
                dbSet = models.Set.query.filter_by(set_ind=SetNumber, series=Series).first()
                dbCard = models.Card.query.filter_by(set_id=dbSet.id, card_number=CardNumber).first()
                print(dbCard.card_name)

                dbCollectedCards = models.CollectedCards(
                    pull_from=PullFrom, store_at=StorePlace,
                    number_of_cards=int(NumberofCards), card_id=dbCard.id, owner_id=self.uid
                )
                self.db.session.add(dbCollectedCards)
                self.db.session.commit()
            print(Series)