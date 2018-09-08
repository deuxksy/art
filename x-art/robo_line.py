import os
import json
import logging.config
import random
import time
import traceback
from datetime import datetime
from time import gmtime, strftime
from robobrowser import RoboBrowser

logging.config.fileConfig('./config/logging.ini')
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])
# logger = logging.getLogger(__name__)

art_dict = {}
picture = ''
video = ''

class Model:
    name = ''
    age = -1
    country = ''
    profile = ''
    url = ''

    def __init__(self, name=None, age=None, country=None, profile=None, url=None):
        if name:
            self.name = name
        if age:
            self.age = int(age)
        if country:
            self.country = country
        if profile:
            self.profile = profile
        if url:
            self.url = url


class Art:
    title = ''
    kind = ''
    url = ''
    featuring = []
    support = []
    donwload = []
    publish = None
    thumbnail = ''

    def __init__(self, title=None, kind=None, url=None, featuring=None, support=None, download=None, publish=None,
                 thumbnail=None):
        if title:
            self.title = title
        if kind:
            self.kind = kind
        if url:
            self.url = url
        if featuring:
            self.featuring = featuring
        if support:
            self.support = support
        if download:
            self.download = download
        if publish:
            self.publish = publish
        if thumbnail:
            self.thumbnail = thumbnail


def load_cookie():
    with open('./config/cookie.json') as io:
        return json.load(io)


def login(id, password, cookie=None):
    browser = RoboBrowser(history=True,
                          user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
                          parser="lxml")
    if not(id and password):
        browser.session.cookies.update(cookie)
        logger.debug('cookie')
    else:
        browser.open('https://www.x-art.com/members/')
        form = browser.get_form(action='/auth.form')
        form['uid'].value = id
        form['pwd'].value = password
        browser.submit_form(form)
        logger.debug('login')
    browser.open('https://www.x-art.com/members/models/')
    return browser


def next_model_list(browser, index=0, a_element=None, model_dict={}):
    try:
        time.sleep(random.randint(2, 3))
        browser.follow_link(a_element)
        logger.debug('list-{}'.format(browser.url))
        model_div_list = browser.find_all('div', class_="browse-item")
        model_dict.update(get_model_list(browser, model_div_list))
        # art > model > list 로 2번 back
        # browser.back(2)
        browser.follow_link(a_element)
        logger.debug('back-{}'.format(browser.url))
        next_a_element = browser.find('li', attrs={'class': 'current'}).next_sibling.next_sibling.find('a')
        if next_a_element and ('Next' not in next_a_element.text.strip()):
            next_model_list(browser, index + 1, next_a_element, model_dict)
    except Exception:
        logger.error('error-{}'.format(browser.url))
        traceback.print_exc()
    return model_dict


def get_model_list(browser, model_div_list):
    model_dict = {}
    index = 0
    browser.follow_link(model_div_list[0].parent)
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
                get_model(browser, model_a_element)
        except Exception:
            logger.error("{},{},{}".format(index, name, browser.url))
            traceback.print_exc()
        index += 1
    return model_dict


def get_model(browser, a_element):
    time.sleep(random.randint(1, 2))
    browser.follow_link(a_element)
    logger.debug('model-{}'.format(browser.url))

    tags = more_art(browser)
    ul = browser.find('ul', attrs={'id': 'allupdates'})
    for tag in tags:
        ul.append(tag)

    for li in ul.find_all('li'):
        # art a tag element
        a_element = li.find('a')
        thumbnail = li.find('img').get('src')
        publish = li.find_all('h2')[1].text
        get_art(browser, a_element, thumbnail, datetime.strptime(publish, '%b %d, %Y'))


