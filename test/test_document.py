import os
import unittest

from pdb import set_trace
from pymongo import DESCENDING, ASCENDING
from pymongo.connection import Connection
from pymongo.database import Database
from mongobongo import Document


def get_connection():
    host = os.environ.get("DB_IP", "localhost")
    port = int(os.environ.get("DB_PORT", 27017))
    return Connection(host, port)


class TestDoc(Document):
    collection = 'test_docs'

    def get_url(self):
        return 'http://svetlyak.ru'


class Documents(unittest.TestCase):
    def setUp(self):
        TestDoc.objects.db = Database(get_connection(), "pymongo_test")
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
        from pymongo.document import AttributedDict

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

