class NzbSearchResult:
    def __init__(self, title=None, link=None, age=None, provider=None, guid=None, size=None, categories=None, attributes=None):
        self.title = title
        self.link = link
        self.age = age  #In seconds
        self.age_precise = False #Set to false if the age is not received from a pubdate but from an age. That might influence duplicity check
        self.provider = provider
        self.guid = guid
        self.size = size
        self.categories = categories
        self.description = None
        self.comments = None
        self.pubDate = None
        self.attributes = attributes
        

    def __repr__(self):
        return "Title: {}. Age: {}. Size: {}. Provider: {}".format(self.title, self.age, self.size, self.provider)
    
    def __eq__(self, other_nzb_search_result):
        return self.title == other_nzb_search_result.title and self.link == other_nzb_search_result.link and self.provider == other_nzb_search_result.provider and self.guid == other_nzb_search_result.guid  