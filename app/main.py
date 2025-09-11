from fastapi import FastAPI
from .models import DownloadRequest, DownloadResponse, ErrorDetail
from .downloader import dl_with_nodriver

app = FastAPI()

@app.post("/download", response_model=DownloadResponse)
async def download_html(request: DownloadRequest):
    success, result = await dl_with_nodriver(request)

    if success:
        return DownloadResponse(result=result)
    else:
        error_details = ErrorDetail(
            error_msg=str(result),
            error_type=type(result).__name__
        )
        return DownloadResponse(error=error_details)
