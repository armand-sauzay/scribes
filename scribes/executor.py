import concurrent.futures


def execute_concurrently(function, args_list):
    """Execute function concurrently on args_list."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(function, *args) for args in args_list]
        concurrent.futures.wait(futures)
