###
# Copyright (c) 2012, Mike Mueller
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

"""
Quick & dirty prefix tree (aka trie).
"""

# This got a little uglier because using a nice object-oriented approach took
# too much time and memory on big trees.  Now every node is simply a dict,
# with the special '*' field meaning that the word is complete at that node.

class Trie(object):
    def __init__(self):
        self.contents = {'*': False}

    def add(self, value, contents=None):
        if contents is None:
            contents = self.contents
        if not value:
            contents['*'] = True
            return
        prefix = value[0]
        remainder = value[1:]
        child_contents = contents.get(prefix, None)
        if not child_contents:
            child_contents = {'*': False}
            contents[prefix] = child_contents
        self.add(remainder, child_contents)

    def find(self, value):
        "Return true if the value appears, false otherwise."
        x = self.find_prefix(value)
        return x and x['*'] == True

    def find_prefix(self, value, contents=None):
        "Return true if the given prefix appears in the tree."
        if contents is None:
            contents = self.contents
        if not value:
            return contents
        child_contents = contents.get(value[0], None)
        if not child_contents:
            return None
        return self.find_prefix(value[1:], child_contents)

    def dump(self, indent=0, contents=None):
        "Dump the trie to stdout."
        if contents is None:
            contents = self.contents
        for key in sorted(contents.keys()):
            if key == '*':
                continue
            text = indent * ' '
            text += key
            child_contents = contents[key]
            if child_contents['*']:
                text += '*'
            print(text)
            self.dump(indent+2, child_contents)

if __name__ == '__main__':
    import resource
    import sys
    import time

    if '--perf' in sys.argv:
        # Performance test, last arg should be input file
        start = time.time()
        t = Trie()
        f = open(sys.argv[-1], 'r')
        for line in f:
            t.add(line.strip())
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        elapsed = time.time() - start
        print(('Trie created in %g seconds.' % elapsed))
        print(('Used %dMB RAM.' % (mem/1024)))
    else:
        # Regular sanity test
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

        assert not t.find('h')
        assert t.find('he')
        assert not t.find('hel')
        assert t.find('hell')
        assert t.find('hello')
        assert not t.find('r')
        assert t.find('world')
        assert not t.find('ba')
        assert t.find('bar')
        assert t.find('alphabet')
        assert t.find('alphanumeric')
        assert not t.find('alpha')
        assert not t.find('f')
        assert not t.find('fo')
        assert t.find('foo')
        assert t.find('food')
        assert not t.find('foodi')
        assert t.find('foodie')
