from scrapers.semantic_scholar_scraper.semantic_scholar_paper import SemanticScholarPaper
from scrapers.semantic_scholar_scraper.semantic_scholar_object import SemanticScholarObject


class BaseReference(SemanticScholarObject):
    '''
    Base class for both Citation and Reference classes.
    '''

    FIELDS = [
        'contexts',
        'intents',
        'isInfluential'
    ]

    def __init__(self, data: dict) -> None:
        super().__init__()
        self._contexts = None
        self._intents = None
        self._isInfluential = None
        self._paper = None
        self._initialize(data)

    def _initialize(self, data: dict) -> None:
        self._data = data
        if 'contexts' in data:
            self._contexts = data['contexts']
        if 'intents' in data:
            self._intents = data['intents']
        if 'isInfluential' in data:
            self._isInfluential = data['isInfluential']

    @property
    def contexts(self) -> list:
        return self._contexts

    @property
    def intents(self) -> list:
        return self._intents

    @property
    def isInfluential(self) -> bool:
        return self._isInfluential

    @property
    def paper(self) -> SemanticScholarPaper:
        return self._paper


class Reference(BaseReference):
    '''
    This class abstracts a reference.
    '''

    def __init__(self, data: dict) -> None:
        super().__init__(data)
        if 'citedPaper' in data:
            self._paper = Paper(data['citedPaper'])

class Citation(BaseReference):
    '''
    This class abstracts a citation.
    '''

    def __init__(self, data: dict) -> None:
        super().__init__(data)
        if 'citingPaper' in data:
            self._paper = Paper(data['citingPaper'])


