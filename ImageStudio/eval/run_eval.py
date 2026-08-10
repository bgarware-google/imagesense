# ==============================================================================
# Automated Evaluation & Regression Detection Test Runner
# ==============================================================================
import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eval.eval_judge import MultimodalQualityJudge
from app import multi_agent_orchestrator, telemetry_logger

DATASET_PATH = os.path.join(os.path.dirname(__file__), "eval_dataset.json")

def run_evaluation_suite():
    """
    Executes automated evaluation across the benchmark dataset,
    scores candidates with LLM-as-a-Judge, and checks for quality regressions.
    """
    print("=================================================================")
    print("🚀 Starting ImageSense LLM Ops Quality & Regression Eval Suite")
    print("=================================================================\n")

    if not os.path.exists(DATASET_PATH):
        print(f"Error: Eval dataset not found at '{DATASET_PATH}'")
        return False

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)

    judge = MultimodalQualityJudge()
    results = []
    regression_detected = False

    for case in eval_cases:
        eval_id = case["eval_id"]
        category = case["category"]
        prompt = case["prompt"]
        min_faith = case.get("minimum_faithfulness", 3.5)
        min_rel = case.get("minimum_relevance", 3.5)

        print(f"--> [Case {eval_id}] ({category}) Evaluating prompt: '{prompt[:45]}...'")
        start_time = time.time()
        images, trace = multi_agent_orchestrator.process(prompt, user_id=f"eval_runner_{eval_id}")
        latency_ms = (time.time() - start_time) * 1000.0

        best_img = images[0] if images and images[0] is not None else None
        
        # Run Judge Evaluation
        scores = judge.evaluate(prompt, best_img, case.get("expected_elements", []))
        faithfulness = scores.get("faithfulness", 4.0)
        relevance = scores.get("relevance", 4.0)
        coherence = scores.get("coherence", 4.0)

        is_passed = (faithfulness >= min_faith) and (relevance >= min_rel)
        if not is_passed:
            regression_detected = True

        status_str = "✅ PASSED" if is_passed else "❌ REGRESSION"
        print(f"    Scores: Faithfulness={faithfulness} (min {min_faith}), Relevance={relevance} (min {min_rel}), Coherence={coherence} -> {status_str}")

        # Stream Eval Telemetry into BigQuery
        telemetry_logger.log_event({
            "request_id": f"eval_{eval_id}_{int(time.time())}",
            "user_id": "eval_runner",
            "feature": f"eval_{category}",
            "model_name": "gemini-2.5-flash-judge",
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": 256,
            "total_tokens": len(prompt.split()) + 256,
            "images_count": len([img for img in images if img is not None]),
            "latency_ms": latency_ms,
            "estimated_cost_usd": 0.005,
            "action_taken": "EVAL_JUDGE_SCORED",
            "similarity_score": faithfulness / 5.0,
            "pii_redacted": False,
            "vision_safe": True,
            "status": "PASSED" if is_passed else "REGRESSION"
        })

        results.append({
            "eval_id": eval_id,
            "category": category,
            "faithfulness": faithfulness,
            "relevance": relevance,
            "coherence": coherence,
            "passed": is_passed
        })

    # Summary Table
    print("\n=================================================================")
    print("📊 Evaluation Summary Report")
    print("=================================================================")
    print(f"{'Case ID':<10} {'Category':<25} {'Faithfulness':<15} {'Relevance':<12} {'Coherence':<12} {'Status'}")
    print("-" * 80)
    for r in results:
        status_sym = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{r['eval_id']:<10} {r['category']:<25} {r['faithfulness']:<15.1f} {r['relevance']:<12.1f} {r['coherence']:<12.1f} {status_sym}")

    avg_faith = sum(r["faithfulness"] for r in results) / len(results)
    avg_rel = sum(r["relevance"] for r in results) / len(results)
    avg_coh = sum(r["coherence"] for r in results) / len(results)

    print("-" * 80)
    print(f"Overall Average: Faithfulness={avg_faith:.2f}/5.0 | Relevance={avg_rel:.2f}/5.0 | Coherence={avg_coh:.2f}/5.0")
    
    if regression_detected:
        print("\n⚠️ WARNING: Quality regression detected in one or more evaluation benchmarks!")
    else:
        print("\n🎉 SUCCESS: All evaluation benchmarks passed quality gates!")

    return not regression_detected

if __name__ == "__main__":
    success = run_evaluation_suite()
    sys.exit(0 if success else 1)
