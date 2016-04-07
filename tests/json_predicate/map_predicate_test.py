# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=missing-docstring
# pylint: disable=redefined-builtin
# pylint: disable=invalid-name


import unittest

from citest.base import JsonSnapshotHelper
import citest.json_predicate as jp
from citest.json_predicate.path_predicate_helpers import PathEqPredicate
import citest.json_predicate as lp
import citest.json_predicate as mp


_LETTER_DICT = {'a':'A', 'b':'B', 'z':'Z'}
_NUMBER_DICT = {'a':1, 'b':2, 'three':3}
_MIXED_DICT = {'a':'A', 'b':2, 'x':'X'}
_COMPOSITE_DICT = {'letters': _LETTER_DICT, 'numbers': _NUMBER_DICT}

_LETTER_ARRAY = ['a', 'b', 'c']
_NUMBER_ARRAY = [1, 2, 3]
_DICT_ARRAY = [{}, _LETTER_DICT, _NUMBER_DICT, _COMPOSITE_DICT]
_MULTI_ARRAY = [_LETTER_DICT, _NUMBER_DICT, _LETTER_DICT, _NUMBER_DICT]


class JsonMapPredicateTest(unittest.TestCase):
  def assertEqual(self, expect, have, msg=''):
    JsonSnapshotHelper.AssertExpectedValue(expect, have, msg)

  def _try_map(self, pred, obj, expect_ok, expect_map_result=None,
               dump=False, min=1):
    """Helper function for invoking finder and asserting the result.

    Args:
      pred: The jp.ValuePredicate to map.
      obj: The object to apply the predicate to.
      expect_ok: Whether we expect apply to succeed or not.
      expect_map_result: If not None, then the expected
          mp.MapPredicateResult from apply().
      dump: If True then print the filter_result to facilitate debugging.
    """
    map_result = mp.MapPredicate(pred, min=min)(obj)
    if dump:
      print 'MAP_RESULT:\n{0}\n'.format(
          JsonSnapshotHelper.ValueToEncodedJson(map_result))

    if expect_map_result:
      self.assertEqual(expect_map_result, map_result)
    error_msg = '{expect_ok} != {ok}\n{map_result}'.format(
        expect_ok=expect_ok, ok=map_result.__nonzero__(),
        map_result=map_result)
    self.assertEqual(expect_ok, map_result.__nonzero__(), error_msg)

  def test_map_predicate_good_1(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))

    aA_attempt = mp.ObjectResultMapAttempt(_LETTER_DICT, aA(_LETTER_DICT))
    expect_result = mp.MapPredicateResult(
        valid=True, pred=aA,
        obj_list=[_LETTER_DICT], all_results=[aA_attempt.result],
        good_map=[aA_attempt],
        bad_map=[])

    self._try_map(aA, _LETTER_DICT, True, expect_result)

  def test_map_predicate_bad(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))

    expect_result = mp.MapPredicateResult(
        valid=False, pred=aA,
        obj_list=[_NUMBER_DICT], all_results=[aA(_NUMBER_DICT)],
        bad_map=[mp.ObjectResultMapAttempt(_NUMBER_DICT, aA(_NUMBER_DICT))],
        good_map=[])

    self._try_map(aA, _NUMBER_DICT, False, expect_result)

  def test_map_predicate_good_and_bad_min_1(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))

    aa_number_attempt = mp.ObjectResultMapAttempt(_NUMBER_DICT,
                                                  aA(_NUMBER_DICT))
    aa_letter_attempt = mp.ObjectResultMapAttempt(_LETTER_DICT,
                                                  aA(_LETTER_DICT))
    expect_result = mp.MapPredicateResult(
        valid=True, pred=aA,
        obj_list=[_NUMBER_DICT, _LETTER_DICT],
        all_results=[aa_number_attempt.result, aa_letter_attempt.result],
        good_map=[aa_letter_attempt],
        bad_map=[aa_number_attempt])

    self._try_map(aA, [_NUMBER_DICT, _LETTER_DICT], True, expect_result)

  def test_map_predicate_good_and_bad_min_2(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))

    expect_result = mp.MapPredicateResult(
        valid=False, pred=aA,
        obj_list=[_NUMBER_DICT, _LETTER_DICT],
        all_results=[aA(_NUMBER_DICT), aA(_LETTER_DICT)],
        good_map=[mp.ObjectResultMapAttempt(_LETTER_DICT, aA(_LETTER_DICT))],
        bad_map=[mp.ObjectResultMapAttempt(_NUMBER_DICT, aA(_NUMBER_DICT))])

    self._try_map(
        aA, [_NUMBER_DICT, _LETTER_DICT], False, expect_result, min=2)

  def test_map_not_found(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))

    aa_composite_attempt = mp.ObjectResultMapAttempt(_COMPOSITE_DICT,
                                                     aA(_COMPOSITE_DICT))
    expect_result = mp.MapPredicateResult(
        valid=False, pred=aA,
        obj_list=[_COMPOSITE_DICT], all_results=[aa_composite_attempt.result],
        bad_map=[aa_composite_attempt],
        good_map=[])

    self._try_map(aA, _COMPOSITE_DICT, False, expect_result)

  def test_object_filter_cases(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))

    self._try_map(aA, _LETTER_DICT, True)
    self._try_map(aA, _COMPOSITE_DICT, False)
    self._try_map(aA, _NUMBER_DICT, False)
    self._try_map(aA, _MULTI_ARRAY, True)
    self._try_map(aA, [_COMPOSITE_DICT, _COMPOSITE_DICT], False)
    self._try_map(aA, _MIXED_DICT, True)

    AandB = lp.AND([PathEqPredicate('a', 'A'),
                    PathEqPredicate('b', 'B')])
    self._try_map(AandB, _LETTER_DICT, True)
    self._try_map(AandB, _COMPOSITE_DICT, False)
    self._try_map(AandB, _NUMBER_DICT, False)
    self._try_map(AandB, _MULTI_ARRAY, True)
    self._try_map(AandB, _MIXED_DICT, False)


  def test_none_bad(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))
    self._try_map(aA, None, False)

  def test_none_good(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))
    self._try_map(aA, None, True, min=0)


if __name__ == '__main__':
  loader = unittest.TestLoader()
  suite = loader.loadTestsFromTestCase(JsonMapPredicateTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
