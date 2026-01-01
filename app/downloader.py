import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse
from string import Template
import re

import nodriver as uc

from .models import DownloadRequest, WaitCSSSelector, Wait, Scroll

COOKIE_PATH = Path("/app/cookie/")

logger = logging.getLogger(__name__)


async def _cookie_to_param(
    cookies: list[uc.cdp.network.Cookie],
) -> list[uc.cdp.network.CookieParam]:
    if not cookies:
        return []
    return [uc.cdp.network.CookieParam.from_json(c.to_json()) for c in cookies if c]


async def _add_cookies(
    add_cookies: list[uc.cdp.util.T_JSON_DICT],
    base_cookies: list[uc.cdp.network.CookieParam],
):
    if not add_cookies:
        return base_cookies
    results = [c for c in base_cookies]
    for c in add_cookies:
        results.append(uc.cdp.network.CookieParam.from_json(c))
    return results


async def _set_cookies(
    cookiejar: uc.core.browser.CookieJar, cookies: list[uc.cdp.network.CookieParam]
):
    connection = None
    for tab in cookiejar._browser.tabs:
        if tab.closed:
            continue
        connection = tab
        break
    else:
        connection = cookiejar._browser.connection
    await connection.send(uc.cdp.storage.set_cookies(cookies))


async def _wait_css_selector(page, selector: WaitCSSSelector):
    if selector.pre_wait_time and selector.pre_wait_time > 0:
        await asyncio.sleep(selector.pre_wait_time)
    if selector.on_error:
        max_retry = (
            selector.on_error.max_retries
            if selector.on_error.max_retries and selector.on_error.max_retries > 0
            else 1
        )
    else:
        max_retry = 1
    for retry_count in range(max_retry):
        try:
            await page.wait_for(
                selector=selector.selector,
                timeout=selector.timeout,
            )
            return
        except Exception as e:
            logger.warning(
                f"Waiting for selector '{selector.selector}' failed: {e}, retry_count={retry_count}"
            )
            if retry_count >= max_retry - 1:
                logger.error(
                    f"Max retries reached for selector '{selector.selector}', retry_count={retry_count}"
                )
                raise e
            if selector.on_error.action_type == "raise":
                logger.error(
                    f"Raising error for selector '{selector.selector}' as per on_error action"
                )
                raise e
            elif selector.on_error.action_type == "retry":
                wait_time = (
                    selector.on_error.wait_time
                    if selector.on_error.wait_time and selector.on_error.wait_time > 0
                    else 0
                )
                if wait_time > 0 and selector.on_error.check_exist_tag:
                    elem = await page.select(
                        selector.on_error.check_exist_tag, timeout=wait_time
                    )
                    if elem is None:
                        logger.error(
                            f"Check exist tag '{selector.on_error.check_exist_tag}' not found, raising error"
                        )
                        raise e
                    if elem:
                        logger.info(
                            f"Check exist tag '{selector.on_error.check_exist_tag}' found, stopping retries"
                        )
                        return
                    logger.warning(
                        f"Check exist tag '{selector.on_error.check_exist_tag}' not found, continuing retries"
                    )
                    continue
                logger.info(
                    f"Retrying to wait for selector '{selector.selector}', retry_count={retry_count + 1}"
                )
                continue
            else:
                logger.error(
                    f"Unknown on_error action_type '{selector.on_error.action_type}' for selector '{selector.selector}'"
                )
                raise e


async def get_domain_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    return parsed_url.netloc


async def get_cookie_filepath(filename: str, url: str) -> Path:
    if filename:
        return COOKIE_PATH / filename
    domain = await get_domain_from_url(url)
    return COOKIE_PATH / f"{domain}_cookies.dat"


async def format_version_regex(version):
    # 「(数字.数字) の後の .0」を探して、前のグループ部分だけに置換する
    return re.sub(r"^(\d+\.\d+)\.0$", r"\1", version)


