from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List

def run_threaded_operation(operation: Callable, items: List, max_workers: int = 10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(operation, items))