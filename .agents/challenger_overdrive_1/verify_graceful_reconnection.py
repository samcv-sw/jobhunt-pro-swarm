import os
import sys
import asyncio
import logging
from unittest.mock import AsyncMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Configure logging to capture output
log_stream = []
class CaptureHandler(logging.Handler):
    def emit(self, record):
        log_stream.append(self.format(record))

logger = logging.getLogger("backend.sync_worker")
logger.setLevel(logging.INFO)
handler = CaptureHandler()
formatter = logging.Formatter('%(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Custom exception to terminate the infinite worker loop gracefully
class WorkerLoopExit(BaseException):
    pass

async def test_worker_reconnection():
    import asyncpg
    from backend.sync_worker import sync_outbox_to_cloud
    import backend.sync_worker
    
    # Force a remote pg url so it attempts to connect
    backend.sync_worker.REMOTE_PG_URL = "postgresql://mockremotehost:5432/mockdb"
    
    # Mock asyncpg.connect to raise a connection error
    mock_connect = AsyncMock(side_effect=asyncpg.PostgresConnectionError("Connection refused mock error"))
    asyncpg.connect = mock_connect
    
    # Mock asyncio.sleep to exit the loop after the first cycle
    async def mock_sleep(seconds):
        log_stream.append(f"INFO: asyncio.sleep called with {seconds}s")
        raise WorkerLoopExit()
        
    asyncio.sleep = mock_sleep
    
    print("Executing database sync worker with simulated connection refusal...")
    try:
        await sync_outbox_to_cloud()
    except WorkerLoopExit:
        print("Worker loop exited cleanly via mock_sleep exception.")
    except Exception as e:
        print(f"FAILED: Worker crashed with unexpected exception: {e}")
        sys.exit(1)
        
    # Check if the connection error warning was logged
    warning_logged = False
    sleep_logged = False
    
    print("\nCaptured Worker Logs:")
    for log in log_stream:
        print(f"  {log}")
        if "Remote DB unreachable" in log and "Connection refused mock error" in log:
            warning_logged = True
        if "asyncio.sleep called with 30" in log:
            sleep_logged = True
            
    if warning_logged and sleep_logged:
        print("\nSUCCESS: Connection errors are logged without crash, and the worker gracefully retries after sleeping.")
        sys.exit(0)
    else:
        print("\nFAILED: Worker did not log connection errors or retry as expected.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_worker_reconnection())
