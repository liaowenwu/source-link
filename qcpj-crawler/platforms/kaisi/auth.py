import os
import threading
import time
from typing import Callable, List, Optional

import ujson as json
from playwright.sync_api import BrowserContext

from config import AUTH_ROOT_DIR
from core.browser import Browser

PLATFORM_NAME = "kaisi"
AUTH_DIR = os.path.join(AUTH_ROOT_DIR, PLATFORM_NAME)
AUTH_FILE = os.path.join(AUTH_DIR, "auth.json")

LOGIN_URL = "https://www.cassmall.com/passport/login"
CURRENT_USER_URL = "https://www.cassmall.com/seller/_current"


class KaisiAuthManager:

    # 判断认证。
    def has_auth(self) -> bool:
        return os.path.exists(AUTH_FILE)

    # 检查loginvalid。
    def check_login_valid(self, context: BrowserContext) -> bool:
        try:
            res = context.request.get(CURRENT_USER_URL).json()
            return (res or {}).get("errorCode") == 0 and bool((res or {}).get("data"))
        except Exception:
            return False

    # 加载认证载荷。
    def _load_auth_payload(self) -> dict:
        if not os.path.exists(AUTH_FILE):
            return {}
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f) or {}

    # 加载认证。
    def load_auth(self, context: BrowserContext) -> None:
        if not self.has_auth():
            return
        payload = self._load_auth_payload()
        cookies = payload.get("cookies", []) or []
        if cookies:
            context.add_cookies(cookies)

    # 保存认证。
    def save_auth(self, cookies: List) -> None:
        os.makedirs(AUTH_DIR, exist_ok=True)
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump({"cookies": cookies}, f, ensure_ascii=False)

    # 处理loginwith上下文。
    def _interactive_login_with_context(self, context: BrowserContext, logger: Callable[[str], None]) -> None:
        page = context.new_page()
        try:
            logger("[开思] 开始浏览器交互登录")
            page.goto(LOGIN_URL)
            logger("[开思] 请在浏览器中完成登录，正在等待认证信息...")

            max_wait_seconds = 15 * 60
            elapsed = 0
            while elapsed < max_wait_seconds:
                if page.is_closed():
                    raise RuntimeError("[开思] 登录窗口已关闭，登录已取消")
                if self.check_login_valid(context):
                    self.save_auth(context.cookies())
                    logger(f"[开思] 登录成功，认证信息已保存到 {AUTH_FILE}")
                    return
                time.sleep(2)
                elapsed += 2

            raise TimeoutError(f"[开思] 登录超时，等待 {max_wait_seconds}s 后仍未成功")
        finally:
            try:
                page.close()
            except Exception:
                pass

    # 处理login。
    def do_login(self, context: Optional[BrowserContext] = None, log_fn=None) -> None:
        logger = log_fn or print

        if context is not None:
            self._interactive_login_with_context(context, logger)
            return

        error_holder = {}

        # 处理inthread。
        def _login_in_thread():
            edge = None
            try:
                edge = Browser(channel="msedge", headless=False, image=True)
                self._interactive_login_with_context(edge.context, logger)
            except Exception as e:
                error_holder["error"] = e
            finally:
                if edge is not None:
                    try:
                        edge.stop()
                    except Exception:
                        pass

        t = threading.Thread(target=_login_in_thread, name=f"{PLATFORM_NAME}-interactive-login-thread", daemon=True)
        t.start()
        t.join()

        if "error" in error_holder:
            raise error_holder["error"]

    # 获取上下文。
    def get_context(self, browser: Browser, log_fn=None) -> BrowserContext:
        logger = log_fn or print
        context = browser.context

        self.load_auth(context)
        if not self.check_login_valid(context):
            logger("[开思] 登录状态已失效，开始重新登录")
            self.do_login(log_fn=logger)
            self.load_auth(context)
            if not self.check_login_valid(context):
                raise RuntimeError("[开思] 登录失败：用户校验未通过")

        return context


if __name__ == "__main__":
    browser = Browser(channel="msedge", headless=True, image=False)
    try:
        manager = KaisiAuthManager()
        manager.get_context(browser)
    finally:
        browser.stop()
