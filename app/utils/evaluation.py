from typing import List, Dict, Any, Optional
import pandas as pd
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_relevancy,
    context_recall
)
from ragas.metrics.critique import harmfulness
from datasets import Dataset

class RAGEvaluator:
    """
    Evaluator for RAG pipeline using RAGAS metrics.
    """
    
    def __init__(self):
        """Initialize the RAG evaluator."""
        # Initialize RAGAS metrics
        self.metrics = {
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "context_relevancy": context_relevancy,
            "context_recall": context_recall,
            "harmfulness": harmfulness
        }
    
    def prepare_evaluation_data(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> Dataset:
        """
        Prepare evaluation data for RAGAS.
        
        Args:
            questions: List of questions.
            answers: List of generated answers.
            contexts: List of contexts used for each answer.
            ground_truths: Optional list of ground truth answers.
            
        Returns:
            Dataset: RAGAS-compatible dataset.
        """
        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
        }
        
        if ground_truths:
            data["ground_truths"] = [[gt] for gt in ground_truths]
        
        # Convert to HuggingFace Dataset
        return Dataset.from_dict(data)
    
    def evaluate(
        self,
        dataset: Dataset,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Evaluate the RAG pipeline using RAGAS metrics.
        
        Args:
            dataset: RAGAS-compatible dataset.
            metrics: List of metrics to evaluate. If None, all metrics are used.
            
        Returns:
            Dict[str, float]: Evaluation results.
        """
        if metrics is None:
            metrics = list(self.metrics.keys())
        
        # Filter metrics
        selected_metrics = [self.metrics[m] for m in metrics if m in self.metrics]
        
        # Run evaluation
        try:
            result = dataset.map(lambda x: {})  # Create a copy
            
            for metric in selected_metrics:
                result = metric.compute(result)
            
            # Extract scores
            scores = {}
            for metric in metrics:
                if metric in result.column_names:
                    scores[metric] = result[metric].mean()
            
            return scores
        
        except Exception as e:
            print(f"Error during evaluation: {e}")
            return {}
    
    def evaluate_from_qa_pairs(
        self,
        qa_pairs: List[Dict[str, Any]],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Evaluate the RAG pipeline using QA pairs.
        
        Args:
            qa_pairs: List of QA pairs with questions, answers, contexts, and optional ground truths.
            metrics: List of metrics to evaluate. If None, all metrics are used.
            
        Returns:
            Dict[str, float]: Evaluation results.
        """
        questions = []
        answers = []
        contexts = []
        ground_truths = []
        has_ground_truths = False
        
        for pair in qa_pairs:
            questions.append(pair["question"])
            answers.append(pair["answer"])
            contexts.append(pair["contexts"])
            
            if "ground_truth" in pair:
                has_ground_truths = True
                ground_truths.append(pair["ground_truth"])
        
        # Prepare dataset
        if has_ground_truths:
            dataset = self.prepare_evaluation_data(questions, answers, contexts, ground_truths)
        else:
            dataset = self.prepare_evaluation_data(questions, answers, contexts)
        
        # Run evaluation
        return self.evaluate(dataset, metrics)
    
    def generate_evaluation_report(
        self,
        evaluation_results: Dict[str, float]
    ) -> str:
        """
        Generate a human-readable evaluation report.
        
        Args:
            evaluation_results: Evaluation results from evaluate().
            
        Returns:
            str: Human-readable evaluation report.
        """
        report = "# RAG Evaluation Report\n\n"
        
        # Add metrics
        report += "## Metrics\n\n"
        report += "| Metric | Score |\n"
        report += "|--------|-------|\n"
        
        for metric, score in evaluation_results.items():
            report += f"| {metric} | {score:.4f} |\n"
        
        # Add interpretations
        report += "\n## Interpretation\n\n"
        
        # Faithfulness
        if "faithfulness" in evaluation_results:
            score = evaluation_results["faithfulness"]
            if score >= 0.8:
                report += "- **Faithfulness**: Excellent. The answers are highly faithful to the provided context.\n"
            elif score >= 0.6:
                report += "- **Faithfulness**: Good. The answers are mostly faithful to the provided context.\n"
            else:
                report += "- **Faithfulness**: Needs improvement. The answers contain hallucinations or information not in the context.\n"
        
        # Answer relevancy
        if "answer_relevancy" in evaluation_results:
            score = evaluation_results["answer_relevancy"]
            if score >= 0.8:
                report += "- **Answer Relevancy**: Excellent. The answers are highly relevant to the questions.\n"
            elif score >= 0.6:
                report += "- **Answer Relevancy**: Good. The answers are mostly relevant to the questions.\n"
            else:
                report += "- **Answer Relevancy**: Needs improvement. The answers are not sufficiently relevant to the questions.\n"
        
        # Context relevancy
        if "context_relevancy" in evaluation_results:
            score = evaluation_results["context_relevancy"]
            if score >= 0.8:
                report += "- **Context Relevancy**: Excellent. The retrieved contexts are highly relevant to the questions.\n"
            elif score >= 0.6:
                report += "- **Context Relevancy**: Good. The retrieved contexts are mostly relevant to the questions.\n"
            else:
                report += "- **Context Relevancy**: Needs improvement. The retrieved contexts are not sufficiently relevant to the questions.\n"
        
        # Context recall
        if "context_recall" in evaluation_results:
            score = evaluation_results["context_recall"]
            if score >= 0.8:
                report += "- **Context Recall**: Excellent. The retrieved contexts contain most of the information needed to answer the questions.\n"
            elif score >= 0.6:
                report += "- **Context Recall**: Good. The retrieved contexts contain a good amount of the information needed to answer the questions.\n"
            else:
                report += "- **Context Recall**: Needs improvement. The retrieved contexts are missing important information needed to answer the questions.\n"
        
        # Harmfulness
        if "harmfulness" in evaluation_results:
            score = evaluation_results["harmfulness"]
            if score <= 0.1:
                report += "- **Harmfulness**: Excellent. The answers are not harmful.\n"
            elif score <= 0.3:
                report += "- **Harmfulness**: Good. The answers are mostly not harmful.\n"
            else:
                report += "- **Harmfulness**: Needs improvement. The answers contain potentially harmful content.\n"
        
        return report
