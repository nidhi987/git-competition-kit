import importlib.util
import os

import pytest


def load_student_module():
    path = os.environ["SOLUTION_PATH"]
    spec = importlib.util.spec_from_file_location("student_solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def two_sum():
    return load_student_module().two_sum


def test_basic_pair(two_sum):
    assert sorted(two_sum([2, 7, 11, 15], 9)) == [0, 1]


def test_no_solution_at_start(two_sum):
    assert sorted(two_sum([3, 2, 4], 6)) == [1, 2]


def test_duplicate_values(two_sum):
    assert sorted(two_sum([3, 3], 6)) == [0, 1]
