"""
Celery background tasks for all AI generation and video rendering.
Each task updates the GenerationJob document with progress and status.
"""
import asyncio
from datetime import datetime
from typing import Optional
from celery import Task
from loguru import logger
from app.workers.celery_app import celery_app
from app.core.config import settings


def run_async(coro):
    """Run an async coroutine from within a sync Celery task."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop and loop.is_running():
        return loop.create_task(coro)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


async def _update_job(job_id: str, status: str, progress: int,
                      message: str = "", error: str = "", result: dict = None):
    from app.models.job import GenerationJob, JobStatus
    job = await GenerationJob.get(job_id)
    if not job:
        return
    job.status = JobStatus(status)
    job.progress = progress
    if message:
        job.progress_message = message
    if error:
        job.error = error
    if result is not None:
        job.result = result
    if status == "running" and not job.started_at:
        job.started_at = datetime.utcnow()
    if status in ("success", "failed", "cancelled"):
        job.completed_at = datetime.utcnow()
    await job.save()


@celery_app.task(bind=True, name="tasks.generate_script", max_retries=2)
def generate_script_task(self, job_id: str, project_id: str, owner_id: str):
    async def _run():
        await _init_db()
        await _update_job(job_id, "running", 5, "Initializing script generation...")
        try:
            from app.models.project import Project
            from app.adapters.factory import get_llm_adapter

            project = await Project.get(project_id)
            if not project or str(project.owner_id) != owner_id:
                await _update_job(job_id, "failed", 0, error="Project not found")
                return

            await _update_job(job_id, "running", 20, "Generating script with AI...")

            adapter = get_llm_adapter()
            community = project.custom_community or project.community.value
            script = await adapter.generate_script(
                topic=project.topic,
                community=community,
                style=project.style.value,
                duration=project.duration,
                language=project.language,
            )

            await _update_job(job_id, "running", 70, "Saving script to project...")

            # Save scenes to DB
            from app.models.scene import Scene
            await Scene.find({"project_id": project_id}).delete()

            scenes_data = script.get("scenes", [])
            for i, s in enumerate(scenes_data):
                scene = Scene(
                    project_id=project_id,
                    owner_id=owner_id,
                    order=i,
                    narration=s.get("narration", ""),
                    visual_prompt=s.get("visual_prompt", ""),
                    duration=float(s.get("duration", 5.0)),
                    caption=s.get("caption"),
                )
                await scene.save()

            project.script = script
            project.video_title = script.get("video_title", project.title)
            project.video_description = script.get("video_description", "")
            project.hashtags = script.get("hashtags", [])
            project.updated_at = datetime.utcnow()
            await project.save()

            await _update_job(job_id, "success", 100, "Script generated!", result={"scene_count": len(scenes_data)})

        except Exception as e:
            logger.exception(f"Script generation failed for job {job_id}")
            await _update_job(job_id, "failed", 0, error=str(e))

    run_async(_run())


@celery_app.task(bind=True, name="tasks.generate_visuals", max_retries=2)
def generate_visuals_task(self, job_id: str, project_id: str, owner_id: str):
    async def _run():
        await _init_db()
        await _update_job(job_id, "running", 5, "Starting visual generation...")
        try:
            from app.models.project import Project
            from app.models.scene import Scene
            from app.models.asset import Asset, AssetType
            from app.adapters.factory import get_image_adapter
            from app.utils.storage import save_file

            project = await Project.get(project_id)
            if not project or str(project.owner_id) != owner_id:
                await _update_job(job_id, "failed", 0, error="Project not found")
                return

            scenes = await Scene.find({"project_id": project_id}).sort("+order").to_list()
            adapter = get_image_adapter()

            for i, scene in enumerate(scenes):
                scene.generation_status = "generating"
                await scene.save()

                try:
                    img_bytes, ext = await adapter.generate_image(
                        prompt=scene.visual_prompt,
                        style=project.style.value,
                        aspect_ratio=project.aspect_ratio.value,
                    )
                    file_path, file_url = await save_file(
                        img_bytes, owner_id, project_id, f"scene_{i}.{ext}", subdir="images"
                    )
                    scene.image_path = file_path
                    scene.image_url = file_url
                    scene.generation_status = "done"
                    await scene.save()

                    asset = Asset(
                        project_id=project_id,
                        scene_id=str(scene.id),
                        owner_id=owner_id,
                        asset_type=AssetType.IMAGE,
                        file_path=file_path,
                        file_url=file_url,
                        provider="openai" if project.script and not project.script.get("is_demo") else "demo",
                        prompt_used=scene.visual_prompt,
                    )
                    await asset.save()

                except Exception as e:
                    logger.error(f"Scene {i} image generation failed: {e}")
                    scene.generation_status = "failed"
                    scene.error_message = str(e)
                    await scene.save()

                pct = 10 + int((i + 1) / len(scenes) * 80)
                await _update_job(job_id, "running", pct, f"Generated visual {i+1}/{len(scenes)}")

            await _update_job(job_id, "success", 100, "All visuals generated!")

        except Exception as e:
            logger.exception(f"Visual generation failed: {job_id}")
            await _update_job(job_id, "failed", 0, error=str(e))

    run_async(_run())


@celery_app.task(bind=True, name="tasks.generate_tts", max_retries=2)
def generate_tts_task(self, job_id: str, project_id: str, owner_id: str):
    async def _run():
        await _init_db()
        await _update_job(job_id, "running", 5, "Starting narration generation...")
        try:
            from app.models.project import Project
            from app.models.scene import Scene
            from app.models.asset import Asset, AssetType
            from app.adapters.factory import get_tts_adapter
            from app.utils.storage import save_file

            project = await Project.get(project_id)
            if not project or str(project.owner_id) != owner_id:
                await _update_job(job_id, "failed", 0, error="Project not found")
                return

            scenes = await Scene.find({"project_id": project_id}).sort("+order").to_list()
            adapter = get_tts_adapter()

            for i, scene in enumerate(scenes):
                try:
                    audio_bytes = await adapter.generate_speech(
                        text=scene.narration,
                        voice_id=project.voice_id,
                        language=project.language,
                    )
                    file_path, file_url = await save_file(
                        audio_bytes, owner_id, project_id, f"scene_{i}_audio.wav", subdir="audio"
                    )
                    scene.audio_path = file_path
                    scene.audio_url = file_url
                    await scene.save()

                    asset = Asset(
                        project_id=project_id,
                        scene_id=str(scene.id),
                        owner_id=owner_id,
                        asset_type=AssetType.AUDIO,
                        file_path=file_path,
                        file_url=file_url,
                        provider="openai-tts" if project.voice_id else "demo",
                    )
                    await asset.save()

                except Exception as e:
                    logger.error(f"Scene {i} TTS failed: {e}")

                pct = 10 + int((i + 1) / len(scenes) * 80)
                await _update_job(job_id, "running", pct, f"Generated narration {i+1}/{len(scenes)}")

            await _update_job(job_id, "success", 100, "Narration generated!")

        except Exception as e:
            logger.exception(f"TTS generation failed: {job_id}")
            await _update_job(job_id, "failed", 0, error=str(e))

    run_async(_run())


@celery_app.task(bind=True, name="tasks.render_video", max_retries=1)
def render_video_task(self, job_id: str, project_id: str, owner_id: str):
    async def _run():
        await _init_db()
        await _update_job(job_id, "running", 2, "Starting video render...")
        try:
            from app.models.project import Project, ProjectStatus
            from app.models.scene import Scene
            from app.models.asset import Asset, AssetType
            from app.utils.ffmpeg_utils import assemble_video, generate_thumbnail, generate_srt
            from app.utils.storage import save_file, ensure_storage_dirs
            import tempfile, os, io

            ensure_storage_dirs()
            project = await Project.get(project_id)
            if not project or str(project.owner_id) != owner_id:
                await _update_job(job_id, "failed", 0, error="Project not found")
                return

            scenes = await Scene.find({"project_id": project_id}).sort("+order").to_list()
            if not scenes:
                await _update_job(job_id, "failed", 0, error="No scenes found")
                return

            project.status = ProjectStatus.GENERATING
            await project.save()

            # Build scene dicts for assembler
            scene_dicts = []
            combined_audio_chunks = []
            for scene in scenes:
                d = {
                    "image_path": scene.image_path,
                    "video_clip_path": scene.video_clip_path,
                    "audio_path": scene.audio_path,
                    "duration": scene.duration,
                    "narration": scene.narration,
                    "caption": scene.caption,
                }
                scene_dicts.append(d)

            # Concatenate per-scene audio into one file for the assembler
            combined_audio_path = None
            scene_audios = [s.audio_path for s in scenes if s.audio_path]
            if scene_audios and all(scene_audios):
                import subprocess
                tmp_dir = tempfile.mkdtemp(prefix="qoneqt_audio_")
                concat_file = os.path.join(tmp_dir, "audio_concat.txt")
                combined_audio_path = os.path.join(tmp_dir, "combined_audio.aac")
                with open(concat_file, "w") as cf:
                    for ap in scene_audios:
                        cf.write(f"file '{ap}'\n")
                result = subprocess.run(
                    [settings.FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
                     "-i", concat_file, "-c:a", "aac", combined_audio_path],
                    capture_output=True
                )
                if result.returncode != 0:
                    logger.warning(f"Audio concat failed: {result.stderr.decode()[:200]}")
                    combined_audio_path = None

            # Generate SRT
            srt_content = generate_srt(scene_dicts)
            srt_bytes, srt_url = None, None
            if project.enable_subtitles:
                import tempfile
                srt_tmp = tempfile.NamedTemporaryFile(suffix=".srt", delete=False, mode="w")
                srt_tmp.write(srt_content)
                srt_tmp.close()
                srt_file_path = srt_tmp.name
                with open(srt_file_path, "rb") as f:
                    srt_data = f.read()
                srt_path_stored, srt_url = await save_file(
                    srt_data, owner_id, project_id, "subtitles.srt", subdir="subtitles"
                )
                os.unlink(srt_file_path)

            # Render final video
            import tempfile
            video_tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            video_tmp.close()
            video_out_path = video_tmp.name

            progress_messages = []

            async def progress_cb(pct, msg):
                await _update_job(job_id, "running", pct, msg)

            success, error = await assemble_video(
                scenes=scene_dicts,
                output_path=video_out_path,
                aspect_ratio=project.aspect_ratio.value,
                audio_path=combined_audio_path if project.enable_narration else None,
                subtitle_path=srt_path_stored if project.enable_subtitles and srt_url else None,
                progress_callback=progress_cb,
            )

            if not success:
                project.status = ProjectStatus.FAILED
                project.error_message = error
                await project.save()
                await _update_job(job_id, "failed", 0, error=error)
                return

            # Save final video
            with open(video_out_path, "rb") as f:
                video_data = f.read()
            os.unlink(video_out_path)

            video_path, video_url = await save_file(
                video_data, owner_id, project_id, "final_video.mp4", subdir="videos"
            )

            asset = Asset(
                project_id=project_id,
                owner_id=owner_id,
                asset_type=AssetType.FINAL_VIDEO,
                file_path=video_path,
                file_url=video_url,
            )
            await asset.save()

            # Generate thumbnail
            thumb_tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            thumb_tmp.close()
            thumb_success = await generate_thumbnail(video_path, thumb_tmp.name)
            thumb_url = None
            if thumb_success:
                with open(thumb_tmp.name, "rb") as f:
                    thumb_data = f.read()
                _, thumb_url = await save_file(
                    thumb_data, owner_id, project_id, "thumbnail.jpg", subdir="thumbnails"
                )
                thumb_asset = Asset(
                    project_id=project_id,
                    owner_id=owner_id,
                    asset_type=AssetType.THUMBNAIL,
                    file_path=thumb_tmp.name,
                    file_url=thumb_url,
                )
                await thumb_asset.save()
            os.unlink(thumb_tmp.name)

            # Update project
            project.video_url = video_url
            project.video_path = video_path
            project.thumbnail_url = thumb_url
            project.subtitle_url = srt_url
            project.status = ProjectStatus.READY
            project.error_message = None
            project.updated_at = datetime.utcnow()
            await project.save()

            await _update_job(job_id, "success", 100, "Video rendered successfully!",
                              result={"video_url": video_url, "thumbnail_url": thumb_url})

        except Exception as e:
            logger.exception(f"Video render failed: {job_id}")
            try:
                from app.models.project import Project, ProjectStatus
                proj = await Project.get(project_id)
                if proj:
                    proj.status = ProjectStatus.FAILED
                    proj.error_message = str(e)
                    await proj.save()
            except Exception:
                pass
            await _update_job(job_id, "failed", 0, error=str(e))

    run_async(_run())


async def _init_db():
    """Initialize MongoDB connection for a worker process.

    In eager/demo mode (no Redis), Celery tasks run synchronously inside the
    FastAPI process. The DB is already initialized by FastAPI's lifespan event.
    Re-calling connect_db() would create a NEW isolated AsyncMongoMockClient()
    which is a completely separate in-memory DB — any jobs saved there are
    invisible to the FastAPI process, causing persistent "Job not found" errors.

    We check whether Beanie is already initialized on the model and skip
    re-initialization when it is.
    """
    try:
        from app.models.job import GenerationJob
        # get_motor_collection() raises if Beanie hasn't been initialized yet
        col = GenerationJob.get_motor_collection()
        if col is not None:
            return  # Already initialized — reuse existing DB connection
    except Exception:
        pass  # Not yet initialized — fall through and connect
    from app.core.database import connect_db
    await connect_db()

