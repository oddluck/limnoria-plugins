###
# Copyright (c) 2018, Anatoly Popov
# Copyright (c) 2018, Andrey Rahmatullin
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

import random
import pytest
from .sevenSea2EdRaiseRoller import RollResult

class TestRollResult:
    def test_default(self):
        x = RollResult(1, 0, 0)
        assert x.value == 1
        assert x.result == 1

    def test_joie_de_vivre(self):
        x = RollResult(1, joie_de_vivre_target=1)
        assert x.value == 10
        assert x.result == 1

        x = RollResult(2, joie_de_vivre_target=1)
        assert x.value == 2
        assert x.result == 2

    def test_lashes(self):
        x = RollResult(1, lash_count=2)
        assert x.value == 0
        assert x.result == 1

        x = RollResult(2, lash_count=2)
        assert x.value == 2
        assert x.result == 2

    def test_lashes_precede_joie_de_vivre(self):
        x = RollResult(1, lash_count=2, joie_de_vivre_target=1)
        assert x.value == 0
        assert x.result == 1

    def test_joie_de_vivre_works_greater_lashes(self):
        x = RollResult(3, lash_count=2, joie_de_vivre_target=5)
        assert x.value == 10
        assert x.result == 3

        x = RollResult(1, lash_count=2, joie_de_vivre_target=5)
        assert x.value == 0
        assert x.result == 1

    def test_output_no_changes(self):
        x = RollResult(3)
        assert str(x) == '3'

    def test_output_any_change(self):
        x = RollResult(3, lash_count=5)
        assert str(x) == '0 [3]'

        x = RollResult(3, joie_de_vivre_target=5)
        assert str(x) == '10 [3]'
