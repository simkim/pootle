# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from translate.storage import factory
from translate.storage.factory import getclass
from translate.storage.pypo import pounit

from django.contrib.auth import get_user_model
from django.utils import timezone

from pootle.core.mixins.treeitem import CachedMethods
from pootle_store.constants import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED
from pootle_store.models import Unit
from pootle_store.syncer import UnitSyncer


User = get_user_model()


def _update_translation(store, item, new_values, sync=True):
    unit = store.units[item]

    if 'target' in new_values:
        unit.target = new_values['target']

    if 'fuzzy' in new_values:
        unit.markfuzzy(new_values['fuzzy'])

    if 'translator_comment' in new_values:
        unit.translator_comment = new_values['translator_comment']
        unit._comment_updated = True

    unit.submitted_on = timezone.now()
    unit.submitted_by = User.objects.get_system_user()
    unit.save()

    if sync:
        store.sync()

    return store.units[item]


@pytest.mark.django_db
def test_getorig(store0):
    """Tests that the in-DB Store and on-disk Store match by checking that
    units match in order.
    """
    store0.sync()
    for i, db_unit in enumerate(store0.units.iterator()):
        store_unit = store0.file.store.units[i + 1]
        assert db_unit.getid() == store_unit.getid()


@pytest.mark.django_db
def test_convert(store0):
    """Tests that in-DB and on-disk units match after format conversion."""
    store0.sync()
    for db_unit in store0.units.iterator():
        store_unit = store0.file.store.findid(db_unit.getid())
        newunit = db_unit.convert(store0.file.store.UnitClass)

        assert str(newunit) == str(store_unit)


@pytest.mark.django_db
def test_update_target(store0):
    """Tests that target changes are properly sync'ed to disk."""
    db_unit = _update_translation(store0, 0, {'target': u'samaka'})
    store0.sync()
    store_unit = store0.file.store.findid(db_unit.getid())

    assert db_unit.target == u'samaka'
    assert db_unit.target == store_unit.target

    po_file = factory.getobject(store0.file.path)
    assert db_unit.target == po_file.findid(db_unit.unitid).target


@pytest.mark.django_db
def test_empty_plural_target(af_tutorial_po):
    """Tests empty plural targets are not deleted."""
    db_unit = _update_translation(af_tutorial_po, 2, {'target': [u'samaka']})
    store_unit = af_tutorial_po.file.store.findid(db_unit.getid())
    assert len(store_unit.target.strings) == 2

    db_unit = _update_translation(af_tutorial_po, 2, {'target': u''})
    assert len(store_unit.target.strings) == 2


@pytest.mark.django_db
def test_update_plural_target(af_tutorial_po):
    """Tests plural translations are stored and sync'ed."""
    db_unit = _update_translation(
        af_tutorial_po, 2,
        {'target': [u'samaka', u'samak']})
    store_unit = af_tutorial_po.file.store.findid(db_unit.getid())

    assert db_unit.target.strings == [u'samaka', u'samak']
    assert db_unit.target.strings == store_unit.target.strings

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert (
        db_unit.target.strings
        == po_file.units[db_unit.index].target.strings)

    assert db_unit.target == u'samaka'
    assert db_unit.target == store_unit.target
    assert db_unit.target == po_file.units[db_unit.index].target


@pytest.mark.django_db
def test_update_plural_target_dict(af_tutorial_po):
    """Tests plural translations are stored and sync'ed (dict version)."""
    db_unit = _update_translation(
        af_tutorial_po, 2,
        {'target': {0: u'samaka', 1: u'samak'}})
    store_unit = af_tutorial_po.file.store.findid(db_unit.getid())

    assert db_unit.target.strings == [u'samaka', u'samak']
    assert db_unit.target.strings == store_unit.target.strings

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert (
        db_unit.target.strings
        == po_file.findid(db_unit.getid()).target.strings)

    assert db_unit.target == u'samaka'
    assert db_unit.target == store_unit.target
    assert db_unit.target == po_file.findid(db_unit.getid()).target


