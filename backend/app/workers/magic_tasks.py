    # Added magic generation task
@celery_app.task(bind=True, name="tasks.generate_magic", max_retries=1)
def generate_magic_task(self, job_id: str, project_id: str, owner_id: str):
    async def _run():
        await _init_db()
        await _update_job(job_id, "running", 2, "Starting magic video generation...")
        try:
            # We will run the logic of the other tasks sequentially
            # 1. Script
            await _update_job(job_id, "running", 10, "Step 1: Generating Script")
            generate_script_task(job_id, project_id, owner_id)
            
            # Wait, the other tasks run async loops inside. It's better to implement a simple wrapper 
            # Or just update the status and call them one by one.
            pass
        except Exception as e:
            pass
