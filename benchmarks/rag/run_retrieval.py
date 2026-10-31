"""python -m benchmarks.rag.run_retrieval --output .runtime/retrieval-run"""
from benchmarks.rag.runner import main
if __name__ == '__main__':
    raise SystemExit(main('retrieval'))
