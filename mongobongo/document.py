"""
Helper to work with MongoDB's documents.

Author: Alexander Artemenko <svetlyak.40wt@gmail.com>
"""


class AttributedDict(object):
    def __init__(self, d):
        self._data = d

    def __getattr__(self, name):
        value = self._data[name]
        if isinstance(value, dict):
            return AttributedDict(value)
        return value

    def __setattr__(self, name, value):
        if name == '_data':
            self.__dict__[name] = value
        else:
            self._data[name] = value

    def __delattr__(self, name):
        self._data.__delitem__(name)

    def __eq__(self, d):
        if isinstance(d, AttributedDict):
            return self._data == d._data
        else:
            return self._data == d

    def __ne__(self, d):
        return not self.__eq__(d)



class CollectionManager(object):
    """This class redefines some methods from pymongo.Collection
       to wrap results with user's class."""

    __db = None

    def __init__(self, name, cursor_class, document_class):
        self._collection_name = name
        self._cursor_class = cursor_class
        self._document_class = document_class

    @property
    def _collection(self):
        return self.__db[self._collection_name]

    @property
    def collection_name(self):
        return self._collection_name

    def _get_db(self): return CollectionManager.__db
    def _set_db(self, db): CollectionManager.__db = db
    db = property(_get_db, _set_db)

    def remove(self, query = {}):
        """Removed objects from collection.
           WARNING, by default, all objects are removed!
        """
        self._collection.remove(query)

    def all(self):
        return self._cursor_class(self._collection.find())

    def find(self, query = {}):
        return self._cursor_class(self._collection.find(query))

    def find_one(self, query = {}):
        data = self._collection.find_one(query)
        if data:
            data = self._document_class(__kwargs = data)
        return data

    def __getattr__(self, name):
        return getattr(self._collection, name)



class DocumentBase(type):
    """Metaclass to create classes which inherit the Document class."""

    def __new__(cls, name, bases, attrs):
        super_new = super(DocumentBase, cls).__new__
        parents = [b for b in bases if isinstance(b, DocumentBase)]
        if not parents:
            # If this isn't a subclass of Model, don't do anything special.
            return super_new(cls, name, bases, attrs)

        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})

        collection = attrs.pop('collection')

        class CursorProxy(object):
            def __init__(self, real_cursor):
                self.__cursor = real_cursor

            def next(self):
                """Wraps result into the custom class"""
                return new_class(__kwargs = self.__cursor.next())

            def sort(self, *args, **kwargs):
                self.__cursor.sort(*args, **kwargs)
                return self

            def __getattr__(self, name):
                return getattr(self.__cursor, name)

            def __getitem__(self, index):
                """Wraps result into the custom class
                   if it is one item"""
                result = self.__cursor.__getitem__(index)

                if isinstance(index, slice):
                    return self
                else:
                    return new_class(__kwargs = result)

            def __len__(self):
                return self.__cursor.__len__()

            def __iter__(self):
                return self

        # Set all neccessary methods
        for key, value in attrs.iteritems():
            setattr(new_class, key, value)

        setattr(new_class, 'objects', CollectionManager(
            collection,
            CursorProxy,
            new_class,
        ))
        return new_class



class Document(object):
    """
    Helper to comfort work with document collections.
    The most cool feature of this helper is automatic
    mapping all data to user specified classes.
    For example, you can define class with custom methods:

    >>> from pymongo.document import Document
    >>> class Article(Document):
    ...     collection = 'articles'
    ...     def get_url(self):
    ...         return 'http://example.com/blog/%s/' % self.slug
    >>>
    >>> # after that, you can use this class to
    >>> # instantiate objects, save them and fetch from database
    >>>
    >>> # first, you need to setup database connection
    >>> from pymongo.connection import Connection
    >>> Article.objects.db = Connection('localhost').test_database
    >>>
    >>> article = Article(slug = 'first-article',
    ...                   title = 'First article',
    ...                   text = 'Blah minor',
    ...                   tags = ['test', 'short'])
    >>> article.save()
    >>>
    >>> # Now try to search this object by slug
    >>>
    >>> obj = article.objects.find({'slug': 'first-article'})
    >>> assert(obj is not None)
    >>> assert(obj.slug == 'first-article')
    >>> assert(obj.get_url() == 'http://example.com/blog/first-article/')
    """

    __metaclass__ = DocumentBase

    def __init__(self, **kwargs):
        try:
            self.__dict__['_data'] = kwargs['__kwargs']
        except KeyError:
            self.__dict__['_data'] = kwargs


    def __getattr__(self, name):
        value = self._data.get(name, None)

        if isinstance(value, dict):
            return AttributedDict(value)

        return value


    def __setattr__(self, name, value):
        self._data[name] = value


    def __getitem__(self, name):
        return self._data[name]


    def save(self):
        self.objects.save(self._data)
        return self

    def update(self, data):
        self._data.update(data)

