# Repository Overview

This document captures the high-level layout of the `awesome-machine-learning` repository and highlights the most useful entry points when you are exploring the project for the first time.

## Core Curation Lists
- **`README.md`** – Main awesome list grouped by programming language with sections for general-purpose libraries, domain-specific tooling, and a short "Tools" appendix.
- **`books.md`** – Catalog of free or open-access books across machine learning, deep learning, NLP, statistics, and mathematics.
- **`courses.md`** – Collection of online courses with a focus on open or low-cost learning resources.
- **`blogs.md`** – Aggregated blogs and newsletters covering applied machine learning topics.
- **`events.md`** – Professional conferences and meetups relevant to data science and machine learning practitioners.
- **`meetups.md`** – Free-to-attend meetups and local community gatherings.
- **`ml-curriculum.md`** – Suggested study roadmap that pulls together readings, talks, and project ideas.
- **`ML-DL Projects 2022`** – Quick-reference idea list for hands-on projects spanning classical ML and deep learning domains.

## Supporting Utilities
- **`scripts/pull_R_packages.py`** – Helper script that scrapes the CRAN Machine Learning task view and formats package entries in Markdown so they can be copied into the main list. Requires `pyquery` and relies on Python 2-style `urllib` usage.
- **`scripts/requirements.txt`** – Python dependencies needed for the scraping utility above.
- **`Squirrel`** – Note pointing to the [`merantix-momentum/squirrel-core`](https://github.com/merantix-momentum/squirrel-core) project, indicating it should be considered for inclusion.

## Contribution Expectations
- Follow the Awesome List guidelines when proposing additions (consistent Markdown bullet formatting, short descriptions, and active projects).
- Deprecate or remove entries that are no longer maintained or are explicitly archived.
- Prefer resources that are freely accessible or provide substantial open-access content when possible.

## Getting Started Tips
1. Skim `README.md` to understand the existing taxonomy before proposing structural changes.
2. Use the supporting markdown files for deeper dives into specific resource categories (books, courses, blogs, etc.).
3. Run `scripts/pull_R_packages.py` if you need to refresh the R package list, ensuring the requirements from `scripts/requirements.txt` are installed in a compatible Python environment.
4. Keep an eye on notes like `Squirrel` that flag pending additions so the list stays current.