def get_art(browser, a_element, thumbnail, publish):
    time.sleep(random.randint(1, 2))
    browser.follow_link(a_element)
    logger.debug('art-{}'.format(browser.url))
    div_list = browser.find_all('div', attrs={'class': 'small-12 medium-12 large-12 columns'})
    title = div_list[0].find('h1').text.replace('?', '')
    featuring = div_list[0].find('h2').text.strip('featuring ').replace(' ', '').split('|')
    feature_list = ','.join(featuring)
    url = browser.url
    kind = url.split('/')[4]
    download = []
    support = []

    if kind == 'galleries':
        last_a_element = None
        for a in browser.find('ul', attrs={'id': 'drop-download'}).find_all('a'):
            support.append(a.text.replace('\xa0', '').replace(' ', '').replace('\n', '').replace(')', ') '))
            download.append(a.attrs['href'])
            last_a_element = a
        folder = '{}/{}-{}'.format(picture, feature_list, title)
        if not os.path.exists(folder):
            filename = '{}.zip'.format(folder)
            if not os.path.exists(filename):
                before = time.time()
                response = browser.session.get(download[-1], stream=True)
                after = time.time()
                logger.debug('time-{}-{}'.format(kind, after - before))
                with open(filename.format(title), 'wb') as io:
                    try:
                        io.write(response.content)
                    except Exception:
                        logger.error('error-{}-{}-{}'.format(featuring, title, url))
                        traceback.print_exc()
                    else:
                        logger.debug('write-{}'.format(filename))
                    # io.write(response.content)
            else:
                logger.debug('exists-{}'.format(filename))

    elif kind == 'videos':
        for a in div_list[2].find('ul', attrs={'id': 'drop-download'}).find_all('a'):
            support.append(a.text.replace('\xa0', '').replace(' ', '').replace('\n', '').replace(')', ') '))
            download.append(a.attrs['href'])
        fourK =['MP4-4K' in _support for _support in support]
        support_index = 0
        file_download_url = ''
        if True in fourK:
            file_download_url = download[fourK.index(True)]
            support_index = fourK.index(True)
        else:
            file_download_url = download[0]
            support_index = 0

        filename = '{}/{}-{}.{}'.format(video, feature_list, title, file_download_url.split('.')[-1][0:3])
        if not os.path.exists(filename):
            before = time.time()
            response = browser.session.get(file_download_url, stream=True)
            after = time.time()
            logger.debug('time-{}-{}-{}'.format(kind, support[support_index], after - before))

            with open(filename.format(title), 'wb') as io:
                try:
                    io.write(response.content)
                except Exception:
                    logger.error('error-{}-{}-{}'.format(featuring, title, url))
                    traceback.print_exc()
                else:
                    logger.debug('write-{}'.format(filename))
                # io.write(response.content)
        else:
            logger.debug('exists-{}'.format(filename))

    art_dict['{}-{}'.format(kind, title)] = Art(title=title, kind=kind, url=url, featuring=featuring, support=support,
                                                download=download, publish=publish.strftime('%Y-%m-%d'),
                                                thumbnail=thumbnail).__dict__
    # go baack art list
    browser.back()


def more_art(browser, tags=[], page=1, model_id=None):
    from bs4 import BeautifulSoup
    from bs4.element import Tag

    time.sleep(random.randint(1, 2))

    if not model_id:
        model_id = browser.find('input', attrs={'id': 'id_model'}).get('value')
    netxt_url = 'https://www.x-art.com/members/index.php?show=model&pref=detitems&page={}&modelid={}'.format(page, model_id)
    response = browser.session.get(netxt_url)
    data = response.json()
    if data['html']:
        try:
            soup = BeautifulSoup(data['html'], "lxml")
            for i, child in enumerate(soup.body.children):
                if isinstance(child, Tag):
                    tags.append(child)
        except Exception:
            logger.error(data)
            traceback.print_exc()

    if int(data['next']) > 1:
        return more_art(browser, tags, data['next'], model_id)
    return tags


def save_model(model_dict):
    with open('./config/model.{}.json'.format(strftime("%y%m%d%H%M%S", gmtime())), 'w') as io:
        json.dump(model_dict, io)


def save_art(art_dict):
    with open('./config/art.{}.json'.format(strftime("%y%m%d%H%M%S", gmtime())), 'w') as io:
        json.dump(art_dict, io)


def init():
    if not os.path.exists(picture):
        os.makedirs(picture)
    if not os.path.exists(video):
        os.makedirs(video)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--id', help='usename')
    parser.add_argument('--password', help='password')
    parser.add_argument('--picture', default='../data/picture', help='picture save folder')
    parser.add_argument('--video', default='../data/video', help='video save folder')
    args = parser.parse_args()

    picture = args.picture
    video = args.video

    init()

    browser = login(args.id, args.password, load_cookie())
    with open('./config/checkpoint.txt', 'a') as io:
        io.write('\n{}\n'.format(datetime.now().strftime('%y%m%d-%H%M%S')))
    model_dict = next_model_list(browser, 0, browser.find(id='li_M'))
    save_model(model_dict)
    save_art(art_dict)
    with open('./config/checkpoint.txt', 'a') as io:
        io.write('{}\n'.format(datetime.now().strftime('%y%m%d-%H%M%S')))