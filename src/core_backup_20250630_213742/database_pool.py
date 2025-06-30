"""
Database Connection Pool
Manages efficient database connections with pooling
"""
import sqlite3
from queue import Queue
from contextlib import contextmanager
from threading import Lock
import time

class DatabasePool:
    """SQLite connection pool for improved performance"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = Queue(maxsize=pool_size)
        self._all_connections = []
        self._lock = Lock()
        
        # Initialize pool
        for _ in range(pool_size):
            conn = self._create_connection()
            self._pool.put(conn)
            self._all_connections.append(conn)
    
    def _create_connection(self):
        """Create optimized connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = None
        try:
            conn = self._pool.get(timeout=5)
            yield conn
        finally:
            if conn:
                self._pool.put(conn)
    
    def close_all(self):
        """Close all connections"""
        with self._lock:
            while not self._pool.empty():
                conn = self._pool.get()
                conn.close()
            self._all_connections.clear()

# Global database pool
db_pool = DatabasePool("/opt/rtx-trading/data/algoslayer_main.db", pool_size=10)
