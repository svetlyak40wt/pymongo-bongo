# This code is licensed under the New BSD License
# 2009, Alexander Artemenko <svetlyak.40wt@gmail.com>
# For other contacts, visit http://aartemenko.com

import unittest
from mongobongo.attributed import AttributedDict, \
                                  AttributedList

class AttrDictTests(unittest.TestCase):
    def test_attr_dict_just_a_proxy(self):
        d = {'blah': 'minor', 'one': 1}
        a = AttributedDict(d)

        self.assertEqual('minor', a.blah)
        self.assertEqual(1, a.one)

        a.blah = 'shvah'
        self.assertEqual('shvah', a.blah)
        self.assertEqual('shvah', d['blah'])


    def test_attr_dict_returns_inner_dicts_as_proxies(self):
        d = {'ddd': {'b': 2, 'c': 3}}
        a = AttributedDict(d)

        a.ddd.b = 5
        self.assertEqual(5, a.ddd.b)
        self.assertEqual(5, d['ddd']['b'])


    def test_attr_dict_returns_inner_lists_as_proxies(self):
        d = {'ddd': [{'b': 2}, {'c': 3}]}
        a = AttributedDict(d)

        a.ddd[0].b = 5
        self.assertEqual(5, a.ddd[0].b)
        self.assertEqual(5, d['ddd'][0]['b'])


    def test_supports_iteration_by_keys(self):
        d = {'ddd': {'b': 2}}
        a = AttributedDict(d)

        self.assertEqual('ddd', iter(d).next())
        self.assertEqual('ddd', iter(a).next())


    def test_supports_iteration_by_items(self):
        d = {'ddd': {'b': 2}}
        a = AttributedDict(d)

        self.assertEqual(2, d.iteritems().next()[1]['b'])
        self.assertEqual(2, a.iteritems().next()[1].b)


class AttrListTests(unittest.TestCase):
    def test_attr_list_just_a_proxy(self):
        l = [{'b': 2}]
        al = AttributedList(l)

        self.assertEqual(2, al[0].b)
        al[0].b = 123
        self.assertEqual(123, al[0].b)


    def test_attr_list_returns_other_lists_as_proxies(self):
        l = [[{'b': 2}]]
        al = AttributedList(l)

        self.assertEqual(2, al[0][0].b)
        al[0][0].b = 123
        self.assertEqual(123, al[0][0].b)


    def test_have_eq(self):
        l = [[{'b': 2}]]
        al = AttributedList(l)

        self.assertEqual(l, al)


    def test_supports_iteration(self):
        l = [{'b': 2}]
        al = AttributedList(l)

        self.assertEqual(2, iter(al).next().b)

