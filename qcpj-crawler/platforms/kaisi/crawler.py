"""兼容层：历史报价抓取实现已迁移到 platforms.kaisi.history.crawler。"""

from platforms.kaisi.history.crawler import KaisiCrawler

__all__ = ["KaisiCrawler"]
