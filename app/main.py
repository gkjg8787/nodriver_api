import os
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from .models import DownloadRequest, DownloadResponse, ErrorDetail
from .downloader import dl_with_nodriver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    lock_file = "/tmp/.X99-lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)
        logger.info(f"Removed stale lock file: {lock_file}")
    # 仮想ディスプレイを起動
    xvfb_process = await asyncio.create_subprocess_exec(
        "Xvfb", ":99", "-ac", "-screen", "0", "1920x1080x24"
    )
    yield
    if xvfb_process and xvfb_process.returncode is None:
        try:
            xvfb_process.kill()
            await xvfb_process.wait()
        except Exception as e:
            logger.error(f"Error stopping Xvfb: {e}")
    else:
        logger.warning(
            f"Xvfb process was not started or already terminated. returncode: {xvfb_process.returncode}"
        )


app = FastAPI(lifespan=lifespan)


@app.post("/download", response_model=DownloadResponse)
async def download_html(request: DownloadRequest):
    success, result, cookies = await dl_with_nodriver(request)

    if success:
        return DownloadResponse(result=result, cookies=cookies)
    else:
        error_details = ErrorDetail(
            error_msg=str(result), error_type=type(result).__name__
        )
        return DownloadResponse(error=error_details)
