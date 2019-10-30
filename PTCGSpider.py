import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pickle
import os
import urllib
import time
import random
import pymysql


class SPCard:
    def __init__(self, SetName, CardNumber):
        self.SetName = SetName
        self.CardNumber = CardNumber
        self.soup = None

    def __requestSoup(self, url, Cookie=None, headers=None):
        def soup_content(soup):
            html = soup.content
            return BeautifulSoup(html, 'html.parser')

        soup = requests.get(url=url, cookies=Cookie, headers=headers)
        cnt = 0
        while soup.status_code != 200:
            time.sleep(60)
            soup = requests.get(url=url, cookies=Cookie, headers=headers)
            cnt += 1
            if cnt % 5 == 0:
                time.sleep(1200)
                print('休息20min')
            if cnt == 14:
                time.sleep(1800)
                print('休息30min')
            if cnt % 15 == 0:
                print(soup.status_code)
                print(soup_content(soup).get_text)
                raise Exception(soup.status_code)
        soup = soup_content(soup)
        return soup

    def CardUrl(self):
        # sm series
        return 'https://www.pokemon.com/us/pokemon-tcg/pokemon-cards/sm-series/{}/{}/'.format(self.SetName,
                                                                                              self.CardNumber)

    def getCardSoup(self):
        url = self.CardUrl()
        try:
            self.soup = self.__requestSoup(url=url)
        except:
            print('Failed')

    def getCardType(self):
        if not self.soup:
            self.getCardSoup()

        if self.soup:

            # print('')

            self.data = {}
            name = self.soup.find('div', attrs={'class': 'card-description'}).find('h1').get_text()
            self.data['Name'] = name

            # img = self.soup.find('div', attrs={'class': 'column-6'})
            # img=img.find('img').get('src')
            # self.data['ImgUrl'] = img
            # print('img:',img)

            type = self.soup.find('div', attrs={'class': 'card-type'}).find('h2').get_text()
            type=type.strip()

            if 'Pokémon' in type and 'Trainer' not in type:
                HpType = self.soup.find('div', attrs={'class': 'right'})
                Hp = HpType.find('span').get_text().replace('HP', '')
                PokemonType = HpType.find('i')['class'][1].replace('icon-', '')
                self.data['PokemonType'] = PokemonType
                self.data['Hp'] = Hp
                # print(Hp, PokemonType)
                self.data['Type'] = 'Pokemon'

                if type == 'Basic Pokémon':
                    self.data['Subtype'] = 'Basic'
                if type == 'Stage 1 Pokémon':
                    self.data['Subtype'] = 'Stage 1'
                if type == 'Stage 2 Pokémon':
                    self.data['Subtype'] = 'Stage 2'
                if type == 'Pokémon-GX':
                    self.data['Subtype'] = 'GX'
                if type == 'Pokémon-TAG TEAM':
                    self.data['Subtype'] = 'TAG TEAM'

            elif 'Trainer' in type:
                self.data['Type'] = 'Trainer'
                if 'Supporter' in type:
                    self.data['Subtype'] = 'Supporter'
                if 'Item' in type:
                    self.data['Subtype'] = 'Item'
                if 'Stadium' in type:
                    self.data['Subtype'] = 'Stadium'
                if 'Tool' in type:
                    self.data['Subtype'] = 'Pokemon Tool'
            elif type == 'Special Energy':
                self.data['Type'] = 'Energy'
                self.data['Subtype'] = 'Special Energy'


        # print('aaa')
        else:
            raise Exception('card soup not found')

    def getCardInfo(self):
        self.getCardType()
        if self.data.get('Type') == 'Pokemon':
            self.getPokemonMoves()
        else:
            self.getTrainnerEnergyText()

    def getPokemonMoves(self):
        if not self.soup:
            self.getCardSoup()

        if self.soup:
            # print('')
            # print(self.data['Name'])
            PokemonAbilities = self.soup.find('div', attrs={'class': 'pokemon-abilities'})
            Ability = PokemonAbilities.find('div', attrs={'class': 'poke-ability'})
            # Check if the pokemon has ability and get the ability
            if Ability:
                self.data['Ability'] = True
                AbilityName = PokemonAbilities.find_all('div')[1].get_text()
                self.data['AbilityName'] = AbilityName
                # print(AbilityName)
                self.data['AbilityText'] = PokemonAbilities.find('p').get_text()
                # print(self.data['AbilityText'])

            # Get Pokemon moves
            moves = PokemonAbilities.find_all('div', attrs={'class': 'ability'})
            self.data['Move']=[]
            # class:move block may contain moves info
            for move in moves:
                ul = move.find('ul')
                # ul has energy cost info, use it to check move
                if ul:
                    Move = {}
                    EnergyLi = ul.find_all('li')
                    EnergyCost = ''
                    for li in EnergyLi:
                        EnergyCost += '[{}]'.format(li['title'])
                    Move['EnergyCost'] = EnergyCost
                    Move['MoveName'] = move.find('h4').get_text()
                    Damage = move.find('span', attrs={'class': 'right plus'})
                    if Damage:
                        Move['Damage'] = Damage.get_text()
                    Move['Text'] = move.find('pre').get_text()
                    self.data['Move'].append( Move)
                    # print(self.data['Move'])

            # Pokemon Weakness Resistance and Retreat
            PokemonStats = self.soup.find('div', attrs={'class': 'pokemon-stats'})
            PokemonStats = PokemonStats.find_all('div')
            if len(PokemonStats) < 3:
                # No Weakness, Resistance and Retreat
                self.data['Weakness'] = ''
                self.data['Resistance'] = ''
                self.data['Retreat'] = ''
            else:
                # Weakness
                self.data['Weakness'] = PokemonStats[0].find('li')
                if self.data['Weakness']:
                    self.data['Weakness'] = self.data['Weakness'].get('title')

                # Resistance
                self.data['Resistance'] = PokemonStats[1].find('li')
                if self.data['Resistance']:
                    self.data['Resistance'] = self.data['Resistance'].get('title')

                # Retreat
                Retreat = PokemonStats[2].find_all('li')
                self.data['Retreat'] = ''
                for li in Retreat:
                    self.data['Retreat'] += '[{}]'.format(li['title'])

            # Other info
            StatsFooter = self.soup.find('div', attrs={'class': 'stats-footer'})
            info = StatsFooter.find('span').get_text()
            CardSet, Rare = info.split(' ', 1)
            self.data['CardNumberMax'] = CardSet.split('/')[1]
            self.data['Rare'] = Rare

    def getTrainnerEnergyText(self):
        if not self.soup:
            self.getCardSoup()

        if self.soup:
            PokemonAbilities = self.soup.find('div', attrs={'class': 'pokemon-abilities'})
            self.data['Text'] = PokemonAbilities.find('pre').get_text()

            # Other info
            StatsFooter = self.soup.find('div', attrs={'class': 'stats-footer'})
            info = StatsFooter.find('span').get_text()
            CardSet, Rare = info.split(' ', 1)
            self.data['CardNumberMax'] = CardSet.split('/')[1]
            self.data['Rare'] = Rare


