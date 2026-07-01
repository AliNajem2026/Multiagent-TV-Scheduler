from concurrent.futures import ThreadPoolExecutor
from .agents import AudienceAgent, ContentAgent, SchedulingAgent, OptimizationAgent


class SchedulerWorkflow: # orchestrates the entire scheduling process
    def __init__(self, callback=None):
        self.callback = callback or (lambda _: None)

    def run(self, day):
        with ThreadPoolExecutor(max_workers=2) as executor:
            self.callback("AudienceAgent: Analyzing audience patterns...")
            self.callback("ContentAgent: Fetching live sports events...")
            audience_future = executor.submit(AudienceAgent().run, day)
            content_future = executor.submit(ContentAgent().run, day)
            audience = audience_future.result()
            content = content_future.result()

        self.callback("SchedulingAgent: Building schedule...")
        schedule = SchedulingAgent().run(audience, content)

        self.callback("OptimizationAgent: Optimizing for audience retention...")
        optimized = OptimizationAgent().run(schedule)

        self.callback("Complete!")
        return optimized
