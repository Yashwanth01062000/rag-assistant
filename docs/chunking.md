# Chunking strategy

The baseline uses section-aware chunks rather than arbitrary PDF character slices.

- Target: 450 words
- Overlap: 80 words
- Heading inheritance: chapter/section/subsection metadata is carried into each chunk
- Page metadata is retained
- Small chunks are removed

For the final report, compare at least 300/50, 450/80 and 650/100 word/overlap configurations using the evaluation dataset.
