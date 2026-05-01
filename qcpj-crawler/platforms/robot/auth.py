import os
import threading
import time
from typing import Callable, List, Optional
from urllib.parse import unquote

import ujson as json
from playwright.sync_api import BrowserContext

from config import AUTH_ROOT_DIR
from core.browser import Browser

PLATFORM_NAME = "robot"
AUTH_DIR = os.path.join(AUTH_ROOT_DIR, PLATFORM_NAME)
AUTH_FILE = os.path.join(AUTH_DIR, "auth.json")

LOGIN_URL = "https://www.jiqirenai.com/login"
CURRENT_USER_URL = "https://www.jiqirenai.com/restful/user/profile/get"


class RobotAuthManager:
    def has_auth(self) -> bool:
        return os.path.exists(AUTH_FILE)

    def check_login_valid(self, context: BrowserContext) -> bool:
        try:
            headers = self._build_profile_headers(context)
            res = context.request.post(
                CURRENT_USER_URL,
                headers=headers,
                data={},
            ).json()
            if not isinstance(res, dict):
                return False
            msg = str(res.get("msg") or "").strip().lower()
            data = res.get("data")
            code = res.get("code")
            if data is not None:
                return True
            if str(code) in {"0", "200"} and data is not None:
                return True
            return False
        except Exception:
            return False

    def _load_auth_payload(self) -> dict:
        if not os.path.exists(AUTH_FILE):
            return {}
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f) or {}

    def load_auth(self, context: BrowserContext) -> None:
        if not self.has_auth():
            return
        payload = self._load_auth_payload()
        cookies = payload.get("cookies", []) or []
        safe_cookies = self._sanitize_cookies(cookies)
        if safe_cookies:
            context.add_cookies(safe_cookies)

    def save_auth(self, cookies: List) -> None:
        os.makedirs(AUTH_DIR, exist_ok=True)
        safe_cookies = self._sanitize_cookies(cookies)
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump({"cookies": safe_cookies}, f, ensure_ascii=False)

    def _sanitize_header_value(self, value: str) -> str:
        text = str(value or "")
        text = text.replace("\r", "").replace("\n", "").strip()
        filtered = []
        for ch in text:
            code = ord(ch)
            if code == 9 or 32 <= code <= 126:
                filtered.append(ch)
        return "".join(filtered).strip()

    def _sanitize_cookies(self, cookies: List) -> List[dict]:
        safe_items: List[dict] = []
        for item in cookies or []:
            if not isinstance(item, dict):
                continue
            name = self._sanitize_header_value(item.get("name") or "")
            value = self._sanitize_header_value(item.get("value") or "")
            domain = self._sanitize_header_value(item.get("domain") or "")
            path = str(item.get("path") or "/").strip() or "/"
            if not name:
                continue
            safe_item = dict(item)
            safe_item["name"] = name
            safe_item["value"] = value
            safe_item["path"] = path
            if domain:
                safe_item["domain"] = domain
            safe_items.append(safe_item)
        return safe_items

    def _extract_auth_header(self, context: BrowserContext) -> str:
        try:
            cookies = context.cookies()
        except Exception:
            cookies = []
        token_value = ""
        for item in cookies:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if name != "auth._token.local":
                continue
            token_value = str(item.get("value") or "").strip()
            if token_value:
                break
        token_value = self._sanitize_header_value(unquote(token_value))
        if not token_value:
            return ""
        if token_value.lower().startswith("bearer "):
            return token_value
        return f"Bearer {token_value}"

    def _build_profile_headers(self, context: BrowserContext) -> dict:
        headers = {
            "accept": "application/json, text/plain, */*",
            "origin": "https://www.jiqirenai.com",
            "referer": LOGIN_URL,
        }
        auth = self._extract_auth_header(context)
        if auth:
            headers["authorization"] = auth
        return headers

    def _interactive_login_with_context(self, context: BrowserContext, logger: Callable[[str], None]) -> None:
        page = context.new_page()
        try:
            logger("[robot] 开始浏览器交互登录")
            page.goto(LOGIN_URL)
            logger("[robot] 请在浏览器中完成登录，正在等待认证信息...")

            max_wait_seconds = 15 * 60
            elapsed = 0
            while elapsed < max_wait_seconds:
                if page.is_closed():
                    raise RuntimeError("[robot] 登录窗口已关闭，登录已取消")
                if self.check_login_valid(context):
                    self.save_auth(context.cookies())
                    logger(f"[robot] 登录成功，认证信息已保存到 {AUTH_FILE}")
                    return
                time.sleep(2)
                elapsed += 2

            raise TimeoutError(f"[robot] 登录超时，等待 {max_wait_seconds}s 后仍未成功")
        finally:
            try:
                page.close()
            except Exception:
                pass

    def do_login(self, context: Optional[BrowserContext] = None, log_fn=None) -> None:
        logger = log_fn or print

        if context is not None:
            self._interactive_login_with_context(context, logger)
            return

        error_holder = {}

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

    def get_context(self, browser: Browser, log_fn=None) -> BrowserContext:
        logger = log_fn or print
        context = browser.context

        self.load_auth(context)
        if not self.check_login_valid(context):
            logger("[robot] 登录状态已失效，开始重新登录")
            self.do_login(log_fn=logger)
            self.load_auth(context)
            if not self.check_login_valid(context):
                raise RuntimeError("[robot] 登录失败：用户校验未通过")

        return context


if __name__ == "__main__":
    browser = Browser(channel="msedge", headless=True, image=False)
    try:
        manager = RobotAuthManager()
        manager.get_context(browser)
    finally:
        browser.stop()