@pytest.mark.django_db
def test_update_fuzzy(store0):
    """Tests fuzzy state changes are stored and sync'ed."""
    db_unit = _update_translation(
        store0, 0,
        {'target': u'samaka', 'fuzzy': True})
    store_unit = store0.file.store.findid(db_unit.getid())

    assert db_unit.isfuzzy()
    assert db_unit.isfuzzy() == store_unit.isfuzzy()

    po_file = factory.getobject(store0.file.path)
    assert db_unit.isfuzzy() == po_file.findid(db_unit.getid()).isfuzzy()

    db_unit = _update_translation(store0, 0, {'fuzzy': False})
    store_unit = store0.file.store.findid(db_unit.getid())

    assert not db_unit.isfuzzy()
    assert db_unit.isfuzzy() == store_unit.isfuzzy()

    po_file = factory.getobject(store0.file.path)
    assert db_unit.isfuzzy() == po_file.findid(db_unit.getid()).isfuzzy()


@pytest.mark.django_db
def test_update_comment(store0):
    """Tests translator comments are stored and sync'ed."""
    db_unit = _update_translation(
        store0, 0,
        {'translator_comment': u'7amada'})
    store0.sync()
    store_unit = store0.file.store.findid(db_unit.getid())

    assert db_unit.getnotes(origin='translator') == u'7amada'
    assert (
        db_unit.getnotes(origin='translator')
        == store_unit.getnotes(origin='translator'))

    po_file = factory.getobject(store0.file.path)
    assert (
        db_unit.getnotes(origin='translator')
        == po_file.findid(db_unit.getid()).getnotes(origin='translator'))


@pytest.mark.django_db
def test_add_suggestion(store0, system):
    """Tests adding new suggestions to units."""
    untranslated_unit = store0.units.filter(state=UNTRANSLATED)[0]
    translated_unit = store0.units.filter(state=TRANSLATED)[0]
    suggestion_text = 'foo bar baz'

    initial_suggestions = len(untranslated_unit.get_suggestions())

    # Empty suggestion is not recorded
    sugg, added = untranslated_unit.add_suggestion('')
    assert sugg is None
    assert not added

    # Existing translation can't be added as a suggestion
    sugg, added = translated_unit.add_suggestion(translated_unit.target)
    assert sugg is None
    assert not added

    # Add new suggestion
    sugg, added = untranslated_unit.add_suggestion(suggestion_text)
    assert sugg is not None
    assert added
    assert len(untranslated_unit.get_suggestions()) == initial_suggestions + 1

    # Already-suggested text can't be suggested again
    sugg, added = untranslated_unit.add_suggestion(suggestion_text)
    assert sugg is not None
    assert not added
    assert len(untranslated_unit.get_suggestions()) == initial_suggestions + 1

    # Removing a suggestion should allow suggesting the same text again
    tp = untranslated_unit.store.translation_project
    untranslated_unit.reject_suggestion(sugg, tp, system)
    assert len(untranslated_unit.get_suggestions()) == initial_suggestions

    sugg, added = untranslated_unit.add_suggestion(suggestion_text)
    assert sugg is not None
    assert added
    assert len(untranslated_unit.get_suggestions()) == initial_suggestions + 1


@pytest.mark.django_db
def test_accept_suggestion_changes_state(issue_2401_po, system):
    """Tests that accepting a suggestion will change the state of the unit."""
    tp = issue_2401_po.translation_project

    # First test with an untranslated unit
    unit = issue_2401_po.units[0]
    assert unit.state == UNTRANSLATED

    suggestion, created_ = unit.add_suggestion('foo')
    assert unit.state == UNTRANSLATED

    unit.accept_suggestion(suggestion, tp, system)
    assert unit.state == TRANSLATED

    # Let's try with a translated unit now
    unit = issue_2401_po.units[1]
    assert unit.state == TRANSLATED

    suggestion, created_ = unit.add_suggestion('bar')
    assert unit.state == TRANSLATED

    unit.accept_suggestion(suggestion, tp, system)
    assert unit.state == TRANSLATED

    # And finally a fuzzy unit
    unit = issue_2401_po.units[2]
    assert unit.state == FUZZY

    suggestion, created_ = unit.add_suggestion('baz')
    assert unit.state == FUZZY

    unit.accept_suggestion(suggestion, tp, system)
    assert unit.state == TRANSLATED