async def _get_page_with_ua(useragent):
    if not useragent:
        return await uc.start()

    ua_os_version = await format_version_regex(useragent.os_version)
    ua_template = Template(
        "Mozilla/5.0 (Windows NT ${ua_os_version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${major}.0.0.0 Safari/537.36"
    )
    ua_template = ua_template.substitute(
        major=useragent.major, ua_os_version=ua_os_version
    )
    browser = await uc.start(browser_args=[f"--user-agent={ua_template}"])
    page = await browser.get("about:blank")
    js_template = Template(
        """
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'userAgentData', {
            get: () => ({
                brands: [
                    { brand: 'Google Chrome', version: '${major}' },
                    { brand: 'Not_A Brand', version: '24' },
                    { brand: 'Chromium', version: '${major}' }
                ],
                mobile: false,
                platform: '${platform}',
                getHighEntropyValues: (hints) => Promise.resolve({
                    platform: '${platform}',
                    platformVersion: '${os_version}',
                    architecture: 'x86',
                    model: '',
                    bitness: '64'
                })
            })
        });
        """
    )

    injection_script = js_template.substitute(
        major=useragent.major,
        platform=useragent.platform,
        os_version=useragent.os_version,
    )
    await page.send(
        uc.cdp.page.add_script_to_evaluate_on_new_document(source=injection_script)
    )
    return page


async def dl_with_nodriver(req: DownloadRequest):
    logger.debug(f"input_params : {req.model_dump()}")
    browser = None
    page = None
    try:

        page = await _get_page_with_ua(req.useragent)
        page = await page.get(req.url)

        if req.cookie:
            if req.cookie.load:
                try:
                    cookie_fpath = await get_cookie_filepath(
                        filename=req.cookie.filename, url=req.url
                    )
                    await browser.cookies.load(cookie_fpath)
                except Exception as e:
                    logger.error(f"Error loading cookies from file: {e}")

            if req.cookie.cookie_dict_list:
                br_cookies = await _cookie_to_param(await browser.cookies.get_all())
                included_cookies = await _add_cookies(
                    add_cookies=req.cookie.cookie_dict_list, base_cookies=br_cookies
                )
                await _set_cookies(browser.cookies, included_cookies)

            if req.cookie.load or req.cookie.cookie_dict_list:
                await page.reload()

        if not req.actions:
            req.actions = []
        for action in req.actions:
            if isinstance(action, Wait):
                await asyncio.sleep(action.time)
                continue
            elif isinstance(action, Scroll):
                if action.to_bottom:
                    await page.evaluate(
                        """() => {
                            window.scrollTo(0, document.body.scrollHeight);
                        }"""
                    )
                elif action.amount:
                    await page.scroll_down(action.amount)
                if action.pause_time and action.pause_time > 0:
                    await asyncio.sleep(action.pause_time)
                continue

        if req.wait_css_selector:
            try:
                await _wait_css_selector(page, req.wait_css_selector)
            except Exception as e:
                logger.error(f"Error waiting for CSS selector: {e}")
                return False, e, []
        elif req.page_wait_time:
            await asyncio.sleep(req.page_wait_time)

        html_content = await page.get_content()
        cookies = []
        if req.cookie and req.cookie.save:
            try:
                cookie_fpath = await get_cookie_filepath(
                    filename=req.cookie.filename, url=req.url
                )
                await browser.cookies.save(cookie_fpath)
            except Exception as e:
                logger.error(f"Error saving cookies to file: {e}")

        if req.cookie and req.cookie.return_cookies:
            uc_cookies = await browser.cookies.get_all()
            cookies = [c.to_json() for c in uc_cookies]

        return True, html_content, cookies

    except Exception as e:
        logger.exception("other error")
        return False, e, []
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                logger.exception("page close error")
        if browser:
            try:
                browser.stop()
            except Exception:
                logger.exception("browser stop error")
