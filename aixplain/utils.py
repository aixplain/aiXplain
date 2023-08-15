import time


class Timer:
    """Context manager for timing code execution."""

    def __enter__(self):
        """Start the timer."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and print the elapsed time."""
        elapsed_time = time.perf_counter() - self.start_time
        print(f"Elapsed time: {elapsed_time:.4f} seconds")

    @property
    def elapsed_time_formatted(self):
        return f"{self.elapsed_time:.4f} secs"
