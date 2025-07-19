import threading
import time


class SharedRateLimiter:
    """
    A thread-safe rate limiter to coordinate API calls between multiple threads.
    """

    def __init__(self, default_delay: float = 0.0):
        """
        Initialise the shared rate limiter.

        Args:
            default_delay (float): Default delay between requests in seconds.
        """
        self.lock = threading.Lock()
        self.last_request_time = 0.0
        self.rate_limited_until = 0.0
        self.default_delay = default_delay

    def set_rate_limited(self, duration: float) -> None:
        """
        Set the rate limit duration that all threads must respect.

        Args:
            duration (float): How long to wait in seconds.
        """
        with self.lock:
            rate_limit_until = time.time() + duration
            # Only extend the rate limit period, don't shorten it.
            if rate_limit_until > self.rate_limited_until:
                self.rate_limited_until = rate_limit_until
                print(f"Rate limit detected - all threads will pause for {duration:.2f} seconds")

    def wait_if_needed(self) -> None:
        """
        Wait if necessary to respect rate limits and default delays.
        This should be called before making any API request.
        """
        with self.lock:
            current_time = time.time()

            # Check if still in a rate limit period.
            if current_time < self.rate_limited_until:
                wait_time = self.rate_limited_until - current_time
                print(f"Coordinating with other threads - waiting {wait_time:.2f} seconds for rate limit")
            else:
                # Apply default delay since last request.
                time_since_last = current_time - self.last_request_time
                if time_since_last < self.default_delay:
                    wait_time = self.default_delay - time_since_last
                else:
                    wait_time = 0

            if wait_time > 0:
                # Release lock while sleeping
                self.lock.release()
                time.sleep(wait_time)
                self.lock.acquire()
            
            self.last_request_time = time.time()
