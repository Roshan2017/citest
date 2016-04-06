# Copyright 2016 Google Inc. All Rights Reserved.
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


"""Tests the citest.json_predicate.path_predicate module."""


import unittest

from citest.json_predicate import (
    PATH_SEP,
    DONT_ENUMERATE_TERMINAL,
    PathPredicate,
    PathPredicateResultBuilder,
    PathValue,
    PathValueResult,
    MissingPathError,
    ValuePredicate
    )


_LETTER_DICT = {'a': 'A', 'b': 'B', 'z': 'Z'}
_NUMBER_DICT = {'a' :1, 'b': 2, 'three': 3}
_COMPOSITE_DICT = {'letters': _LETTER_DICT, 'numbers': _NUMBER_DICT}


class TestEqualsPredicate(ValuePredicate):
  """A simple 'Equals' predicate for testing purposes."""

  @property
  def operand(self):
    return self.__operand

  def __init__(self, operand):
    self.__operand = operand

  def __call__(self, value):
    valid = value == self.__operand
    return PathValueResult(pred=self, source=value, target_path='',
                           path_value=PathValue('', value), valid=valid)

  def __eq__(self, pred):
    return self.__class__ == pred.__class__ and self.__operand == pred.operand

  def __repr__(self):
    return 'TestEqualsPredicate({0})'.format(self.__operand)


