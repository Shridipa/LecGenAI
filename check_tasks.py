from transformers import pipelines
print("Available tasks:", list(pipelines.PIPELINE_REGISTRY.get_supported_tasks()))