@pytest.mark.django_db
def test_accept_suggestion_update_wordcount(it_tutorial_po, system):
    """Tests that accepting a suggestion for an untranslated unit will
    change the wordcount stats of the unit's store.
    """

    # Parse store
    it_tutorial_po.update(it_tutorial_po.file.store)

    untranslated_unit = it_tutorial_po.units[0]
    suggestion_text = 'foo bar baz'

    sugg, added = untranslated_unit.add_suggestion(suggestion_text)
    assert sugg is not None
    assert added
    assert len(untranslated_unit.get_suggestions()) == 1
    assert it_tutorial_po.get_cached(CachedMethods.SUGGESTIONS) == 1
    assert (
        it_tutorial_po.get_cached(CachedMethods.WORDCOUNT_STATS)['translated']
        == 1)
    assert untranslated_unit.state == UNTRANSLATED
    untranslated_unit.accept_suggestion(sugg,
                                        it_tutorial_po.translation_project,
                                        system)
    assert untranslated_unit.state == TRANSLATED
    assert (
        it_tutorial_po.get_cached(CachedMethods.WORDCOUNT_STATS)['translated']
        == 2)


@pytest.mark.django_db
def test_unit_repr():
    unit = Unit.objects.first()
    assert str(unit) == str(unit.convert())
    assert unicode(unit) == unicode(unit.source)


@pytest.mark.django_db
def test_unit_po_plurals(store_po):
    unit = Unit(store=store_po, index=1)
    unit_po = pounit('bar')
    unit_po.msgid_plural = ['bars']
    unit.update(unit_po)
    assert unit.hasplural()
    unit.save()
    assert unit.hasplural()


@pytest.mark.django_db
def test_unit_ts_plurals(store_po, test_fs):
    with test_fs.open(['data', 'ts', 'add_plurals.ts']) as f:
        file_store = getclass(f)(f.read())
    unit = Unit(store=store_po, index=1)
    unit_ts = file_store.units[0]
    unit.update(unit_ts)
    assert unit.hasplural()
    unit.save()
    unit = Unit.objects.get(id=unit.id)
    assert unit.hasplural()
    unit.save()
    unit = Unit.objects.get(id=unit.id)
    assert unit.hasplural()


def _test_unit_syncer(unit, newunit):
    assert newunit.source == unit.source
    assert newunit.target == unit.target
    assert newunit.getid() == unit.getid()
    assert newunit.istranslated() == unit.istranslated()
    assert (
        newunit.getnotes(origin="developer")
        == unit.getnotes(origin="developer"))
    assert (
        newunit.getnotes(origin="translator")
        == unit.getnotes(origin="translator"))
    assert newunit.isobsolete() == unit.isobsolete()
    assert newunit.isfuzzy() == unit.isfuzzy()


@pytest.mark.django_db
def test_unit_syncer(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    newunit = syncer.convert(unit_class)
    assert newunit.istranslated()
    assert not newunit.isfuzzy()
    assert not newunit.isobsolete()
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_fuzzy(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    unit.state = FUZZY
    unit.save()
    newunit = syncer.convert(unit_class)
    assert newunit.isfuzzy()
    assert not newunit.isobsolete()
    assert not newunit.istranslated()
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_untranslated(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    unit.state = UNTRANSLATED
    unit.target = ""
    unit.save()
    newunit = syncer.convert(unit_class)
    assert not newunit.isfuzzy()
    assert not newunit.isobsolete()
    assert not newunit.istranslated()
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_obsolete(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    unit.state = OBSOLETE
    unit.save()
    newunit = syncer.convert(unit_class)
    assert newunit.isobsolete()
    assert not newunit.isfuzzy()
    assert not newunit.istranslated()
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_notes(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    unit.addnote(origin="developer", text="hello")
    newunit = syncer.convert(unit_class)
    assert newunit.getnotes(origin="developer") == "hello"
    _test_unit_syncer(unit, newunit)

    unit.addnote(origin="translator", text="world")
    newunit = syncer.convert(unit_class)
    assert newunit.getnotes(origin="translator") == "world"
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_locations(unit_syncer):
    unit, unit_class = unit_syncer
    unit.addlocation("FOO")
    syncer = UnitSyncer(unit)
    newunit = syncer.convert(unit_class)
    assert newunit.getlocations() == ["FOO"]
    _test_unit_syncer(unit, newunit)
