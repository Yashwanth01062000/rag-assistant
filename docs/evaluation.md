# Evaluation

The project contains a 70-question evaluation set: 20 simple, 20 retrieval, 10 comparative, 10 multi-hop and 10 unanswerable questions.

`evaluation/run_eval.py` produces `results.csv` and `scores.csv`.

Before final submission, verify every expected section/page against the exact supplied PDF version. The CSV intentionally labels the rows as needing source verification so the benchmark does not silently assume printed page labels match PDF page indexes.
