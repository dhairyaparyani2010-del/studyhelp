import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const readJson = file => JSON.parse(readFileSync(new URL(file, import.meta.url), 'utf8'));
const { meta, papers } = readJson('./research-catalog.json');
const summary = readJson('./research-summary.json');
const doiPapers = papers.filter(paper => paper.doi !== null);
const normalizedTitle = title => title.toLowerCase().replace(/[^\p{L}\p{N}_]/gu, '');
const typeLabels = new Set(['Journal article', 'Review', 'Systematic review', 'Meta-analysis', 'Clinical trial', 'Randomized controlled trial']);
const queries = new Map(meta.queries.map(query => [query.id, query]));
const countsBy = getKeys => {
  const counts = {};
  for (const paper of papers) for (const key of getKeys(paper)) counts[key] = (counts[key] || 0) + 1;
  return counts;
};

test('the public research count represents exactly 1,000 distinct publications', () => {
  assert.equal(papers.length, 1000);
  assert.equal(meta.count, papers.length);
  assert.equal(meta.deduplication.selectedUniqueRecords, papers.length);
  assert.equal(new Set(papers.map(paper => paper.id)).size, papers.length, 'duplicate PMID');
  assert.equal(new Set(doiPapers.map(paper => paper.doi.toLowerCase())).size, doiPapers.length, 'duplicate DOI');
  assert.equal(new Set(papers.map(paper => normalizedTitle(paper.title))).size, papers.length, 'duplicate normalized title');
});

test('every indexed record carries usable bibliographic metadata and a canonical source link', () => {
  const cutoffYear = Number(meta.publicationCutoff.slice(0, 4));
  for (const paper of papers) {
    assert.match(paper.id, /^PMID:\d+$/);
    for (const field of ['title', 'authors', 'journal']) {
      assert.equal(typeof paper[field], 'string', `${paper.id}: ${field}`);
      assert.ok(paper[field].trim(), `${paper.id}: empty ${field}`);
    }
    assert.ok(Number.isInteger(paper.year) && paper.year >= 1950 && paper.year <= cutoffYear, `${paper.id}: publication year`);
    assert.ok(typeLabels.has(paper.type), `${paper.id}: unknown publication type ${paper.type}`);
    assert.ok(Number.isInteger(paper.citedBy) && paper.citedBy >= 0, `${paper.id}: citation count`);
    assert.equal(paper.url, `https://pubmed.ncbi.nlm.nih.gov/${paper.id.slice(5)}/`);
    if (paper.doi !== null) assert.match(paper.doi, /^10\.\d{4,9}\/\S+$/i, `${paper.id}: DOI format`);
    assert.equal(paper.status, 'Indexed');
    assert.equal(paper.source, 'Europe PMC / PubMed');
    assert.ok(!Object.keys(paper).some(key => /abstract|fulltext/i.test(key)), `${paper.id}: full text should not be in the index`);
  }
});

test('the student index excludes identified specialty-treatment mismatches while retaining foundational learning experiments', () => {
  const ids = new Set(papers.map(paper => paper.id));
  for (const id of ['PMID:15222820', 'PMID:23692173', 'PMID:19139252']) {
    assert.ok(!ids.has(id), `${id}: previously identified older-adult treatment or surgical mismatch`);
  }
  for (const id of ['PMID:16507066', 'PMID:18276894']) {
    assert.ok(ids.has(id), `${id}: foundational student learning experiment was unexpectedly excluded`);
  }
  for (const paper of papers) {
    assert.doesNotMatch(paper.title, /\b(?:adenotonsillectomy|tonsillectomy|adenoidectomy|methylphenidate|atomoxetine|pharmacotherap\w*|pharmacolog\w*|placebo|melatonin|alzheimer\w*|dementia)\b/i, `${paper.id}: specialty-treatment title`);
    if (/\b(?:older adults?|elderly)\b/i.test(paper.title)) {
      assert.doesNotMatch(paper.title, /\b(?:therapy|treatment|depressive|rehabilitation|intervention|program)\b/i, `${paper.id}: older-adult intervention title`);
    }
  }
});

test('every topic label resolves to the source query that supplied the record', () => {
  assert.equal(new Set(meta.topics).size, meta.topics.length);
  assert.equal(queries.size, meta.queries.length);
  assert.deepEqual(new Set(meta.queries.map(query => query.label)), new Set(meta.topics));
  for (const query of meta.queries) {
    assert.match(query.query, /SRC:MED/);
    assert.ok(query.query.includes(`FIRST_PDATE:[1950-01-01 TO ${meta.publicationCutoff}]`));
    assert.ok(Number.isInteger(query.quota) && query.quota > 0);
    assert.ok(Number.isInteger(query.examined) && query.examined >= query.quota);
    assert.ok(Number.isInteger(query.withinQueryDuplicatesSkipped) && query.withinQueryDuplicatesSkipped >= 0);
  }
  for (const paper of papers) {
    assert.ok(paper.topics.length > 0, `${paper.id}: missing topic`);
    assert.equal(new Set(paper.topics).size, paper.topics.length, `${paper.id}: duplicate topic`);
    assert.equal(new Set(paper.queryIds).size, paper.queryIds.length, `${paper.id}: duplicate query provenance`);
    assert.ok(paper.queryIds.includes(paper.queryId), `${paper.id}: missing primary provenance`);
    assert.equal(queries.get(paper.queryId)?.label, paper.topics[0], `${paper.id}: primary topic/provenance mismatch`);
    assert.deepEqual(new Set(paper.queryIds.map(id => queries.get(id)?.label)), new Set(paper.topics), `${paper.id}: topic/provenance mismatch`);
  }
});

test('topic allocations and publication-type counts describe the records actually included', () => {
  assert.deepEqual(countsBy(paper => [paper.topics[0]]), meta.primaryTopicCounts);
  assert.deepEqual(countsBy(paper => paper.topics), meta.topicCounts);
  assert.deepEqual(countsBy(paper => [paper.type]), meta.publicationTypeCounts);
  assert.equal(Object.values(meta.primaryTopicCounts).reduce((a, b) => a + b, 0), 1000);
  for (const query of meta.queries) assert.equal(meta.primaryTopicCounts[query.label], query.quota);
});

test('the homepage summary and methods document agree with the complete catalog', () => {
  assert.equal(summary.count, papers.length);
  assert.equal(summary.fetchedAt, meta.fetchedAt);
  assert.ok(Number.isFinite(Date.parse(meta.fetchedAt)));
  assert.equal(summary.cutoff, meta.publicationCutoff);
  assert.deepEqual(summary.topics, meta.topics);
  assert.deepEqual(summary.topicCounts, meta.topicCounts);
  assert.match(summary.status, /not individually appraised/i);
  assert.match(meta.status, /not individually appraised/i);
  const methods = readFileSync(new URL('../RESEARCH_METHODS.md', import.meta.url), 'utf8');
  assert.ok(methods.includes(`**${doiPapers.length} nonempty, unique DOIs**`), 'document DOI count is stale');
  assert.ok(methods.includes(`generated at \`${meta.fetchedAt}\``), 'document collection date is stale');
  for (const topic of meta.topics) assert.ok(methods.includes(`| ${topic} | ${meta.primaryTopicCounts[topic]} | ${meta.topicCounts[topic]} |`), `document topic counts are stale: ${topic}`);
});
