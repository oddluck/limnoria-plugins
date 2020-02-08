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
from .sevenSea2EdRaiseRoller import Raise, RollResult, SevenSea2EdRaiseRoller

class TestRoller:
    def test_zero_dice(self):
        x = SevenSea2EdRaiseRoller(lambda x: range(1, x+1)).roll_and_count(0)
        assert len(x.raises) == 0
        assert len(x.unused) == 0
        assert str(x) == "0 raises"

    def test_zero_raises_one_dice(self):
        x = SevenSea2EdRaiseRoller(lambda x: range(1, x+1)).roll_and_count(1)
        assert len(x.raises) == 0
        assert len(x.unused) == 1
        assert str(x) == "0 raises, unused: 1"

    def test_green(self):
        x = SevenSea2EdRaiseRoller(lambda x: range(1, x+1)).roll_and_count(4)
        assert len(x.raises) == 1
        assert len(x.unused) == 0
        assert str(x) == "1 raise: *(4 + 3 + 2 + 1)"

    def test_explode(self):
        rolls = SevenSea2EdRaiseRoller(ExplodingRoller().roll).roll(1)
        assert ', '.join(map(str, rolls)) == "10"

        rolls = SevenSea2EdRaiseRoller(ExplodingRoller().roll, explode=True).roll(1)
        assert ', '.join(map(str, rolls)) == "10, 5x"

        rolls = SevenSea2EdRaiseRoller(ExplodingRoller(3).roll, explode=True).roll(1)
        assert ', '.join(map(str, rolls)) == "10, 10x, 10xx, 5xxx"

        rolls = SevenSea2EdRaiseRoller(ExplodingRoller(3).roll, explode=True).roll(3)
        assert ', '.join(map(str, rolls)) == "10, 10, 10, 5x, 10x, 10x, 10xx, 5xx, 10xxx, 10xxxx, 10xxxxx, 5xxxxxx"

    def test_big_skill(self):
        rolls = SevenSea2EdRaiseRoller(
            RerollRoller([8, 6, 1, 8, 5, 2, 4]).roll,
            skill_rank=7
        ).roll_and_count(7)
        assert str(rolls) == "4 raises: **(8 + 6 + 1), **(8 + 5 + 2), unused: 4, discarded: 1r"

    def test_nines_without_ones(self):
        rolls = SevenSea2EdRaiseRoller(
            RerollRoller([10, 9, 9, 9, 8, 7, 6, 2]).roll,
            skill_rank=3
        ).roll_and_count(8)
        assert str(rolls) == "4 raises: *(10), *(9 + 2), *(9 + 6), *(9 + 7), unused: 8, discarded: 1r"

    def test_discard_one_of_the_initial(self):
        rolls = SevenSea2EdRaiseRoller(
            RerollRoller([10, 9, 9, 9, 8, 7, 6, 2], [10, 5]).roll,
            skill_rank=3
        ).roll_and_count(8)
        assert str(rolls) == "5 raises: *(10r), *(10), *(9 + 6), *(9 + 7), *(9 + 8), discarded: 2"

    def test_discard_one_of_the_initial_explode(self):
        rolls = SevenSea2EdRaiseRoller(
            RerollRoller([10, 9, 9, 9, 8, 7, 6, 2], [10, 5]).roll,
            skill_rank=3,
            explode=True
        ).roll_and_count(7)
        assert str(rolls) == "5 raises: *(10r), *(10), *(9 + 5rx), *(9 + 6), *(9 + 7), unused: 8, discarded: 2x"

    def test_optimal_solution_is_one_step_up(self):
        rolls = SevenSea2EdRaiseRoller(
            RerollRoller([10, 10, 10, 10, 5, 5, 5, 4, 4, 7, 6]).roll,
            skill_rank=5
        ).roll_and_count(7)
        assert str(rolls) == "10 raises: **(10 + 5), **(10 + 5), **(10 + 5), **(10 + 6x), **(7x + 4x + 4x), discarded: 1r"

    def test_optimal_solution_is_one_step_up2(self):
        rolls = SevenSea2EdRaiseRoller(
            RerollRoller([10, 5, 10, 5, 6, 4, 3, 4, 3], [2]).roll,
            skill_rank=5
        ).roll_and_count(7)
        assert str(rolls) == "6 raises: **(10 + 5), **(10 + 5), **(6 + 4x + 4 + 3x), unused: 3, discarded: 2r"

    # will wait boosting trees
    # def test_optimal_solution_is_one_step_up3(self):
    #     rolls = SevenSea2EdRaiseRoller(
    #         RerollRoller([7, 6, 3, 1, 6, 4, 4]).roll,
    #         skill_rank=5
    #     ).roll_and_count(7)
    #     assert str(rolls) == "4 raises: **(7 + 6 + 3), **(6 + 4 + 4 + 1), discarded: 1"

class Roller:
    def roll(self, count):
        return [next(self) for _ in range(count)]

class RerollRoller(Roller):
    def __init__(self, result, reroll_result=[1]):
        self.result = result + reroll_result
        self.index = 0

    def __next__(self):
        self.index %= len(self.result)
        value = self.result[self.index]
        self.index += 1
        return value

class ExplodingRoller(Roller):
    def __init__(self, ten_count=1, default_value=5):
        self.ten_count = ten_count
        self.current_ten_count = ten_count
        self.default_value = default_value

    def __next__(self):
        if self.current_ten_count == 0:
            self.current_ten_count = self.ten_count
            return self.default_value
        else:
            self.current_ten_count -= 1
            return 10
