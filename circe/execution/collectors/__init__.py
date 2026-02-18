"""Built-in collectors.

These collectors are referenced by entry points so they can be loaded lazily.
They must not import optional dependencies at module import time.
"""

__all__ = ["polars"]