class JsonPathPredicateTest(unittest.TestCase):
  def assertEqual(self, a, b, msg=''):
    if not msg:
      msg = 'EXPECTED\n{0!r}\nGOT\n{1!r}'.format(a, b)
    super(JsonPathPredicateTest, self).assertEqual(a, b, msg)

  def test_collect_from_dict_identity(self):
    source = _LETTER_DICT
    pred = PathPredicate('')
    values = pred(source)

    builder = PathPredicateResultBuilder(source, pred)
    builder.add_result_candidate(
        PathValue('', source),
        PathValueResult(source=source, target_path='',
                        path_value=PathValue('', source), valid=True))
    self.assertEqual(builder.build(True), values)

    self.assertEqual([PathValue('', source)], values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate('/')
    values = pred(source)
    self.assertEqual([PathValue('', source)], values.path_values)
    self.assertEqual([], values.path_failures)

  def test_collect_from_list_identity(self):
    letters = ['A', 'B', 'C']
    pred = PathPredicate('')
    values = pred(letters)
    self.assertEqual([PathValue('[0]', 'A'),
                      PathValue('[1]', 'B'),
                      PathValue('[2]', 'C')],
                     values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate(DONT_ENUMERATE_TERMINAL)
    values = pred(letters)
    self.assertEqual([PathValue('', letters)], values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate(PATH_SEP)
    values = pred(letters)
    self.assertEqual([PathValue('[0]', 'A'),
                      PathValue('[1]', 'B'),
                      PathValue('[2]', 'C')],
                     values.path_values)
    self.assertEqual([], values.path_failures)

  def test_collect_from_dict_found(self):
    # """Normal dictionary attribute lookup."""
    source = _LETTER_DICT
    pred = PathPredicate('a')
    values = pred(source)
    self.assertEqual([PathValue('a', 'A')], values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate('b')
    values = pred(source)
    self.assertEqual([PathValue('b', 'B')], values.path_values)
    self.assertEqual([], values.path_failures)

  def test_collect_from_dict_not_found(self):
    # """Normal dictionary attribute lookup with missing attribute."""
    source = _LETTER_DICT
    pred = PathPredicate('Z')
    values = pred(source)
    self.assertEqual([], values.path_values)
    self.assertEqual([MissingPathError(_LETTER_DICT, 'Z',
                                       path_value=('', _LETTER_DICT))],
                     values.path_failures)

  def test_collect_from_nested_dict_found(self):
    # """Nested dictionary attribute lookup."""
    source = {'outer': {'inner': _LETTER_DICT}}
    pred = PathPredicate(PATH_SEP.join(['outer', 'inner', 'a']))
    values = pred(source)
    self.assertEqual([PathValue(pred.path, 'A')], values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate(PATH_SEP.join(['outer', 'inner', 'b']))
    values = pred(source)
    self.assertEqual([PathValue(pred.path, 'B')], values.path_values)
    self.assertEqual([], values.path_failures)

  def test_collect_from_nested_dict_not_found(self):
    # """Nested dictionary attribute lookup with missing element."""
    source = _LETTER_DICT
    pred = PathPredicate(PATH_SEP.join(['a', 'b']))
    values = pred(source)
    self.assertEqual([], values.path_values)
    self.assertEqual(
        [MissingPathError('A', 'b', path_value=PathValue('a', 'A'))],
        values.path_failures)

  def test_collect_from_list_found(self):
    # """Ambiguous path passes through a list element."""
    source = [_LETTER_DICT]
    pred = PathPredicate('a')
    values = pred(source)
    self.assertEqual([PathValue(PATH_SEP.join(['[0]', 'a']), 'A')],
                     values.path_values)
    pred = PathPredicate('b')
    values = pred(source)
    self.assertEqual([PathValue(PATH_SEP.join(['[0]', 'b']), 'B')],
                     values.path_values)
    self.assertEqual([], values.path_failures)

  def test_collect_from_list_not_found(self):
    # """Ambiguous path passes through a list element but cannot be resolved."""
    source = [_LETTER_DICT]
    pred = PathPredicate('Z')
    values = pred(source)
    self.assertEqual([], values.path_values)
    self.assertEqual(
        [MissingPathError(
            _LETTER_DICT, 'Z', path_value=PathValue('[0]', _LETTER_DICT))],
        values.path_failures)

  def test_collect_plain_terminal_list(self):
    # """Path to a value that is a list."""
    source = {'a': [_LETTER_DICT]}
    pred = PathPredicate('a' + DONT_ENUMERATE_TERMINAL)
    values = pred(source)
    self.assertEqual([PathValue('a', [_LETTER_DICT])], values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate(PATH_SEP.join(['a', 'a']))
    values = pred(source)
    self.assertEqual([PathValue(PATH_SEP.join(['a[0]', 'a']), 'A')],
                     values.path_values)
    self.assertEqual([], values.path_failures)

  def test_collect_enumerated_terminal_list(self):
    # """Enumerated path to a value that is a list."""
    array = ['A', 'B', 'C']
    source = {'a': array}
    pred = PathPredicate('a' + PATH_SEP)
    values = pred(source)
    self.assertEqual([PathValue('a[0]', 'A'),
                      PathValue('a[1]', 'B'),
                      PathValue('a[2]', 'C')],
                     values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate('a')
    values = pred(source)
    self.assertEqual([PathValue('a[0]', 'A'),
                      PathValue('a[1]', 'B'),
                      PathValue('a[2]', 'C')],
                     values.path_values)
    self.assertEqual([], values.path_failures)

  def test_collect_from_list_with_index(self):
    # """Path with explicit list indexes to traverse."""
    source = [_LETTER_DICT, _NUMBER_DICT]
    pred = PathPredicate('[0]')
    values = pred(source)
    self.assertEqual([PathValue('[0]', _LETTER_DICT)], values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate('[1]')
    values = pred(source)
    self.assertEqual([PathValue('[1]', _NUMBER_DICT)], values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate(PATH_SEP.join(['[1]', 'a']))
    values = pred(source)
    self.assertEqual([PathValue('[1]/a', 1)], values.path_values)
    self.assertEqual([], values.path_failures)


  def test_collect_from_list_of_list_with_index(self):
    # """Path with explicit list indexes to traverse through nested lists."""
    upper = ['A', 'B', 'C']
    lower = ['a', 'b', 'c']
    letters = [upper, lower]
    arabic = [1, 2, 3]
    roman = ['i', 'ii', 'iii']
    numbers = [arabic, roman]
    source = [letters, numbers]

    # By default, values that are lists get expanded (one level)
    pred = PathPredicate('[1]')
    values = pred(source)
    self.assertEquals([PathValue('[1][0]', arabic),
                       PathValue('[1][1]', roman)],
                      values.path_values)
    self.assertEqual([], values.path_failures)

    # If we dont want to expand, then decorate with DONT_ENUMERATE_TERMINAL.
    pred = PathPredicate('[0]' + DONT_ENUMERATE_TERMINAL)
    values = pred(source)
    self.assertEqual([PathValue('[0]', letters)], values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate('[1]' + DONT_ENUMERATE_TERMINAL)
    values = pred(source)
    self.assertEqual([PathValue('[1]', numbers)], values.path_values)
    self.assertEqual([], values.path_failures)

    # Go out one more level
    pred = PathPredicate('[1][0]' + DONT_ENUMERATE_TERMINAL)
    values = pred(source)
    self.assertEqual([PathValue('[1][0]', arabic)], values.path_values)
    self.assertEqual([], values.path_failures)

    pred = PathPredicate('[1][0]')
    values = pred(source)
    self.assertEqual([PathValue('[1][0][0]', 1),
                      PathValue('[1][0][1]', 2),
                      PathValue('[1][0][2]', 3)],
                     values.path_values)
    self.assertEqual([], values.path_failures)

    # Go all the way down.
    pred = PathPredicate('[1][0][2]')
    values = pred(source)
    self.assertEqual([PathValue('[1][0][2]', 3)], values.path_values)
    self.assertEqual([], values.path_failures)


  def test_collect_from_nested_list_found(self):
    # """Ambiguous path through nested lists."""
    source = {'outer': [_LETTER_DICT, _NUMBER_DICT]}
    pred = PathPredicate(PATH_SEP.join(['outer', 'a']))
    values = pred(source)
    self.assertEqual([PathValue(PATH_SEP.join(['outer[0]', 'a']), 'A'),
                      PathValue(PATH_SEP.join(['outer[1]', 'a']), 1)],
                     values.path_values)

    pred = PathPredicate(PATH_SEP.join(['outer', 'z']))
    values = pred(source)
    self.assertEqual([PathValue(PATH_SEP.join(['outer[0]', 'z']), 'Z')],
                     values.path_values)
    self.assertEqual(
        [MissingPathError(
            _NUMBER_DICT, 'z',
            path_value=PathValue('outer[1]', _NUMBER_DICT))],
        values.path_failures)

    pred = PathPredicate(PATH_SEP.join(['outer', 'three']))
    values = pred(source)
    self.assertEqual([PathValue(PATH_SEP.join(['outer[1]', 'three']), 3)],
                     values.path_values)
    self.assertEqual(
        [MissingPathError(
            _LETTER_DICT, 'three',
            path_value=PathValue('outer[0]', _LETTER_DICT))],
        values.path_failures)

  def test_collect_from_nested_list_not_found(self):
    # """Path through nested lists that cannot be resolved."""
    source = {'outer': [_LETTER_DICT, _NUMBER_DICT]}
    pred = PathPredicate(PATH_SEP.join(['outer', 'X']))
    values = pred(source)
    self.assertEqual([], values.path_values)
    self.assertEqual(
        [MissingPathError(
            _LETTER_DICT, 'X',
            path_value=PathValue('outer[0]', _LETTER_DICT)),
         MissingPathError(
             _NUMBER_DICT, 'X',
             path_value=PathValue('outer[1]', _NUMBER_DICT))],
        values.path_failures)

  def test_collect_filter_good(self):
    source = {'outer': [_LETTER_DICT, _NUMBER_DICT]}
    filter_pred = TestEqualsPredicate(2)
    pred = PathPredicate(PATH_SEP.join(['outer', 'b']), pred=filter_pred)
    values = pred(source)
    self.assertEqual([PathValue(PATH_SEP.join(['outer[1]', 'b']), 2)],
                     values.path_values)

    self.assertEqual(
        [PathValueResult(pred=filter_pred, valid=False,
                         source=source, target_path='outer/b',
                         path_value=PathValue('outer[0]/b', 'B'))],
        values.path_failures)


if __name__ == '__main__':
  # pylint: disable=invalid-name
  loader = unittest.TestLoader()
  suite = loader.loadTestsFromTestCase(JsonPathPredicateTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
