import test from 'node:test';
import assert from 'node:assert/strict';
import { categories } from './data.js';
import { cards, evidenceSources, getCard } from './content.js';

test('every selectable detail has a complete, distinct action card', () => {
  const details = categories.flatMap(category => category.subs);
  assert.deepEqual(Object.keys(cards).sort(), [...details].sort());
  assert.equal(new Set(Object.values(cards).map(card => card.first)).size, details.length);
  for (const detail of details) {
    const card = getCard(detail);
    for (const field of ['title', 'first', 'smaller', 'support', 'note']) {
      assert.equal(typeof card[field], 'string', `${detail}: ${field}`);
      assert.ok(card[field].trim(), `${detail}: empty ${field}`);
    }
    assert.equal(card.steps.length, 3, detail);
    assert.ok(card.steps.every(step => typeof step === 'string' && step.trim()), detail);
    assert.ok(['study', 'support', 'practical'].includes(card.kind), detail);
    assert.ok(Array.isArray(card.sourceIds), detail);
  }
});

test('references resolve to real source records with visible scope limits', () => {
  const sourceIds = new Set(evidenceSources.map(source => source.id));
  assert.equal(sourceIds.size, evidenceSources.length);
  assert.ok(evidenceSources.length >= 15 && evidenceSources.length <= 25);
  for (const source of evidenceSources) {
    assert.equal(new URL(source.url).protocol, 'https:');
    assert.ok(source.claim && source.limit && source.org && source.reviewStatus);
    assert.equal(source.checked, '2026-11-04');
    assert.match(source.reviewStatus, /untested/);
  }
  for (const [detail, card] of Object.entries(cards)) {
    for (const id of card.sourceIds) assert.ok(sourceIds.has(id), `${detail}: missing ${id}`);
    if (!card.sourceIds.length) assert.match(card.note, /App-designed support navigation; qualified review pending/);
  }
});

test('sensitive wellbeing routes offer support rather than compulsory study', () => {
  const sensitive = [
    'Persistent sadness', 'Feeling numb or empty', 'A loved one died',
    'Threats, violence, control, or feeling unsafe',
    'Concerned that someone’s whereabouts are unknown', 'Unhealthy relationship',
  ];
  for (const detail of sensitive) {
    assert.equal(cards[detail].kind, 'support', detail);
    assert.ok(cards[detail].support.trim(), detail);
    assert.match(cards[detail].note, /review|cannot/i, detail);
    assert.doesNotMatch(cards[detail].first, /start (?:your )?(?:schoolwork|studying)/i, detail);
  }
  assert.notEqual(cards['A loved one died'].first, cards['Family lives far away'].first);
  assert.match(cards['A loved one died'].steps.join(' '), /schoolwork is optional/i);
  assert.match(cards['Threats, violence, control, or feeling unsafe'].first, /emergency|safe nearby/i);
  assert.match(cards['Concerned that someone’s whereabouts are unknown'].first, /trusted adult|emergency/i);
  assert.match(cards['Threats, violence, control, or feeling unsafe'].steps.join(' '), /avoid confronting/i);
});

test('practical barriers receive practical navigation without promises of benefits', () => {
  for (const detail of categories.find(category => category.id === 'needs').subs) {
    assert.equal(cards[detail].kind, 'practical', detail);
    assert.doesNotMatch(cards[detail].first, /motivat|work harder|just study/i, detail);
  }
  assert.match(cards['Not enough food'].first, /food/i);
  assert.match(cards['Unstable housing'].support, /liaison/i);
  assert.equal(getCard('__proto__'), undefined);
  assert.equal(getCard('unknown detail'), undefined);
});
