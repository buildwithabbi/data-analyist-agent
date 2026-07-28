from concurrent.futures import ThreadPoolExecutor
class Scheduler:
    def run(self, tasks, handler, *, parallel=False):
        if parallel:
            with ThreadPoolExecutor(max_workers=len(tasks) or 1) as pool: return list(pool.map(handler, tasks))
        return [handler(task) for task in tasks]
