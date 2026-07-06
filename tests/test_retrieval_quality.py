"""
test_retrieval_quality.py

Evaluates the Graph Retrieval Engine over 20 representative queries.
"""

import sys
from pathlib import Path
import networkx as nx

from graph.retrieval.retriever import GraphRetriever

# 20 representative evaluation queries mapping to our multi-paper corpus
EVAL_CASES = [
    {
        "query": "Who proposed the Transformer architecture?",
        "expected": ["transformer", "ashish_vaswani", "noam_shazeer", "niki_parmar"]
    },
    {
        "query": "Who is the lead author of BERT?",
        "expected": ["jacob_devlin", "bert", "google_ai_language"]
    },
    {
        "query": "Which datasets evaluate RoBERTa?",
        "expected": ["roberta", "glue", "squad", "mnli"]
    },
    {
        "query": "Which papers improve upon BERT?",
        "expected": ["roberta", "albert", "deberta"]
    },
    {
        "query": "What methods belong to Transformer?",
        "expected": ["self_attention", "multi_head_attention", "positional_encoding"]
    },
    {
        "query": "Explain the disentangled attention mechanism.",
        "expected": ["deberta", "disentangled_attention", "relative_position"]
    },
    {
        "query": "What is the key contribution of DeBERTa?",
        "expected": ["deberta", "disentangled_attention", "enhanced_mask_decoder"]
    },
    {
        "query": "What benchmarks are used to evaluate BERT?",
        "expected": ["glue", "squad"]
    },
    {
        "query": "Who authored the paper Attention Is All You Need?",
        "expected": ["ashish_vaswani", "niki_parmar", "łukasz_kaiser", "jakob_uszkoreit"]
    },
    {
        "query": "Which model achieves state-of-the-art on GLUE benchmark?",
        "expected": ["roberta", "deberta", "albert"]
    },
    {
        "query": "What is the parameter size reduction in ALBERT?",
        "expected": ["albert", "factorized_embedding_parameterization", "cross_layer_parameter_sharing"]
    },
    {
        "query": "What are the components of Multi-Head Attention?",
        "expected": ["scaled_dot_product_attention", "self_attention"]
    },
    {
        "query": "What vocabulary size is used in RoBERTa?",
        "expected": ["roberta", "byte_level_bpe"]
    },
    {
        "query": "Which institutions are affiliated with the authors of Attention Is All You Need?",
        "expected": ["google_brain", "google_research", "university_of_toronto"]
    },
    {
        "query": "Compare BERT and RoBERTa pre-training techniques.",
        "expected": ["bert", "roberta", "masked_language_modeling"]
    },
    {
        "query": "Is masking used in BERT?",
        "expected": ["bert", "masked_language_modeling"]
    },
    {
        "query": "What dataset is used for BERT pre-training?",
        "expected": ["wikipedia", "bookcorpus"]
    },
    {
        "query": "Which authors are affiliated with Google Brain?",
        "expected": ["ashish_vaswani", "noam_shazeer", "niki_parmar", "jakob_uszkoreit"]
    },
    {
        "query": "What is the optimizer used in Transformer training?",
        "expected": ["adam_optimizer", "learning_rate_scheduler"]
    },
    {
        "query": "Which conference published BERT?",
        "expected": ["naacl_2019", "google_ai_language"]
    }
]


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def evaluate_retrieval_quality():
    divider("RUNNING RETRIEVAL QUALITY EVALUATIONS")

    # Target path
    graph_path = Path("data/graphs/global_graph.graphml")
    if not graph_path.exists():
        graph_path = Path("data/graphs/attention.graphml")
        print(f"⚠️ Global graph not found. Falling back to: {graph_path}")

    if not graph_path.exists():
        print(f"❌ Error: Graph not found at {graph_path}. Please run pipeline first.")
        sys.exit(1)

    retriever = GraphRetriever(graph_path)

    report_lines = []
    report_lines.append("# GraphRAG Retrieval Quality Evaluation Report\n")
    report_lines.append(f"**Target Graph**: `{graph_path.name}`")
    report_lines.append(f"**Total Cases evaluated**: {len(EVAL_CASES)}\n")
    
    report_lines.append("| Query | Intent | Visited Nodes | Retained Nodes | Precision | Recall | Top-k Acc | Latency |")
    report_lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

    sum_precision = 0.0
    sum_recall = 0.0
    sum_latency = 0.0
    sum_top_k_acc = 0.0

    for idx, case in enumerate(EVAL_CASES, 1):
        query = case["query"]
        expected = case["expected"]
        
        # Run retrieval
        result = retriever.retrieve(query)
        stats = result.statistics
        
        # Calculate metrics
        intent = result.query_intent
        nodes_visited = stats.get("nodes_visited", 0)
        nodes_retained = stats.get("nodes_retained", 0)
        precision = stats.get("precision", 0.0)
        recall = stats.get("recall", 0.0)
        latency = stats.get("traversal_latency_ms", 0.0)

        # Check Top-k accuracy (at least one expected entity must be in the retrieved nodes)
        retrieved_ids = [n["id"] for n in result.nodes]
        top_k_hit = any(exp in retrieved_ids for exp in expected)
        top_k_val = 1.0 if top_k_hit else 0.0

        # Sum
        sum_precision += precision
        sum_recall += recall
        sum_latency += latency
        sum_top_k_acc += top_k_val
        top_val = top_k_val

        # Add row to report
        report_lines.append(
            f"| {query} | `{intent}` | {nodes_visited} | {nodes_retained} | "
            f"{precision:.4f} | {recall:.4f} | {top_val:.1f} | {latency:.2f} ms |"
        )

        print(f"[{idx}/20] Query: '{query}' -> Intent: {intent} | Hit: {top_k_hit} | Latency: {latency:.2f} ms")

    # Calculate overall averages
    avg_precision = sum_precision / len(EVAL_CASES)
    avg_recall = sum_recall / len(EVAL_CASES)
    avg_latency = sum_latency / len(EVAL_CASES)
    avg_top_k = sum_top_k_acc / len(EVAL_CASES)

    summary_section = f"""
## Summary Averages

- **Top-k Entity Accuracy (Target Hits)**: {avg_top_k * 100.0:.2f}%
- **Mean Search Precision**: {avg_precision:.4f}
- **Mean Search Recall (Seeds)**: {avg_recall:.4f}
- **Mean Traversal Latency**: {avg_latency:.2f} ms
"""
    report_lines.insert(3, summary_section)

    # Export report
    report_content = "\n".join(report_lines)
    report_output_path = Path("data/graphs/retrieval_evaluation_report.md")
    
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    divider("EVALUATION COMPLETED")
    print(f"Retrieval evaluation report generated at: {report_output_path.resolve()}")
    print(f"Overall Top-k Accuracy: {avg_top_k * 100.0:.2f}%")
    print(f"Mean Precision: {avg_precision:.4f}")
    print(f"Mean Recall: {avg_recall:.4f}")
    print(f"Mean Latency: {avg_latency:.2f} ms")


if __name__ == "__main__":
    evaluate_retrieval_quality()
