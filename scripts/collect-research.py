#!/usr/bin/env python3
"""Collect a reproducible bibliographic index, not a clinical evidence synthesis.

Source documentation: https://europepmc.org/RestfulWebService
The response's metadata is used; abstracts are never written to the catalog.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import pathlib
import re
import time
import hashlib
import tempfile
import urllib.parse
import urllib.request

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
CUTOFF = "2026-11-04"
ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIENCE = '(TITLE_ABS:student OR TITLE_ABS:adolescent OR TITLE_ABS:school OR TITLE_ABS:college OR TITLE_ABS:university OR TITLE_ABS:youth OR TITLE_ABS:teenager)'
EXCLUDED_TYPES = '(PUB_TYPE:"Retracted Publication" OR PUB_TYPE:"Retraction of Publication" OR PUB_TYPE:"Published Erratum" OR PUB_TYPE:"Editorial" OR PUB_TYPE:"Comment" OR PUB_TYPE:"Letter" OR PUB_TYPE:"Case Reports")'
BASE = f'SRC:MED AND FIRST_PDATE:[1950-01-01 TO {CUTOFF}] AND LANG:eng NOT {EXCLUDED_TYPES}'

# Quotas add to exactly 1,000. Title screening further narrows abstract matches.
# Each group includes foundational and current publications in citation order.
TOPICS = [
 ("learning", "Learning & memory", 100,
  '(TITLE_ABS:"retrieval practice" OR TITLE_ABS:"testing effect" OR TITLE_ABS:"spaced repetition" OR TITLE_ABS:"distributed practice" OR TITLE_ABS:"spacing effect")',
  r'learn|memory|recall|retriev|testing|spacing|spaced|practice|retention|forget|metacognit'),
 ("strategies", "Study strategies", 100,
  f'(TITLE_ABS:"study strategies" OR TITLE_ABS:"learning strategies" OR TITLE_ABS:"worked examples" OR TITLE_ABS:"self-regulated learning" OR TITLE_ABS:interleaving OR TITLE_ABS:"self-explanation") AND {AUDIENCE}',
  r'learn|study|studying|worked|interleav|self.explan|metacognit|academic'),
 ("motivation", "Motivation & procrastination", 80,
  f'(TITLE_ABS:"academic procrastination" OR TITLE_ABS:"student motivation" OR TITLE_ABS:"academic motivation" OR TITLE_ABS:perfectionism OR TITLE_ABS:"self-determination theory") AND {AUDIENCE}',
  r'procrastinat|motivat|self.determ|goal|perfection|academic'),
 ("attention", "Attention & digital distraction", 80,
  f'(TITLE_ABS:"digital distraction" OR TITLE_ABS:"media multitasking" OR TITLE_ABS:"smartphone use" OR TITLE_ABS:"social media use" OR TITLE_ABS:"problematic smartphone") AND {AUDIENCE}',
  r'attention|distract|phone|social media|screen|digital|multitask|internet'),
 ("sleep", "Sleep & energy", 90,
  f'(TITLE_ABS:sleep OR TITLE_ABS:"school start times") AND {AUDIENCE}',
  r'sleep|school start|circadian|bedtime|insomnia'),
 ("stress", "Stress & emotions", 90,
  f'(TITLE_ABS:"academic stress" OR TITLE_ABS:"test anxiety" OR TITLE_ABS:"school stress" OR TITLE_ABS:"emotion regulation" OR TITLE_ABS:"student mental health") AND {AUDIENCE}',
  r'stress|anxiety|emotion|mental health|well.being|wellbeing|coping'),
 ("belonging", "Friends & belonging", 80,
  f'(TITLE_ABS:"school connectedness" OR TITLE_ABS:"school belonging" OR TITLE_ABS:loneliness OR TITLE_ABS:"peer support" OR TITLE_ABS:bullying) AND {AUDIENCE}',
  r'connect|belong|lonel|peer|friend|bully|bullying|social support'),
 ("grief", "Grief & family separation", 60,
  f'(TITLE_ABS:bereavement OR TITLE_ABS:grief OR TITLE_ABS:"parental incarceration" OR TITLE_ABS:"family separation" OR TITLE_ABS:homesickness) AND ({AUDIENCE} OR TITLE_ABS:child)',
  r'grief|bereave|parental death|parental loss|parental incarceration|family separat|homesick|mourning|parentally bereaved|death of a parent'),
 ("family", "Home & family", 70,
  f'(TITLE_ABS:"parental support" OR TITLE_ABS:"family conflict" OR TITLE_ABS:"parent-adolescent" OR TITLE_ABS:"parental involvement" OR TITLE_ABS:"family relationships") AND {AUDIENCE}',
  r'parent|family|families|home environment|caregiv'),
 ("access", "Learning & access", 70,
  f'(TITLE_ABS:"learning disabilities" OR TITLE_ABS:dyslexia OR TITLE_ABS:"academic accommodations" OR TITLE_ABS:"inclusive education" OR TITLE_ABS:"ADHD students" OR TITLE_ABS:"executive function") AND {AUDIENCE}',
  r'learn|dyslex|accommodat|inclusiv|disabilit|adhd|attention.deficit|executive|academic|school'),
 ("needs", "Money & basic needs", 60,
  f'(TITLE_ABS:"food insecurity" OR TITLE_ABS:"housing insecurity" OR TITLE_ABS:"basic needs" OR TITLE_ABS:"digital divide" OR TITLE_ABS:"financial stress") AND {AUDIENCE}',
  r'food insecur|housing|basic needs|digital divide|financial|poverty|homeless|socioeconomic|food secur|food sufficien|material hardship'),
 ("planning", "Time & planning", 50,
  f'(TITLE_ABS:"time management" OR TITLE_ABS:"implementation intentions" OR TITLE_ABS:"goal setting" OR TITLE_ABS:"academic workload" OR TITLE_ABS:"school absenteeism") AND {AUDIENCE}',
  r'time management|planning|implementation intention|goal|workload|absen|attendance|self.regulat'),
 ("future", "Future & expectations", 40,
  f'(TITLE_ABS:"career indecision" OR TITLE_ABS:"career anxiety" OR TITLE_ABS:"academic expectations" OR TITLE_ABS:"parental expectations" OR TITLE_ABS:"career decision" OR TITLE_ABS:"academic pressure") AND {AUDIENCE}',
  r'career|expectation|academic pressure|educational aspiration|future|college readiness'),
 ("support", "School support", 30,
  f'(TITLE_ABS:"school counseling" OR TITLE_ABS:"school counselling" OR TITLE_ABS:"help-seeking" OR TITLE_ABS:"school-based mental health") AND {AUDIENCE}',
  r'counsel|counsell|help.seek|school.based|support|mental health servic'),
]

BAD_TITLE = re.compile(r'\b(veterinar\w*|mice|mouse|rats?|rodent\w*|murine|zebrafish|macaque\w*|rhesus|canine|porcine|piglet\w*|drosophila|alzheimer\w*|parkinson\w*|dementia|neoplasm\w*|tumou?r\w*|dialysis|surgical|surgery|dental|dentist\w*|nurs\w*|physiotherap\w*|infants?|newborn\w*|neonatal|diabet\w*|cancer|carcinoma|oncolog\w*|antimicrobial|antibiotic\w*|inpatient|respiratory|cardiovascular|metabolic|medical|medicin\w*|physician\w*|surgeon\w*|anatomy|anatomical|radiolog\w*)\b|health profession|multiple sclerosis|cerebral palsy|patient portal|clinical education|clinical learning', re.I)
BAD_TYPE = re.compile(r'retract|erratum|editorial|comment|letter|case reports', re.I)
SPECIALTY_INTERVENTION_TITLE = re.compile(r'\b(adenotonsillectomy|tonsillectomy|adenoidectomy|surg\w*|operativ\w*|postoperativ\w*|preoperativ\w*|an[ae]esthe\w*|pharmac\w*|pharma\w*|medication\w*|methylphenidate|atomoxetine|amphetamine\w*|lisdexamfetamine|dexamphetamine|dexmethylphenidate|modafinil|armodafinil|melatonin|zolpidem|benzodiazepin\w*|antidepressant\w*|sertraline|fluoxetine|escitalopram|citalopram|paroxetine|bupropion|venlafaxine|duloxetine|ketamine|antipsychotic\w*|risperidone|aripiprazole|clonidine|guanfacine|placebo|geriatr\w*|neurodegenerat\w*)\b|mild cognitive impairment|drug (?:treatment|therap)', re.I)
OLDER_TREATMENT_TITLE = re.compile(r'(?=.*\b(?:older adults?|elderly|late.life|old.age)\b)(?=.*\b(?:therap\w*|treat\w*|depress\w*|symptom\w*|rehabilitat\w*|intervention\w*|program\w*|cognitive training)\b)', re.I)
AUDIENCE_RE = re.compile(r'\b(student\w*|adolescen\w*|youth\w*|teen\w*|child|children|childhood|school\w*|undergraduat\w*|pupil\w*)\b', re.I)
EDUCATIONAL_TITLE_RE = re.compile(r'\b(college|universit\w*|academic)\b', re.I)
TOPIC_EXCLUSIONS = {
    'strategies': re.compile(r'vegetable|flavou?r|food|nutrien|taste|intake|motor|movement|practitioner|health promotion', re.I),
    'needs': re.compile(r'ehealth|pregnan|lactat|perinatal|maternal|patient portal', re.I),
    'grief': re.compile(r'stillbirth|miscarriage|perinatal|pregnan|neonatal|prenatal|midlife|spouses|couples|congenital|fathers|bereaved (?:parents|older)|parental (?:grief|coping|burden)|death of (?:one.s|a|their|a young|their young) child|(?:a|their) child.s death|children.s deaths|losing a child|loss of a child|child dies|child has died|parents.{0,60}bereavement|bereavement.{0,60}parents', re.I),
    'planning': re.compile(r'diet|physical activ|exercise|sexual|condom|alcohol|smoking|substance|antibiotic|vaccin', re.I),
    'future': re.compile(r'pedestrian|marriage|parenthood|fertility|reproductive|obstet|anesthe|alcohol|substance|drinking|smoking|doctors?|midwif|clinical|urolog|telemedicine|pediatric|spina bifida|chronic pain', re.I),
}
GRIEF_TITLE_RE = re.compile(r'child|adolescen|youth|teen|student|school|college|universit|young people|family bereavement|parental death|parental loss|parental incarceration|family separat|homesick', re.I)
FUTURE_TITLE_RE = re.compile(r'career|academic|school|college|universit|future|calling|educat|aspir|achievement', re.I)

def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', str(value or '')))).strip()

def refresh_methods(meta, papers, path=ROOT/'RESEARCH_METHODS.md'):
    """Keep reported counts and dates synchronized with the generated corpus."""
    if not path.exists():
        return
    content = path.read_text()
    content = re.sub(r'generated at `[^`]+`', f"generated at `{meta['fetchedAt']}`", content)
    content = re.sub(r'first-publication cutoff of \*\*[^*]+\*\*', f"first-publication cutoff of **{meta['publicationCutoff']}**", content)
    content = re.sub(r'allocation skipped \*\*\d+ cross-topic duplicate candidates\*\*', f"allocation skipped **{meta['deduplication']['crossTopicDuplicatesSkippedDuringAllocation']} cross-topic duplicate candidates**", content)
    content = re.sub(r'Within-query duplicate records skipped: \*\*\d+\*\*', f"Within-query duplicate records skipped: **{meta['deduplication']['withinQueryDuplicatesSkipped']}**", content)
    doi_count = sum(bool(paper['doi']) for paper in papers)
    content = re.sub(r'\*\*\d+ nonempty, unique DOIs\*\*', f"**{doi_count} nonempty, unique DOIs**", content)
    for topic in meta['topics']:
        content = re.sub(r'^\| ' + re.escape(topic) + r' \| \d+ \| \d+ \|$', f"| {topic} | {meta['primaryTopicCounts'][topic]} | {meta['topicCounts'][topic]} |", content, flags=re.M)
    path.write_text(content)

def get_json(params):
    url = API + '?' + urllib.parse.urlencode(params)
    cache_dir = pathlib.Path(tempfile.gettempdir())/'next-step-research-cache-v1'
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'NextStepResearchCatalog/1.0 (bibliographic metadata index)'})
            with urllib.request.urlopen(request, timeout=55) as response:
                result = json.load(response)
            cache_file.write_text(json.dumps(result))
            return result
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)

def fetch_topic(topic):
    slug, label, quota, expression, title_pattern = topic
    query = f'({expression}) AND {BASE}'
    candidates, seen, cursor, examined, duplicate_candidates = [], set(), '*', 0, 0
    for page in range(3):
        result = get_json({'query': query, 'format': 'json', 'resultType': 'core', 'pageSize': 300, 'sort': 'CITED desc', 'cursorMark': cursor})
        for article in result.get('resultList', {}).get('result', []):
            examined += 1
            title = clean(article.get('title'))
            audience_text = title + ' ' + clean(article.get('abstractText'))
            types = (article.get('pubTypeList') or {}).get('pubType', [])
            corrections = (article.get('commentCorrectionList') or {}).get('commentCorrection', [])
            mesh_terms = {m.get('descriptorName') for m in (article.get('meshHeadingList') or {}).get('meshHeading', [])}
            if (not title or article.get('source') != 'MED' or BAD_TITLE.search(title)
                or SPECIALTY_INTERVENTION_TITLE.search(title)
                or OLDER_TREATMENT_TITLE.search(title)
                or not re.search(title_pattern, title, re.I)
                or (slug != 'learning' and not (AUDIENCE_RE.search(audience_text) or EDUCATIONAL_TITLE_RE.search(title)))
                or ('Animals' in mesh_terms and 'Humans' not in mesh_terms)
                or (slug in TOPIC_EXCLUSIONS and TOPIC_EXCLUSIONS[slug].search(title))
                or (slug == 'grief' and not GRIEF_TITLE_RE.search(title))
                or (slug == 'future' and not FUTURE_TITLE_RE.search(title))
                or not clean(article.get('authorString'))
                or any(BAD_TYPE.search(t) for t in types)
                or any('retract' in c.get('type', '').lower() for c in corrections)
                or article.get('isRetracted') == 'Y'):
                continue
            pmid = str(article.get('id', ''))
            doi = clean(article.get('doi')).lower() or None
            date = article.get('firstPublicationDate', '')
            if not pmid.isdigit() or (date and date > CUTOFF):
                continue
            year = int(article.get('pubYear') or 0)
            if not 1950 <= year <= 2026:
                continue
            key = doi or pmid
            if key in seen:
                duplicate_candidates += 1
                continue
            seen.add(key)
            ptype = 'Meta-analysis' if any('meta-analysis' in t.lower() for t in types) else 'Systematic review' if any('systematic review' in t.lower() for t in types) else 'Review' if any(t.lower() == 'review' for t in types) else 'Randomized controlled trial' if any('randomized controlled trial' in t.lower() for t in types) else 'Clinical trial' if any('clinical trial' in t.lower() for t in types) else 'Journal article'
            authors = clean(article.get('authorString'))
            if len(authors) > 200:
                authors = ', '.join(authors.split(', ')[:3]) + ', et al.'
            journal = article.get('journalInfo', {}).get('journal', {}).get('title') or article.get('journalTitle') or 'Journal not supplied'
            candidates.append({'id': 'PMID:' + pmid, 'title': title, 'authors': authors, 'year': year, 'journal': clean(journal), 'doi': doi, 'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/', 'topics': [label], 'type': ptype, 'citedBy': int(article.get('citedByCount') or 0), 'status': 'Indexed', 'source': 'Europe PMC / PubMed', 'queryId': slug})
        cursor = result.get('nextCursorMark')
        if len(candidates) >= quota + 50 or not cursor or not result.get('resultList', {}).get('result'):
            break
    print(f'{label}: {len(candidates)} eligible candidates; quota {quota}; examined {examined}', flush=True)
    return {'id': slug, 'label': label, 'quota': quota, 'query': query, 'candidates': candidates, 'examined': examined, 'withinQueryDuplicatesSkipped': duplicate_candidates}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=pathlib.Path, default=ROOT/'src/research-catalog.json')
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    assert sum(t[2] for t in TOPICS) == 1000
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(4, args.workers))) as pool:
        topic_results = list(pool.map(fetch_topic, TOPICS))
    selected, identities, primary_counts, cross_topic_duplicates = [], set(), {}, 0
    # Deterministic quota allocation, with cross-topic deduplication.
    for group in topic_results:
        count = 0
        for paper in group['candidates']:
            keys = [paper['id'], re.sub(r'\W+', '', paper['title'].lower())]
            if paper['doi']:
                keys.append(paper['doi'])
            if any(k in identities for k in keys):
                cross_topic_duplicates += 1
                continue
            selected.append(paper)
            identities.update(keys)
            count += 1
            if count == group['quota']:
                break
        primary_counts[group['label']] = count
        if count < group['quota']:
            raise RuntimeError(f"Insufficient unique records for {group['label']}: {count}/{group['quota']}")
    assert len(selected) == 1000
    # Add useful secondary topic labels for papers returned by multiple queries.
    selected_by_id = {p['id']: p for p in selected}
    for paper in selected:
        paper['queryIds'] = [paper['queryId']]
    for group in topic_results:
        for candidate in group['candidates']:
            paper = selected_by_id.get(candidate['id'])
            if paper is not None and group['label'] not in paper['topics']:
                paper['topics'].append(group['label'])
                paper['queryIds'].append(group['id'])
    selected.sort(key=lambda p: (-p['citedBy'], -p['year'], p['title']))
    fetched_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    topic_counts = {g['label']: sum(g['label'] in p['topics'] for p in selected) for g in topic_results}
    meta = {'count': len(selected), 'fetchedAt': fetched_at, 'publicationCutoff': CUTOFF, 'source': 'Europe PMC REST API, PubMed-indexed records (SRC:MED)', 'sourceUrl': 'https://europepmc.org/RestfulWebService', 'status': 'Bibliographic index; not individually appraised', 'method': 'Topic quotas, citation-ranked database queries, automated metadata/title screening, DOI/PMID/title deduplication. Full texts were not reviewed.', 'topics': [g['label'] for g in topic_results], 'topicCounts': topic_counts, 'primaryTopicCounts': primary_counts, 'deduplication': {'withinQueryDuplicatesSkipped': sum(g['withinQueryDuplicatesSkipped'] for g in topic_results), 'crossTopicDuplicatesSkippedDuringAllocation': cross_topic_duplicates, 'selectedUniqueRecords': len(selected)}, 'queries': [{k: g[k] for k in ['id', 'label', 'quota', 'query', 'examined', 'withinQueryDuplicatesSkipped']} for g in topic_results], 'limits': ['Indexing does not establish study quality, causal effects, or effectiveness of this app.', 'Topic labels are based on database queries and title screening, not individual evidence appraisal.', 'English-language PubMed coverage favors health and psychology; this is not a systematic or exhaustive education literature review.', 'Citation ranking favors older and widely cited publications.', 'Publication-type and retraction filtering depend on current source metadata.', 'The publication cutoff does not mean every record was available in the database on that date.'], 'publicationTypeCounts': {t: sum(p['type'] == t for p in selected) for t in sorted(set(p['type'] for p in selected))}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'meta': meta, 'papers': selected}, ensure_ascii=False, indent=2) + '\n')
    summary = {k: meta[k] for k in ['count', 'fetchedAt', 'topics', 'topicCounts']}
    summary['cutoff'] = CUTOFF
    summary['status'] = 'Indexed records; not individually appraised'
    args.output.with_name('research-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    if args.output.resolve() == (ROOT/'src/research-catalog.json').resolve():
        refresh_methods(meta, selected)
    print(json.dumps({'count': len(selected), 'topicCounts': topic_counts, 'types': meta['publicationTypeCounts'], 'output': str(args.output)}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
