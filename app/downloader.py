import asyncio
import nodriver as uc
from .models import DownloadRequest

async def dl_with_nodriver(req: DownloadRequest):
    xvfb_process = None
    browser = None
    page = None
    try:
        # 仮想ディスプレイを起動
        xvfb_process = await asyncio.create_subprocess_exec(
            'Xvfb', ':99', '-ac', '-screen', '0', '1920x1080x24'
        )

        browser = await uc.start()
        page = await browser.get(
            req.url,
            page_load_timeout=req.page_load_timeout
        )

        if req.cookie_dict_list:
            for cookie in req.cookie_dict_list:
                await page.add_cookie(**cookie)
            # クッキー設定後にリロード
            await page.reload()

        if req.wait_css_selector:
            if req.pre_wait_time:
                await asyncio.sleep(req.pre_wait_time)
            await page.wait_for(selector=req.wait_css_selector, timeout=req.tag_wait_timeout)
        elif req.page_wait_time:
            await asyncio.sleep(req.page_wait_time)

        # pre_wait_timeが指定されていて、上記の待機条件がない場合
        elif req.pre_wait_time and not req.wait_css_selector and not req.page_wait_time:
            await asyncio.sleep(req.pre_wait_time)


        html_content = await page.get_content()
        return True, html_content

    except Exception as e:
        return False, e
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass # Ignore errors on cleanup
        if browser:
            try:
                browser.stop()
            except Exception:
                pass # Ignore errors on cleanup
        if xvfb_process and xvfb_process.returncode is None:
            try:
                xvfb_process.kill()
                await xvfb_process.wait()
            except Exception:
                pass # Ignore errors on cleanup
