"""
Thin CLI wrapper that calls the shared eToro Pro Investor collection pipeline.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etoro.pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline()
