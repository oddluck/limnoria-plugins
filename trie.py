#!/usr/bin/env python

"""
Quick & dirty prefix tree (aka trie).
"""

class Trie(object):
    def __init__(self):
        self.complete = False # Does this node complete a valid word?
        self.children = {}

    def add(self, value):
        if not value:
            self.complete = True
            return
        prefix = value[0]
        remainder = value[1:]
        node = self.children.get(prefix, None)
        if not node:
            node = Trie()
            self.children[prefix] = node
        node.add(remainder)

    def find(self, value):
        "Return the node associated with a value (None if not found)."
        if not value:
            return self
        node = self.children.get(value[0], None)
        if not node:
            return None
        return node.find(value[1:])

    def dump(self, indent=0):
        for key in sorted(self.children.keys()):
            text = indent * ' '
            text += key
            node = self.children[key]
            if node.complete:
                text += '*'
            print(text)
            node.dump(indent+2)

if __name__ == '__main__':
    t = Trie()
    t.add('hell')
    t.add('hello')
    t.add('he')
    t.add('world')
    t.add('alphabet')
    t.add('foo')
    t.add('food')
    t.add('foodie')
    t.add('bar')
    t.add('alphanumeric')
    t.dump()

    assert t.find('r') is None
    assert t.find('bars') is None
    assert not t.find('hel').complete
    assert t.find('hell').complete
    assert t.find('hello').complete
    assert not t.find('f').complete
    assert not t.find('fo').complete
    assert t.find('foo').complete
    assert t.find('food').complete
    assert not t.find('foodi').complete
    assert t.find('foodie').complete
