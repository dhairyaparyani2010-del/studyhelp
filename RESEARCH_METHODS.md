# Next Step research catalog: collection methods

The catalog contains **1,000 unique PubMed-indexed publication records**. It was generated at `2026-11-05T04:26:16+00:00` (UTC), with a first-publication cutoff of **2026-11-04**. This is a searchable bibliographic index, not a systematic review or an evaluation of the app.

## Source and reproducibility

Records come from the official Europe PMC REST search endpoint, restricted to PubMed records (`SRC:MED`). Official documentation: https://europepmc.org/RestfulWebService and https://dev.europepmc.org/docs/EBI_Europe_PMC_Web_Service_Reference.pdf .

Run `python3 scripts/collect-research.py` from the repository root. It uses the Python standard library, the normal HTTPS/proxy settings, bounded retries, and at most four concurrent requests. API responses are cached temporarily in the system temporary directory, outside the repository. Delete that temporary cache directory to force fresh retrieval. The API can update metadata and citation counts, so subsequent collections need not be byte-identical. The collector also updates this document’s collection timestamp, DOI count, deduplication counters, and topic-count table when writing the default catalog.

Fourteen topic queries are sent with `format=json`, `resultType=core`, `pageSize=300`, `sort=CITED desc`, and cursor pagination (up to three pages per query). Full query strings, examined-record counts, and topic quotas are included in `research-catalog.json` under `meta.queries`.

Pagination stops after a query has at least its quota plus 50 screened candidates, or reaches its three-page limit. This reserve allows cross-topic deduplication without unnecessary requests for more candidates. A collection fails rather than padding the catalog when a topic cannot supply its required number of unique eligible records.

## Inclusion, screening, and deduplication

- English-language PubMed records with first-publication dates from 1950-01-01 through the cutoff.
- Topic terms in title/abstract searches, followed by a topic-specific title match. Except for foundational learning/memory research, title/abstract text must indicate students, children, adolescents, youth, school populations, or an academic/college/university title.
- The grief/separation group additionally requires child, student, family-bereavement, parental-loss/incarceration, family-separation, or homesickness wording in the title.
- Automatically exclude indexed retractions, errata, editorials, comments, letters, and case reports. Exclude records with retraction relationships, animal-only MeSH indexing, animal titles, many unrelated medical specialties, and selected topic-specific mismatches. The exact regular expressions are in the script.
- Exclude older-adult therapy/treatment programs, dementia/Alzheimer and related neurodegenerative disease titles, surgical procedures, pharmacological interventions and medication trials, and specialty pharmacy training. Foundational adult laboratory learning experiments remain eligible. These title-based exclusions improve the student-support fit; they are not a full clinical appraisal.
- Require a numeric PubMed ID, title, author metadata, and a valid publication year.
- Allocate a fixed quota to each topic in query order. Deduplicate across PMID, normalized DOI, and normalized title before adding a record. Add secondary topic labels when the same selected PMID appears in another query’s screened candidates.

The final allocation skipped **19 cross-topic duplicate candidates** before selecting 1,000 records. Within-query duplicate records skipped: **0**. These are allocation counters, not the number of all potentially overlapping matches in the source database.

The selected set has **1,000 unique PMIDs** and **994 nonempty, unique DOIs**. All records have a source link, and none of the deliverable records contains an abstract or full text.

## Primary allocation

| Topic | Primary records | Records carrying the topic tag |
| --- | ---: | ---: |
| Learning & memory | 100 | 100 |
| Study strategies | 100 | 102 |
| Motivation & procrastination | 80 | 83 |
| Attention & digital distraction | 80 | 81 |
| Sleep & energy | 90 | 98 |
| Stress & emotions | 90 | 92 |
| Friends & belonging | 80 | 86 |
| Grief & family separation | 60 | 60 |
| Home & family | 70 | 76 |
| Learning & access | 70 | 72 |
| Money & basic needs | 60 | 60 |
| Time & planning | 50 | 53 |
| Future & expectations | 40 | 40 |
| School support | 30 | 32 |

The primary column sums to 1,000. Tag counts can sum to more than 1,000 because a paper may match several topic searches.

## Record and summary schemas

`src/research-catalog.json` contains `{meta, papers}`. `meta.topics` is an array of topic-label strings. `meta.topicCounts` maps each label to its actual number of tagged records. `meta.primaryTopicCounts` contains quota allocations.

Each paper has `id`, `title`, `authors`, `year`, `journal`, nullable `doi`, a canonical PubMed `url`, `topics`, `type`, `citedBy`, `status`, `source`, `queryId`, and `queryIds`. `queryId` is the primary allocating query; `queryIds` lists all screened source queries in which that selected record was observed. These IDs resolve to complete query provenance under `meta.queries`.

`type` is derived from source publication-type metadata, prioritizing meta-analysis, systematic review, review, randomized controlled trial, clinical trial, then journal article. It is not an evidence-quality rating. `citedBy` is the source citation count at collection, not a measure of correctness. `status: "Indexed"` means the bibliographic record was retrieved and screened automatically.

