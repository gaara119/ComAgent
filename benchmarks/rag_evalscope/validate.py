"""Validate real pinned EvalScope configs without sending any model request."""
from importlib.metadata import version
import argparse
import json
import os
from pathlib import Path

from benchmarks.rag_evalscope.bridge import VERSION
from benchmarks.rag_evalscope.run import ragas_config, local_caches


def mteb_config(data_path, model_path):
    return {'eval_backend': 'RAGEval', 'eval_config': {
        'tool': 'MTEB', 'models': [{'model_name_or_path': str(model_path),
            'max_seq_length': 512, 'encode_kwargs': {'batch_size': 2}}],
        'eval': {'custom_tasks': [{'name': 'ComAgentReviewedDevRetrieval',
                    'data_path': str(data_path), 'eval_splits': ['dev']}],
                 'output_folder': 'outputs/mteb', 'top_k': 5}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    local_caches(args.output.resolve().parent / 'evalscope-cache')
    from evalscope.backend.rag_eval.ragas.arguments import RAGASToolConfig
    from evalscope.backend.rag_eval.mteb.arguments import MTEBToolConfig
    # Config classes alone do not import the real RAGAS execution dependencies.
    # Validate the same entrypoint and constructors as the official backend,
    # without invoking a model or producing evaluation samples.
    import ragas as ragas_runtime
    from evalscope.backend.rag_eval.ragas.task_template import _build_llm, _build_embeddings, import_metric
    from evalscope.backend.rag_eval.ragas.tasks import generate_testset
    from ragas.run_config import RunConfig
    if version('evalscope') != VERSION:
        raise ValueError('Pinned official EvalScope required')
    ragas = ragas_config('actual-rag-input.json', 'http://127.0.0.1:1/v1')
    mteb = mteb_config('REQUIRES_REVIEWED_QRELS', 'REQUIRES_FULL_SENTENCE_TRANSFORMER_MODEL')
    validated_ragas = RAGASToolConfig.model_validate(ragas['eval_config'])
    MTEBToolConfig.model_validate(mteb['eval_config'])
    llm = _build_llm(validated_ragas.eval.critic_llm)
    _build_embeddings(validated_ragas.eval.embeddings)
    metric = import_metric('faithfulness')
    metric.llm = llm
    metric.init(RunConfig(timeout=60, max_retries=0))
    value = {'status': 'official_config_validation_passed',
             'versions': {name: version(name) for name in ('evalscope', 'ragas', 'mteb', 'openai', 'instructor', 'langchain-community')},
             'checks': ['RAGASToolConfig', 'MTEBToolConfig', 'ragas_runtime_import',
                        'official_backend_task_import', 'official_llm_and_embedding_client_constructors',
                        'official_faithfulness_metric_init'], 'new_model_calls': 0,
             'MTEB_execution': 'not_run_missing_reviewed_qrels_and_matching_frozen_retrieval_protocol',
             'RAGAS_config': ragas, 'MTEB_config_template_not_results': mteb}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps(value['versions']))


if __name__ == '__main__':
    main()
