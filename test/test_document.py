import os
import unittest

from pdb import set_trace
from pymongo import DESCENDING, ASCENDING
from pymongo.connection import Connection
from pymongo.database import Database

from mongobongo.document import Document, get_doc_class_for_collection
from mongobongo.attributed import AttributedDict



def get_connection():
    host = os.environ.get("DB_IP", "localhost")
    port = int(os.environ.get("DB_PORT", 27017))
    return Connection(host, port)


class TestDoc(Document):
    collection = 'test_docs'

    def get_url(self):
        return 'http://svetlyak.ru'


class OrderedDoc(Document):
    collection = 'test_docs'
    class Meta:
        ordering = [('user', ASCENDING)]


class Documents(unittest.TestCase):
    def setUp(self):
        db = Database(get_connection(), "pymongo_test")

        TestDoc.objects.db = db
        TestDoc.objects.remove()

    def test_save_and_find(self):
        TestDoc(author = 'art', tags = ['test', 'python']).save()
        TestDoc(author = 'vasily', tags = ['test', 'django']).save()

        TestDoc.objects.ensure_index([('author', ASCENDING)])
        docs = TestDoc.objects.all()
        self.assertEqual(2, len(docs))

        docs = list(docs)
        self.assertEqual('art', docs[0].author)
        self.assertEqual('vasily', docs[1].author)

        self.assertEqual('art', TestDoc.objects.find({'tags': 'python'})[0].author)

    def test_save_returns_object_with_id(self):
        doc = TestDoc(author = 'art')

        self.assertEqual(None, doc._id)
        self.assertEqual(doc, doc.save())
        self.assert_(doc._id)

    def test_custom_method(self):
        doc = TestDoc(author = 'art')
        self.assertEqual('http://svetlyak.ru', doc.get_url())

    def test_find_one(self):
        TestDoc(author = 'art', tags = ['test', 'python']).save()
        TestDoc(author = 'vasily', tags = ['test', 'django']).save()

        doc = TestDoc.objects.find_one({'author': 'art'})
        self.assertEqual('art', doc.author)

    def test_update(self):
        doc = TestDoc(author = 'art')
        doc.update({'tag': 'test'})
        self.assertEqual('test', doc.tag)

    def test_find_one_can_return_none(self):
        doc = TestDoc.objects.find_one({'author': 'unknown'})
        self.assertEqual(None, doc)

    def test_doc_can_be_subscriptable(self):
        doc = TestDoc(__kwargs = {'the-title': 'Just a Poem'})
        self.assertEqual('Just a Poem', doc['the-title'])

    def test_access_to_inner_attributes(self):
        doc = TestDoc(author = dict(
            name = 'Alexander',
            nick = 'svetlyak40wt',
            address = dict(
                country = 'Russia',
                city = 'Moscow')
        ))
        self.assertEqual('Alexander', doc.author.name)
        self.assertEqual('Russia', doc.author.address.country)
        self.assertEqual(dict(country = 'Russia', city = 'Moscow'), doc.author.address)

    def test_change_attributes(self):
        doc = TestDoc()
        doc.author = 'Alexander'
        doc.article = {}
        doc.article.title = 'Just a Poem'
        doc.article.tags = ['one', 'two']
        doc.save()

        doc = TestDoc.objects.find_one()
        self.assertEqual('Alexander', doc.author)
        self.assertEqual(dict(title = 'Just a Poem', tags = ['one', 'two']), doc.article)

    def test_dict_proxy(self):
        d = dict(title = 'Just an Example', tags = ['test', 'python'])
        dp = AttributedDict(d)
        dp.author = dict(name = 'Alexander')
        dp.author.lastname = 'Artemenko'

        self.assertEqual('Alexander', d['author']['name'])
        self.assertEqual('Artemenko', d['author']['lastname'])

        del dp.author.lastname
        self.assertEqual(dict(name='Alexander'), dp.author)

    def test_sort_documents(self):
        TestDoc(user = 'vasily').save()
        TestDoc(user = 'alex').save()
        TestDoc(user = 'zuger').save()
        TestDoc(user = 'olga').save()

        TestDoc.objects.ensure_index([('user', ASCENDING)])

        docs = list(TestDoc.objects.all().sort([('user', ASCENDING)])[:2])

        self.assertEqual(2, len(docs))
        self.assertEqual('alex', docs[0].user)
        self.assertEqual('olga', docs[1].user)

    def test_default_ordering_for_iterator(self):
        names = ['vasily', 'alex', 'zuger', 'olga']

        for name in names:
            OrderedDoc(user = name).save()

        for name, doc in zip(sorted(names), OrderedDoc.objects.all()):
            self.assertEqual(name, doc.user)

    def test_default_ordering_for_single_items(self):
        names = ['vasily', 'alex', 'zuger', 'olga']

        for name in names:
            OrderedDoc(user = name).save()

        names = sorted(names)
        objects = OrderedDoc.objects.all()

        for i in range(len(names)):
            self.assertEqual(names[i], objects[i].user)

    def test_default_ordering_for_find_one(self):
        names = ['vasily', 'alex', 'zuger', 'olga']

        for name in names:
            OrderedDoc(user = name).save()

        self.assertEqual('alex', OrderedDoc.objects.find_one().user)




class Article(Document):
    collection = 'articles'


class Author(Document):
    collection = 'authors'


class References(unittest.TestCase):
    def setUp(self):
        db = Database(get_connection(), "pymongo_test")

        Article.objects.db = db
        Article.objects.remove()
        Author.objects.remove()

    def testDocClassAutoregistration(self):
        self.assertEqual(Article, get_doc_class_for_collection('articles'))
        self.assertEqual(Author, get_doc_class_for_collection('authors'))


    def testReferenceObject(self):
        author = Author(name = 'Alexander')
        author.save()

        article =  Article(title = 'Life is miracle', author = author)
        article.save()

        article = Article.objects.find_one()

        self.assertEqual('Alexander', article.author.name)
        self.assertEqual(Author, type(article.author))


    def testSaveReferenceObjectWithParent(self):
        author = Author(name = 'Alexander')
        article =  Article(title = 'Life is miracle', author = author)

        self.assert_(author._id is None)
        article.save()
        self.assert_(author._id is not None)

