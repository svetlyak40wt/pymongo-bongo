# This code is licensed under the New BSD License
# 2009, Alexander Artemenko <svetlyak.40wt@gmail.com>
# For other contacts, visit http://aartemenko.com

class AttributedDict(object):
    def __init__(self, d):
        self._data = d


    def __getattr__(self, name):
        value = self._data[name]
        if isinstance(value, dict):
            return AttributedDict(value)
        elif isinstance(value, list):
            return AttributedList(value)
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



class AttributedList(object):
    def __init__(self, l):
        self._data = l


    def __getitem__(self, index):
        value = self._data[index]
        if isinstance(value, dict):
            return AttributedDict(value)
        elif isinstance(value, list):
            return AttributedList(value)
        return value


    def __eq__(self, l):
        if isinstance(l, AttributedList):
            return self._data == l._data
        else:
            return self._data == l


    def __ne__(self, l):
        return not self.__eq__(l)

