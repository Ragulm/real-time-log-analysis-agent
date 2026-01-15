import asyncio
import aiofiles
import os

class LogCollector:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path

    async def tail_log(self):
        """
        Generator that yields new lines from the log file as they differ.
        Simulates 'tail -f'.
        """
        print(f"Agent 1 (Collector): Watching {self.log_file_path}...")
        
        # Wait for file to exist
        while not os.path.exists(self.log_file_path):
            await asyncio.sleep(1)

        async with aiofiles.open(self.log_file_path, mode='r') as f:
            # Move pointer to end of file to start reading only NEW logs
            await f.seek(0, 2)
            
            while True:
                line = await f.readline()
                if not line:
                    await asyncio.sleep(0.1) # efficient polling
                    continue
                
                yield line.strip()
