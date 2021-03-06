'''
Created on 3 Apr 2016

@author: John Beard
'''

class RequestData(object):
    '''
    Class to represent structured data related to a query. This could be one of
    (but not limited to):
      - URL to some external resource/web page (eg search engine results page
        for a given query)
      - Strutured list of search results of some kind (eg list of chemicals
        matching a certain string)
      - Structured data relating to a specific query on a database (eg list
        of properties for a given chemical)
    '''

    def __init__(self, search_term):
        self.search_term = search_term

    def getData(self):
        '''
        Gets an object representing the data
        
        Used to serialise the data for handover to clients
        '''
        raise NotImplementedError


class PlainUrlReqData(RequestData):
    '''
    Request data that points a user to some external URL, with minimal extra 
    context
    
    This is likely to be  common data type for most "blind" queries, where
    Mnem just interpolates a string to a URL and the user goes to that page
    '''

    def __init__(self, search_term, url, title=None):
        super(PlainUrlReqData, self).__init__(search_term)

        self.url = url
        self.title = title

    def getData(self):

        d = {
            'term': self.search_term,
            'uri': self.url
        }

        # this bit is optional
        if self.title:
            d['title'] = self.title

        return d

class CompletionReqData(RequestData):
    '''
    Request data representing a request that results in some list of 
    completions
    '''
    def __init__(self, compls=[]):
        self.compls = compls

    def append(self, c):
        self.compls.append(c)

    def getData(self):

        def formatCompl(c):

            # all completions have a keyword
            d = {
                'keyword': c.keyword
            };

            if c.category:
                d['category'] = c.category

            if c.url:
                d['url'] = c.url

            if c.description:
                d['desc'] = c.description

            return d

        return {
            'completions': [formatCompl(c) for c in self.compls]
        }
