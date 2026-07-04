# GraphRAG Retrieval Quality Evaluation Report

**Target Graph**: `global_graph.graphml`
**Total Cases evaluated**: 20


## Summary Averages

- **Top-k Entity Accuracy (Target Hits)**: 35.00%
- **Mean Search Precision**: 0.5300
- **Mean Search Recall (Seeds)**: 0.3761
- **Mean Traversal Latency**: 78.77 ms

| Query | Intent | Visited Nodes | Retained Nodes | Precision | Recall | Top-k Acc | Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Who proposed the Transformer architecture? | `METHOD_QUERY` | 15 | 8 | 0.5333 | 0.2500 | 0.0 | 45.03 ms |
| Who is the lead author of BERT? | `AUTHOR_QUERY` | 27 | 1 | 0.0370 | 0.0370 | 0.0 | 15.70 ms |
| Which datasets evaluate RoBERTa? | `DATASET_QUERY` | 53 | 1 | 0.0189 | 0.0189 | 0.0 | 39.90 ms |
| Which papers improve upon BERT? | `GENERAL_QUERY` | 15 | 15 | 1.0000 | 1.0000 | 0.0 | 191.16 ms |
| What methods belong to Transformer? | `METHOD_QUERY` | 15 | 12 | 0.8000 | 0.3333 | 0.0 | 49.66 ms |
| Explain the disentangled attention mechanism. | `EXPLANATION_QUERY` | 20 | 15 | 0.7500 | 0.5556 | 0.0 | 74.65 ms |
| What is the key contribution of DeBERTa? | `EXPLANATION_QUERY` | 20 | 20 | 1.0000 | 1.0000 | 1.0 | 78.90 ms |
| What benchmarks are used to evaluate BERT? | `BENCHMARK_QUERY` | 29 | 1 | 0.0345 | 0.0345 | 0.0 | 44.59 ms |
| Who authored the paper Attention Is All You Need? | `AUTHOR_QUERY` | 10 | 9 | 0.9000 | 0.5000 | 1.0 | 14.29 ms |
| Which model achieves state-of-the-art on GLUE benchmark? | `BENCHMARK_QUERY` | 26 | 1 | 0.0385 | 0.0385 | 0.0 | 52.67 ms |
| What is the parameter size reduction in ALBERT? | `EXPLANATION_QUERY` | 20 | 17 | 0.8500 | 0.5000 | 1.0 | 107.02 ms |
| What are the components of Multi-Head Attention? | `METHOD_QUERY` | 15 | 9 | 0.6000 | 0.5000 | 1.0 | 87.36 ms |
| What vocabulary size is used in RoBERTa? | `GENERAL_QUERY` | 15 | 13 | 0.8667 | 0.3333 | 1.0 | 147.09 ms |
| Which institutions are affiliated with the authors of Attention Is All You Need? | `INSTITUTION_QUERY` | 32 | 1 | 0.0312 | 0.0312 | 0.0 | 18.63 ms |
| Compare BERT and RoBERTa pre-training techniques. | `COMPARISON_QUERY` | 13 | 13 | 1.0000 | 1.0000 | 1.0 | 107.99 ms |
| Is masking used in BERT? | `GENERAL_QUERY` | 15 | 11 | 0.7333 | 0.2000 | 1.0 | 118.44 ms |
| What dataset is used for BERT pre-training? | `DATASET_QUERY` | 56 | 1 | 0.0179 | 0.0179 | 0.0 | 40.42 ms |
| Which authors are affiliated with Google Brain? | `INSTITUTION_QUERY` | 26 | 1 | 0.0385 | 0.0385 | 0.0 | 17.83 ms |
| What is the optimizer used in Transformer training? | `EXPLANATION_QUERY` | 20 | 7 | 0.3500 | 0.1333 | 0.0 | 126.24 ms |
| Which conference published BERT? | `GENERAL_QUERY` | 15 | 15 | 1.0000 | 1.0000 | 0.0 | 197.80 ms |