# This code is licensed under the New BSD License
# 2009, Alexander Artemenko <svetlyak.40wt@gmail.com>
# For other contacts, visit http://aartemenko.com

"""
This is a helper to work with MongoDB's documents.

Author: Alexander Artemenko <svetlyak.40wt@gmail.com>
"""

import types
from pymongo.dbref import DBRef
from mongobongo.attributed import AttributedDict

_DEFAULT_OPTIONS = dict(
    ordering = None,
)


class Options(object):
    """ Document's options.
    """
    def __init__(self, meta):
        self.meta = meta
        for attr_name, value in _DEFAULT_OPTIONS.iteritems():
            setattr(self, attr_name, value)

    def contribute_to_class(self, cls, name):
        cls._meta = self

        if self.meta:
            meta_attrs = self.meta.__dict__.copy()
            for name in self.meta.__dict__:
                if name.startswith('_'):
                    del meta_attrs[name]

            for attr_name, value in _DEFAULT_OPTIONS.iteritems():
                setattr(self, attr_name, meta_attrs.pop(attr_name, value))

        del self.meta



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
        data = list(self.find(query).limit(1))

        if data:
            return self._document_class(__kwargs = data[0])
        return None

    def dereference(self, dbref):
        doc_cls = get_doc_class_for_collection(dbref.collection)
        value = self.__db.dereference(dbref)
        return doc_cls(__kwargs = value)

    def save(self, obj):
        def transform_docs_to_dbrefs(data):
            def transform_value(value):
                if isinstance(value, Document):
                    if value._id is None:
                        value.save()
                    return DBRef(value.objects.collection_name, transform_value(value._id))
                elif isinstance(value, types.DictType):
                    return transform_dict(value)
                elif isinstance(value, types.ListType):
                    return [transform_value(v) for v in value]
                return value

            def transform_dict(object):
                for (key, value) in object.iteritems():
                    object[key] = transform_value(value)
                return object

            return transform_dict(data)

        return self._collection.save(transform_docs_to_dbrefs(obj))


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
        attr_meta = attrs.pop('Meta', None)

        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta

        new_class.add_to_class('_meta', Options(meta))

        collection = attrs.pop('collection')

        class CursorProxy(object):
            _doctype = new_class

            def __init__(self, real_cursor):
                self.__cursor = real_cursor

                if self._doctype._meta.ordering:
                    self.sort(self._doctype._meta.ordering)

            def next(self):
                """Wraps result into the custom class"""
                return self._doctype(__kwargs = self.__cursor.next())

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
                    return self._doctype(__kwargs = result)

            def __len__(self):
                return self.__cursor.__len__()

            def __iter__(self):
                return self

        # Set all neccessary methods
        for key, value in attrs.iteritems():
            new_class.add_to_class(key, value)

        setattr(new_class, 'objects', CollectionManager(
            collection,
            CursorProxy,
            new_class,
        ))

        register_doc_class(new_class)
        return new_class

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)



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

        if isinstance(value, DBRef):
            value = self.objects.dereference(value)
            self._data[name] = value

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



class Cache(object):
    __shared_state = dict(
        doc_classes = {},
    )

    def __init__(self):
        self.__dict__ = self.__shared_state

    def register_doc_class(self, cls):
        self.doc_classes[cls.objects.collection_name] = cls

    def get_doc_class_for_collection(self, collection_name):
        return self.doc_classes.get(collection_name, None)



cache = Cache()
register_doc_class = cache.register_doc_class
get_doc_class_for_collection = cache.get_doc_class_for_collection

