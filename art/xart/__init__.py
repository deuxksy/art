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
