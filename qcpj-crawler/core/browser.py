from playwright.sync_api import sync_playwright

class Browser:

    # 处理__init__的相关逻辑。
    def __init__(self,
                 channel: str = 'msedge',
                 headless: bool = True,
                 image: bool = False):
        self.start(channel, headless,  image)

    # 启动start的相关逻辑。
    def start(self, channel, headless, image):
        _args = ['--disable-blink-features=AutomationControlled']
        if not image:
            _args.append("--blink-settings=imagesEnabled=false")

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            channel=channel,
            headless=headless,
            ignore_default_args=['--enable-automation'],
            args=_args,
        )
        self._ua = self.playwright.devices['Desktop Edge']
        self.context = self.browser.new_context(
            **self._ua,
            permissions=['notifications'],
            ignore_https_errors=True,
        )

    # 停止stop的相关逻辑。
    def stop(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()