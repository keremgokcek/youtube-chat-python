from aiohttp import CookieJar
from typing import Self


class Cookie:
    def __init__(self, cookie_dict: dict[str, str]) -> None:
        self._cookie_dict: dict[str, str] = cookie_dict
        self._cookie_jar: CookieJar | None

    async def _load_cookies(self) -> CookieJar:
        self._cookie_jar = CookieJar()
        self._cookie_jar.update_cookies(self._cookie_dict)
        return self._cookie_jar

    async def get_cookies(self) -> CookieJar:
        return self._cookie_jar or await self._load_cookies()

    @classmethod
    def from_file(cls, cookie_file: str) -> Self:
        cookies: dict[str, str] = {}

        with open(cookie_file, 'r') as f:
            for line in f.readlines():
                if line.startswith('#') or line.startswith('\n'):
                    continue

                parts = line.strip().split('\t')

                cookie_name = parts[5]
                cookie_value = parts[6]

                cookies[cookie_name] = cookie_value

        return cls(cookies)

    @classmethod
    def from_dict(cls, cookies: dict[str, str]) -> Self:
        return cls(cookies)
