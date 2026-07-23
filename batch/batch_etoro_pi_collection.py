"""
Thin CLI wrapper that calls the shared eToro Pro Investor collection pipeline.
"""

from etoro.pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline()
