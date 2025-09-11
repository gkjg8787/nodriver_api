from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ErrorDetail(BaseModel):
    error_msg: str = ""
    error_type: str = ""

class DownloadRequest(BaseModel):
    url: str
    page_load_timeout: Optional[int] = None
    tag_wait_timeout: Optional[int] = None
    cookie_dict_list: Optional[List[Dict[str, Any]]] = None
    wait_css_selector: Optional[str] = None
    page_wait_time: Optional[float] = None
    pre_wait_time: Optional[float] = None

class DownloadResponse(BaseModel):
    result: str = ""
    error: ErrorDetail = ErrorDetail()
