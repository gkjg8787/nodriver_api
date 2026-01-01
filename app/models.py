from pydantic import BaseModel, Field
from typing import Optional, Any


class ErrorDetail(BaseModel):
    error_msg: str = ""
    error_type: str = ""


class Cookie(BaseModel):
    cookie_dict_list: Optional[list[dict[str, Any]]] = None
    return_cookies: Optional[bool] = False
    save: Optional[bool] = False
    load: Optional[bool] = False
    filename: Optional[str] = None


class OnError(BaseModel):
    action_type: str = "raise"  # "raise" or "retry"
    max_retries: int = 0
    wait_time: float = 0.0  # seconds
    check_exist_tag: str = ""  # CSS selector


class WaitCSSSelector(BaseModel):
    selector: str
    timeout: Optional[int] = 10  # seconds
    on_error: Optional[OnError] = OnError()
    pre_wait_time: Optional[float] = 0.0  # seconds


class Wait(BaseModel):
    time: int = 0  # seconds


class Scroll(BaseModel):
    to_bottom: bool = False
    amount: Optional[int] = None  # pixels
    pause_time: Optional[float] = 0.5  # seconds


class DownloadRequest(BaseModel):
    url: str
    cookie: Optional[Cookie] = None
    wait_css_selector: Optional[WaitCSSSelector] = None
    page_wait_time: Optional[float] = None
    actions: list[Wait | Scroll] = Field(default_factory=list)


class DownloadResponse(BaseModel):
    result: str = ""
    cookies: list[dict[str, Any]] = []
    error: ErrorDetail = ErrorDetail()