class SPSet:
    def __init__(self, SetIndex):
        SetIndex='sm'+str(SetIndex)
        self.SetIndex = SetIndex
        self.DefaultName = {1:'Sun & Moon',2:'Guardians Rising',3:'Burning Shadows',4:'Crimson Invasion',5: 'Ultra Prism', 6: 'Forbidden Light', 7: 'Celestial Storm', 8: 'Lost Thunder',
                            9: 'Team Up', 10: 'Unbroken Bonds', 11: 'Unified Minds', 12: 'Cosmic Eclipse'}
        self.DefaultCode = {1:'SUM',2:'GRI',3:'BUS',4:'CIN',5: 'UPR', 6: 'FLI', 7: 'CES', 8: 'LOT', 9: 'TEU', 10: 'UNB', 11: 'UNM', 12: 'CEC'}

    def __getSetMax(self):
        card = SPCard(self.SetIndex, 1)
        card.getCardInfo()
        self.SetMax = int(card.data['CardNumberMax'])

    def getAllCards(self):
        self.Cards = []
        self.__getSetMax()
        # self.SetMax=10
        for i in range(self.SetMax):
            card = SPCard(self.SetIndex, i + 1)
            card.getCardInfo()
            self.Cards.append(card)
            print(card.data.get('Name'),' ','{}/{}'.format(i+1,self.SetMax))

    def sm11Test(self):
        self.SetIndex = 'sm11'
        self.TestCards = [171, 172, 215, 216, 210, 212, 199, 203, 207, 221, 223, 77]
        for i in self.TestCards:
            card = SPCard(self.SetIndex, i)
            card.getCardInfo()
            print('')
            print(card.data.get('Name'))
            print(card.data.get('Subtype'))


def main():
    SetNames = [11]
    set = SPSet(SetNames[0])
    set.sm11Test()
    # set.getAllCards()


if __name__ == '__main__':
    main()
