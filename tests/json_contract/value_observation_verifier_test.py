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
# pylint: disable=invalid-name


import unittest

from citest.base import JsonSnapshotHelper
import citest.json_contract as jc
import citest.json_predicate as jp


_LETTER_DICT = {'a':'A', 'b':'B', 'z':'Z'}
_NUMBER_DICT = {'a':1, 'b':2, 'three':3}

_COMPOSITE_DICT = {'letters': _LETTER_DICT, 'numbers': _NUMBER_DICT}

_LETTER_ARRAY = ['a', 'b', 'c']
_NUMBER_ARRAY = [1, 2, 3]
_DICT_ARRAY = [{}, _LETTER_DICT, _NUMBER_DICT, _COMPOSITE_DICT]
_MULTI_ARRAY = [_LETTER_DICT, _NUMBER_DICT, _LETTER_DICT, _NUMBER_DICT]


class JsonValueObservationVerifierTest(unittest.TestCase):
  def assertEqual(self, expect, have, msg=''):
    try:
      JsonSnapshotHelper.AssertExpectedValue(expect, have, msg)
    except AssertionError:
      print 'EXPECTED\n{0!r}\nGOT\n{1!r}'.format(expect, have)

  def test_verifier_builder_add_constraint(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))
    bB = jp.PathPredicate('b', jp.STR_EQ('B'))
    builder = jc.ValueObservationVerifierBuilder('TestAddConstraint')
    builder.add_constraint(aA)
    builder.add_constraint(bB)
    verifier = builder.build()
    self.assertEqual('TestAddConstraint', verifier.title)
    self.assertEqual([aA, bB], verifier.constraints)

  def test_verifier_builder_contains_pred_list(self):
    aA = jp.PathPredicate('a', jp.STR_EQ('A'))
    bB = jp.PathPredicate('b', jp.STR_EQ('B'))
    builder = jc.ValueObservationVerifierBuilder('TestContainsGroup')
    builder.contains_path_pred('a', jp.STR_EQ('A'))
    builder.contains_path_pred('b', jp.STR_EQ('B'))
    verifier = builder.build()

    count_aA = jp.CardinalityPredicate(aA, 1, None)
    count_bB = jp.CardinalityPredicate(bB, 1, None)
    self.assertEqual([count_aA, count_bB], verifier.constraints)

  def test_object_observation_verifier_multiple_constraint_found(self):
    pred_list = [jp.PathPredicate('a', jp.STR_EQ('A')),
                 jp.PathPredicate('b', jp.STR_EQ('B'))]
    # This is our object verifier for these tests.
    verifier = jc.ValueObservationVerifier(
        title='Find Both', constraints=pred_list)

    test_cases = [('dict', _LETTER_DICT),
                  ('array', _DICT_ARRAY),
                  ('multi', _MULTI_ARRAY)]
    for test in test_cases:
      observation = jc.Observation()
      builder = jc.ObservationVerifyResultBuilder(observation)

      obj = test[1]
      if isinstance(test, list):
        observation.add_all_objects(obj)
      else:
        observation.add_object(obj)

      for pred in pred_list:
        builder.add_path_predicate_result(pred(observation.objects))

      # All of these tests succeed.
      verify_results = builder.build(True)

      try:
        self._try_verify(verifier, observation, True, verify_results)
      except:
        print 'testing {0}'.format(test[0])
        raise

  def test_object_observation_verifier_one_constraint_not_found(self):
    pred_list = [jp.PathPredicate('a', jp.STR_EQ('NOT_FOUND'))]

    # This is our object verifier for these tests.
    verifier = jc.ValueObservationVerifier(
        title='Cannot find one', constraints=pred_list)

    test_cases = [('array', _DICT_ARRAY),
                  ('dict', _LETTER_DICT),
                  ('array', _DICT_ARRAY),
                  ('multi', _MULTI_ARRAY)]

    for test in test_cases:
      observation = jc.Observation()
      builder = jc.ObservationVerifyResultBuilder(observation)

      obj = test[1]
      if isinstance(test, list):
        observation.add_all_objects(obj)
      else:
        observation.add_object(obj)

      for pred in pred_list:
        builder.add_path_predicate_result(pred(observation.objects))

      # None of these tests succeed.
      verify_results = builder.build(False)

      try:
        self._try_verify(verifier, observation, False, verify_results)
      except:
        print 'testing {0}'.format(test[0])
        raise

  def test_object_observation_verifier_multiple_constraint_not_found(self):
    pred_list = [jp.PathPredicate('a', jp.STR_EQ('NOT_FOUND')),
                 jp.PathPredicate('b', jp.STR_EQ('NOT_FOUND'))]

    # This is our object verifier for these tests.
    verifier = jc.ValueObservationVerifier(
        title='Cannot find either', constraints=pred_list)

    test_cases = [('array', _DICT_ARRAY),
                  ('dict', _LETTER_DICT),
                  ('array', _DICT_ARRAY),
                  ('multi', _MULTI_ARRAY)]

    for test in test_cases:
      observation = jc.Observation()
      builder = jc.ObservationVerifyResultBuilder(observation)

      obj = test[1]
      if isinstance(test, list):
        observation.add_all_objects(obj)
      else:
        observation.add_object(obj)

      for pred in pred_list:
        builder.add_path_predicate_result(pred(observation.objects))

      # None of these tests succeed.
      verify_results = builder.build(False)

      try:
        self._try_verify(verifier, observation, False, verify_results)
      except:
        print 'testing {0}'.format(test[0])
        raise

  def test_object_observation_verifier_some_but_not_all_constraints_found(self):
    pred_list = [jp.PathPredicate('a', jp.STR_EQ('NOT_FOUND')),
                 jp.PathPredicate('b', jp.STR_EQ('B'))]

    # This is our object verifier for these tests.
    verifier = jc.ValueObservationVerifier(
        title='Find one of two', constraints=pred_list)

    test_cases = [('array', _DICT_ARRAY),
                  ('dict', _LETTER_DICT),
                  ('array', _DICT_ARRAY),
                  ('multi', _MULTI_ARRAY)]

    for test in test_cases:
      observation = jc.Observation()
      builder = jc.ObservationVerifyResultBuilder(observation)

      obj = test[1]
      if isinstance(test, list):
        observation.add_all_objects(obj)
      else:
        observation.add_object(obj)

      for pred in pred_list:
        pred_result = jp.PathPredicate('', pred)(observation.objects)
        builder.add_path_predicate_result(pred(observation.objects))

      # None of these tests succeed.
      verify_results = builder.build(False)

      try:
        self._try_verify(verifier, observation, False, verify_results)
      except:
        print 'testing {0}'.format(test[0])
        raise

  def test_object_observation_verifier_with_conditional(self):
    # We need strict True here because we want each object to pass
    # the constraint test. Otherwise, if any object passes, then the whole
    # observation would pass. This causes a problem when we say that
    # we dont ever want to see 'name' unless it has a particular 'value'.
    # Without strict test, we'd allow this to occur as long as another object
    # satisfied that constraint.
    # When we use 'excludes', it applies to the whole observation since this
    # is normally the intent. However, here we are excluding values under
    # certain context -- "If the 'name' field is 'NAME' then it must contain
    # a value field 'VALUE'". Excluding name='NAME' everywhere would
    # not permit the context where value='VALUE' which we want to permit.
    verifier_builder = jc.ValueObservationVerifierBuilder(
        title='Test Conditional', strict=True)

    name_eq_pred = jp.PathEqPredicate('name', 'NAME')
    value_eq_pred = jp.PathEqPredicate('value', 'VALUE')

    conditional = jp.IF(name_eq_pred, value_eq_pred)
    pred_list = [jp.PathPredicate('', conditional)]
    verifier_builder.add_constraint(conditional)

    match_name_value_obj = {'name':'NAME', 'value':'VALUE'}
    match_value_not_name_obj = {'name':'GOOD', 'value':'VALUE'}
    match_neither_obj = {'name':'GOOD', 'value':'GOOD'}
    match_name_not_value_obj = {'name':'NAME', 'value':'BAD'}   # bad

    test_cases = [(True, [match_name_value_obj, match_neither_obj]),
                  (True, [match_value_not_name_obj, match_neither_obj]),
                  (False, [match_neither_obj, match_name_not_value_obj])]

    verifier = verifier_builder.build()
    for test in test_cases:
      observation = jc.Observation()
      result_builder = jc.ObservationVerifyResultBuilder(observation)

      expect_valid = test[0]
      obj_list = test[1]
      observation.add_all_objects(obj_list)

      for pred in pred_list:
        result_builder.add_path_predicate_result(pred(observation.objects))

      # All of these tests succeed.
      verify_results = result_builder.build(expect_valid)

      try:
        self._try_verify(verifier, observation, expect_valid, verify_results)
      except:
        print 'testing {0}'.format(obj_list)
        raise

  def _try_verify(self, verifier, observation, expect_ok, expect_results=None,
                  dump=False):
    """Helper function for a verifier result on a given observation.

    Args:
      verifier: The jc.ObservationVerifier to run.
      observation: The jc.Observation to run on.
      expect_ok: Whether we expect the verifier to succeed or not.
      expect_results: If not None, then the expected verify_results.
      dump: If True then print the verify_results to facilitate debugging.
    """
    verify_results = verifier(observation)

    # Assert that the observation was unchanged.
    self.assertEqual(verify_results.observation, observation)

    ok = verify_results.__nonzero__()
    if dump:
      print 'GOT RESULTS {0}:\n{1!r}\n'.format(
          verify_results.__class__.__name__, verify_results)
      print '\nExpected {0}:\n{1!r}\n'.format(
          expect_results.__class__.__name__, expect_results)

    self.assertEqual(expect_ok, ok)
    if expect_results:
      self.assertEqual(expect_results, verify_results)


if __name__ == '__main__':
  loader = unittest.TestLoader()
  suite = loader.loadTestsFromTestCase(JsonValueObservationVerifierTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