`src/research-summary.json` is a small startup payload containing `count`, `fetchedAt`, `cutoff`, `topics` (strings), `topicCounts` (label-to-count mapping), and `status`. The main catalog can be loaded only when the research screen is opened.

## Limits on use

The 1,000 full papers were not individually read, independently appraised, or synthesized into clinical guidance. Title/abstract screening improves relevance but cannot establish each study’s quality, population applicability, causal effects, or safety. The corpus includes foundational adult laboratory research and child, adolescent, and college research; it is not exclusively evidence from high school students.

PubMed coverage favors health and psychology and misses education research indexed elsewhere. English-language limits, selected queries, citation ranking, fixed quotas, and automated exclusions introduce selection biases. Citation ranking favors older, widely cited work. Retraction and publication-type checks depend on current source metadata. This is neither exhaustive nor an unbiased sample of all available evidence.

Do not present the catalog count as proof that the app works or as 1,000 studies supporting every recommendation. Advice cards should cite a smaller, explicitly checked evidence/guidance set and show their own limitations. Sensitive grief, mental health, family safety, and disability pathways require qualified professional review. Research links are for exploration; they do not diagnose a student or establish treatment recommendations.

## Validation performed

Validated 1,000 unique PMIDs, unique nonempty DOIs, unique normalized titles, required metadata fields, publication-year types, source-link formats, topic labels, and per-record query provenance. Representative titles were spot-checked, and screening was tightened to remove clear off-topic clinical, infant-motor-learning, dietary-learning, and unrelated parental-expectation results. This spot check is not a full content or quality review.

Regression checks exclude identified older-adult treatment and childhood surgery mismatches (PMIDs 15222820, 19139252, and 23692173), while preserving foundational student retrieval-practice experiments (PMIDs 16507066 and 18276894). Surgical/pharmacological title checks apply to every indexed record.

## Additional source spot check

Two source records per primary topic (28 records total) were independently retrieved again from the Europe PMC API. Their titles matched the catalog, and their abstracts were checked for broad topic relevance. The sample includes child and college populations, foundational laboratory research, observational associations, measurement research, and contextual attendance research. It does not establish that all findings apply to teenagers or that the papers test the app’s plans. Full texts and risk of bias were not assessed.

| Topic | Source records checked |
| --- | --- |
| Learning & memory | [PMID:16507066](https://pubmed.ncbi.nlm.nih.gov/16507066/); [PMID:18276894](https://pubmed.ncbi.nlm.nih.gov/18276894/) |
| Study strategies | [PMID:22352812](https://pubmed.ncbi.nlm.nih.gov/22352812/); [PMID:22083626](https://pubmed.ncbi.nlm.nih.gov/22083626/) |
| Motivation & procrastination | [PMID:21179384](https://pubmed.ncbi.nlm.nih.gov/21179384/); [PMID:29283599](https://pubmed.ncbi.nlm.nih.gov/29283599/) |
| Attention & digital distraction | [PMID:26132913](https://pubmed.ncbi.nlm.nih.gov/26132913/); [PMID:27294324](https://pubmed.ncbi.nlm.nih.gov/27294324/) |
| Sleep & energy | [PMID:29073412](https://pubmed.ncbi.nlm.nih.gov/29073412/); [PMID:15586779](https://pubmed.ncbi.nlm.nih.gov/15586779/) |
| Stress & emotions | [PMID:32805704](https://pubmed.ncbi.nlm.nih.gov/32805704/); [PMID:20123251](https://pubmed.ncbi.nlm.nih.gov/20123251/) |
| Friends & belonging | [PMID:8576833](https://pubmed.ncbi.nlm.nih.gov/8576833/); [PMID:11311098](https://pubmed.ncbi.nlm.nih.gov/11311098/) |
| Grief & family separation | [PMID:19411367](https://pubmed.ncbi.nlm.nih.gov/19411367/); [PMID:22229730](https://pubmed.ncbi.nlm.nih.gov/22229730/) |
| Home & family | [PMID:8013239](https://pubmed.ncbi.nlm.nih.gov/8013239/); [PMID:1446552](https://pubmed.ncbi.nlm.nih.gov/1446552/) |
| Learning & access | [PMID:10945922](https://pubmed.ncbi.nlm.nih.gov/10945922/); [PMID:21852486](https://pubmed.ncbi.nlm.nih.gov/21852486/) |
| Money & basic needs | [PMID:16317128](https://pubmed.ncbi.nlm.nih.gov/16317128/); [PMID:21644024](https://pubmed.ncbi.nlm.nih.gov/21644024/) |
| Time & planning | [PMID:17720288](https://pubmed.ncbi.nlm.nih.gov/17720288/); [PMID:12361443](https://pubmed.ncbi.nlm.nih.gov/12361443/) |
| Future & expectations | [PMID:15982107](https://pubmed.ncbi.nlm.nih.gov/15982107/); [PMID:37437728](https://pubmed.ncbi.nlm.nih.gov/37437728/) |
| School support | [PMID:24569086](https://pubmed.ncbi.nlm.nih.gov/24569086/); [PMID:19454625](https://pubmed.ncbi.nlm.nih.gov/19454625/) |
