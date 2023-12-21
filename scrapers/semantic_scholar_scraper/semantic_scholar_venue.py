from scrapers.semantic_scholar_scraper.semantic_scholar_object import SemanticScholarObject


class SemanticScholarVenue(SemanticScholarObject):
    '''
    This class represents the publication venue of the paper
    '''

    def __init__(self, data: dict) -> None:
        super().__init__()
        self._alternate_names = None
        self._alternate_urls = None
        self._id = None
        self._issn = None
        self._name = None
        self._type = None
        self._url = None
        self._initialize(data)

    def _initialize(self, data):
        self._data = data
        if 'alternate_names' in data:
            self._alternate_names = data['alternate_names']
        if 'alternate_urls' in data:
            self._alternate_urls = data['alternate_urls']
        if 'id' in data:
            self._id = data['id']
        if 'issn' in data:
            self._issn = data['issn']
        if 'name' in data:
            self._name = data['name']
        if 'type' in data:
            self._type = data['type']
        if 'url' in data:
            self._url = data['url']

    @property
    def alternate_names(self) -> list:
        return self._alternate_names

    @property
    def alternate_urls(self) -> list:
        return self._alternate_urls

    @property
    def id(self) -> str:
        return self._id

    @property
    def issn(self) -> str:
        return self._issn

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> str:
        return self._type

    @property
    def url(self) -> str:
        return self._url


