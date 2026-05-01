import os
import threading
import time
from typing import Callable, List, Optional

import ujson as json
from playwright.sync_api import BrowserContext

from config import AUTH_ROOT_DIR
from core.browser import Browser

PLATFORM_NAME = "benben"
AUTH_DIR = os.path.join(AUTH_ROOT_DIR, PLATFORM_NAME)
AUTH_FILE = os.path.join(AUTH_DIR, "auth.json")
LEGACY_AUTH_FILE = os.path.join(AUTH_ROOT_DIR, "auth.json")

LOGIN_URL = "https://web.apbenben.com/login/loginPage"
LOGIN_OK_URL = "**/web/index"
USER_DETAIL_URL = "https://api.apbenben.com/benben-dubbo-web/user/getUserDetail"


class BenbenAuthManager:

    # 判断认证。
    def has_auth(self) -> bool:
        return os.path.exists(AUTH_FILE) or os.path.exists(LEGACY_AUTH_FILE)

    # 检查loginvalid。
    def check_login_valid(self, context: BrowserContext) -> bool:
        try:
            res = context.request.post(USER_DETAIL_URL).json()
            return (res or {}).get("code") == "200"
        except Exception:
            return False

    # 加载认证载荷。
    def _load_auth_payload(self) -> dict:
        file_path = AUTH_FILE if os.path.exists(AUTH_FILE) else LEGACY_AUTH_FILE
        if not os.path.exists(file_path):
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f) or {}

    # 加载认证。
    def load_auth(self, context: BrowserContext) -> None:
        if not self.has_auth():
            return
        payload = self._load_auth_payload()
        cookies = payload.get("cookies", []) or []
        context.add_cookies(cookies)
        # Migrate legacy auth file to platform-specific path on first successful read.
        if cookies and not os.path.exists(AUTH_FILE):
            self.save_auth(cookies)

    # 保存认证。
    def save_auth(self, cookies: List) -> None:
        os.makedirs(AUTH_DIR, exist_ok=True)
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump({"cookies": cookies}, f, ensure_ascii=False)

    # 处理loginwith上下文。
    def _interactive_login_with_context(self, context: BrowserContext, logger: Callable[[str], None]) -> None:
        page = context.new_page()
        try:
            logger("[犇犇] 开始浏览器交互登录")
            goto_timeout_ms = int(os.getenv("BENBEN_LOGIN_GOTO_TIMEOUT_MS", "120000"))
            goto_retry_times = max(int(os.getenv("BENBEN_LOGIN_GOTO_RETRY_TIMES", "3")), 1)
            last_error = None
            for attempt in range(goto_retry_times):
                try:
                    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=goto_timeout_ms)
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt < goto_retry_times - 1:
                        logger(
                            f"[benben] login page open failed, retry {attempt + 2}/{goto_retry_times}: {exc}"
                        )
                        time.sleep(2)
            if last_error is not None:
                raise last_error
            logger("[犇犇] 请在浏览器中完成登录，正在等待认证信息...")

            max_wait_seconds = 15 * 60
            elapsed = 0
            while elapsed < max_wait_seconds:
                if page.is_closed():
                    raise RuntimeError("[犇犇] 登录窗口已关闭，登录已取消")
                if self.check_login_valid(context):
                    self.save_auth(context.cookies())
                    logger(f"[犇犇] 登录成功，认证信息已保存到 {AUTH_FILE}")
                    return
                time.sleep(2)
                elapsed += 2

            raise TimeoutError(f"[犇犇] 登录超时，等待 {max_wait_seconds}s 后仍未成功")
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
            logger("[犇犇] 登录状态已失效，开始重新登录")
            self.do_login(log_fn=logger)
            self.load_auth(context)
            if not self.check_login_valid(context):
                raise RuntimeError("[犇犇] 登录失败：用户校验未通过")

        return context


if __name__ == "__main__":
    browser = Browser(channel="msedge", headless=True, image=False)
    try:
        manager = BenbenAuthManager()
        manager.get_context(browser)
    finally:
        browser.stop()
