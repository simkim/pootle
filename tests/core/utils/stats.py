# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.utils.stats import get_top_scorers_data


class TestUser(object):
    def __init__(self, email, display_name, username):
        self.email = email
        self.display_name = display_name
        self.username = username


TEST_TOP_SCORERS = [
    dict(
        public_total_score=1,
        suggested=0,
        translated=1,
        reviewed=0,
        user=TestUser(
            email='test0@poot.le',
            display_name='Test0',
            username='test0',
        )
    ),
    dict(
        public_total_score=3,
        suggested=1,
        translated=2,
        reviewed=1,
        user=TestUser(
            email='test1@poot.le',
            display_name='Test1',
            username='test1',
        )
    )
]


@pytest.mark.parametrize('top_scorers, chunk_size', [
    (TEST_TOP_SCORERS, 1),
    (TEST_TOP_SCORERS, 2),
])
def test_get_top_scorers_data(top_scorers, chunk_size):
    has_more_scorers = len(top_scorers) > chunk_size
    top_scorer_items = [
        dict(
            public_total_score=x['public_total_score'],
            suggested=x['suggested'],
            translated=x['translated'],
            reviewed=x['reviewed'],
            email=x['user'].email,
            display_name=x['user'].display_name,
            username=x['user'].username,
        )
        for x in top_scorers[:chunk_size]
    ]
    assert (
        get_top_scorers_data(top_scorers, chunk_size) == dict(
            items=top_scorer_items,
            has_more_items=has_more_scorers,
        )
    )
