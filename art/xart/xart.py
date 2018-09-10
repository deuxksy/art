import json
import logging.config
import os
import random
import time
import traceback
from datetime import datetime
from time import gmtime, strftime

from robobrowser import RoboBrowser

from art import PROJECT_HOME
from art.xart import Art, Model


class XArt:
    browser = None
    logger = None
    picture = None
    video = None
    art_dict = []

    def __init__(self, picture=None, video=None):
        self.browser = RoboBrowser(history=True,
                                   user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
                                   parser="lxml")

        logging.config.fileConfig('{}/resources/logging.ini'.format(PROJECT_HOME))
        self.logger = logging.getLogger(os.path.basename(__file__).split('.')[0])
        self.video = video
        self.picture = picture

        if not os.path.exists(self.picture):
            os.makedirs(self.picture)
        if not os.path.exists(self.video):
            os.makedirs(self.video)

    def login(self, username, password, cookie=None):
        if not (username and password):
            # self.browser.session.cookies.update(cookie)
            self.logger.debug('cookie')
        else:
            self.browser.open('https://www.x-art.com/members/')
            form = self.browser.get_form(action='/auth.form')
            form['uid'].value = username
            form['pwd'].value = password
            self.browser.submit_form(form)
            self.logger.debug('login')
        self.browser.open('https://www.x-art.com/members/models/')

    def next_model_list(self, index=0, a_element=None, model_dict={}):
        try:
            self.logger.debug('list-{}'.format(self.browser.url))
            print(self.browser, index, a_element, model_dict)

            time.sleep(random.randint(2, 3))
            self.browser.follow_link(a_element)
            self.logger.debug('list-{}'.format(self.browser.url))
            model_div_list = self.browser.find_all('div', class_="browse-item")
            model_dict.update(self.get_model_list(model_div_list))
            # art > model > list 로 2번 back
            # browser.back(2)
            self.browser.follow_link(a_element)
            self.logger.debug('back-{}'.format(self.browser.url))
            next_a_element = self.browser.find('li', attrs={'class': 'current'}).next_sibling.next_sibling.find('a')
            if next_a_element and ('Next' not in next_a_element.text.strip()):
                self.next_model_list(index + 1, next_a_element, model_dict)
        except Exception:
            self.logger.error('error-{}'.format(self.browser.url))
            traceback.print_exc()
        return model_dict

    def get_model_list(self, model_div_list):
        model_dict = {}
        index = 0
        self.browser.follow_link(model_div_list[0].parent)
        for model_div in model_div_list:
            try:
                if model_div:
                    # profile img url
                    profile = model_div.find('img', attrs={'class': 'model-img'}).attrs['src']
                    # model name
                    name = model_div.find('div', attrs={'class', 'item-header'}).find('h1').text.strip()
                    # model age/country
                    h2_text_array = model_div.find('div', attrs={'class', 'item-header'}).find('h2').text.split('/')
                    # age
                    age = h2_text_array[0].strip(' Years')
                    # country
                    country = h2_text_array[1].strip()
                    # model a tag element
                    model_a_element = model_div.parent
                    # model URL
                    url = model_a_element.attrs['href']
                    model_dict[name] = Model(name, age, country, profile, url).__dict__
                    self.get_model(model_a_element)
            except Exception:
                self.logger.error("{},{},{}".format(index, name, self.browser.url))
                traceback.print_exc()
            index += 1
        return model_dict

    def get_model(self, a_element):
        time.sleep(random.randint(1, 2))
        self.browser.follow_link(a_element)
        self.logger.debug('model-{}'.format(self.browser.url))

        tags = self.more_art()
        ul = self.browser.find('ul', attrs={'id': 'allupdates'})
        for tag in tags:
            ul.append(tag)

        for li in ul.find_all('li'):
            # art a tag element
            a_element = li.find('a')
            thumbnail = li.find('img').get('src')
            publish = li.find_all('h2')[1].text
            self.get_art(a_element, thumbnail, datetime.strptime(publish, '%b %d, %Y'))

    def get_art(self, a_element, thumbnail, publish):
        time.sleep(random.randint(1, 2))
        self.browser.follow_link(a_element)
        self.logger.debug('art-{}'.format(self.browser.url))
        div_list = self.browser.find_all('div', attrs={'class': 'small-12 medium-12 large-12 columns'})
        title = div_list[0].find('h1').text.replace('?', '')
        featuring = div_list[0].find('h2').text.strip('featuring ').replace(' ', '').split('|')
        feature_list = ','.join(featuring)
        url = self.browser.url
        kind = url.split('/')[4]
        download = []
        support = []

        if kind == 'galleries':
            last_a_element = None
            for a in self.browser.find('ul', attrs={'id': 'drop-download'}).find_all('a'):
                support.append(a.text.replace('\xa0', '').replace(' ', '').replace('\n', '').replace(')', ') '))
                download.append(a.attrs['href'])
                last_a_element = a
            folder = '{}/{}-{}'.format(self.picture, feature_list, title)
            if not os.path.exists(folder):
                filename = '{}.zip'.format(folder)
                if not os.path.exists(filename):
                    before = time.time()
                    response = self.browser.session.get(download[-1], stream=True)
                    after = time.time()
                    self.logger.debug('time-{}-{}'.format(kind, after - before))
                    with open(filename.format(title), 'wb') as io:
                        try:
                            io.write(response.content)
                        except Exception:
                            self.logger.error('error-{}-{}-{}'.format(featuring, title, url))
                            traceback.print_exc()
                        else:
                            self.logger.debug('write-{}'.format(filename))
                        # io.write(response.content)
                else:
                    self.logger.debug('exists-{}'.format(filename))

        elif kind == 'videos':
            for a in div_list[2].find('ul', attrs={'id': 'drop-download'}).find_all('a'):
                support.append(a.text.replace('\xa0', '').replace(' ', '').replace('\n', '').replace(')', ') '))
                download.append(a.attrs['href'])
            fourK = ['MP4-4K' in _support for _support in support]
            support_index = 0
            file_download_url = ''
            if True in fourK:
                file_download_url = download[fourK.index(True)]
                support_index = fourK.index(True)
            else:
                file_download_url = download[0]
                support_index = 0

            filename = '{}/{}-{}.{}'.format(self.video, feature_list, title, file_download_url.split('.')[-1][0:3])
            if not os.path.exists(filename):
                before = time.time()
                response = self.browser.session.get(file_download_url, stream=True)
                after = time.time()
                self.logger.debug('time-{}-{}-{}'.format(kind, support[support_index], after - before))

                with open(filename.format(title), 'wb') as io:
                    try:
                        io.write(response.content)
                    except Exception:
                        self.logger.error('error-{}-{}-{}'.format(featuring, title, url))
                        traceback.print_exc()
                    else:
                        self.logger.debug('write-{}'.format(filename))
                    # io.write(response.content)
            else:
                self.logger.debug('exists-{}'.format(filename))

        self.art_dict['{}-{}'.format(kind, title)] = Art(title=title, kind=kind, url=url, featuring=featuring,
                                                         support=support,
                                                         download=download, publish=publish.strftime('%Y-%m-%d'),
                                                         thumbnail=thumbnail).__dict__
        # go baack art list
        self.browser.back()

    def more_art(self, tags=[], page=1, model_id=None):
        from bs4 import BeautifulSoup
        from bs4.element import Tag

        time.sleep(random.randint(1, 2))

        if not model_id:
            model_id = self.browser.find('input', attrs={'id': 'id_model'}).get('value')
        netxt_url = 'https://www.x-art.com/members/index.php?show=model&pref=detitems&page={}&modelid={}'.format(page,
                                                                                                                 model_id)
        response = self.browser.session.get(netxt_url)
        data = response.json()
        if data['html']:
            try:
                soup = BeautifulSoup(data['html'], "lxml")
                for i, child in enumerate(soup.body.children):
                    if isinstance(child, Tag):
                        tags.append(child)
            except Exception:
                self.logger.error(data)
                traceback.print_exc()

        if int(data['next']) > 1:
            return self.more_art(tags, data['next'], model_id)
        return tags

    def save_model(self, model_dict):
        with open('./config/model.{}.json'.format(strftime("%y%m%d%H%M%S", gmtime())), 'w') as io:
            json.dump(model_dict, io)

    def save_art(self, art_dict):
        with open('./config/art.{}.json'.format(strftime("%y%m%d%H%M%S", gmtime())), 'w') as io:
            json.dump(art_dict, io)