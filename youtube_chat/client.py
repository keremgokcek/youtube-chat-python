from asyncio import sleep, create_task, run
from aiohttp import ClientSession
from .request import fetch_live_page, fetch_chat
from .youtube_types import TextMessage
from .types.cookie import Cookie
from typing import TYPE_CHECKING, Callable, Optional, Union
from time import time

if TYPE_CHECKING:
    from request import RequestOptions


MAX_RETRY_ATTEMPTS = 3


class Client:
    def __init__(self, live_url: str, cookies: Cookie | None = None):
        self.live_url: str = live_url
        self.cookies: Cookie = cookies

        self.options: 'RequestOptions' = None
        self.session: ClientSession
        self.running: bool = False

        self.on_ready: list[Callable] = []
        self.on_message: list[Callable] = []
        self.on_stream_end: list[Callable] = []
        self.commands: dict[str, dict] = {}
        self.cooldowns: dict[str, Union[dict[str, float], float]] = {}

        self.live_id: str | None
        self.channel_id: str | None
        self.retry_attempts: int = 0

    def run(
        self, ignore_first: bool = True, wait_for_streams: bool = True
    ) -> None:
        async def main():
            if wait_for_streams:
                while True:
                    await self.start(
                        ignore_first=ignore_first,
                        wait_for_streams=wait_for_streams,
                    )
                    await sleep(30)
            else:
                await self.start(
                    ignore_first=ignore_first,
                    wait_for_streams=wait_for_streams,
                )

        run(main())

    async def start(
        self, ignore_first: bool = True, wait_for_streams: bool = True
    ):
        cookie_jar = self.cookies and await self.cookies._load_cookies()

        self.session = ClientSession(cookie_jar=cookie_jar)

        live_page_data = await fetch_live_page(self.live_url, self.session)
        while wait_for_streams and not live_page_data:
            await sleep(30)
            live_page_data = await fetch_live_page(self.live_url, self.session)

        if not live_page_data:
            print('Livestream was not found.')
            return

        self.options, live_id, channel_id = live_page_data

        self.running = True
        self.live_id = live_id
        self.channel_id = channel_id

        for on_ready in self.on_ready:
            create_task(on_ready())

        await self.execute(not ignore_first)
        await sleep(1)

        while self.running:
            try:
                await self.execute()
                self.retry_attempts = 0
            except ValueError as e:
                self.retry_attempts += 1
                print(
                    f'Failed to fetch chat, retrying... ({self.retry_attempts}/{MAX_RETRY_ATTEMPTS})'
                )

                if self.retry_attempts >= MAX_RETRY_ATTEMPTS:
                    self.running = False

                    for on_stream_end in self.on_stream_end:
                        create_task(on_stream_end())

            await sleep(1)

        await self.session.close()

    async def execute(self, emit: bool = True):
        if not self.options:
            raise ValueError('This client is not ready for execute')

        chat_items, self.options.continuation = await fetch_chat(
            self.options, self.session
        )

        for item in chat_items:
            if not emit:
                continue

            for on_message in self.on_message:
                create_task(on_message(item))

            # Command check
            if (
                isinstance(item, TextMessage)
                and isinstance(item.message[0], str)
                and item.message[0].startswith('!')
            ):
                command_name = item.message[0].split()[0][1:]
                command = self.commands.get(command_name)

                if not command:
                    continue

                cooldown = command.get('cooldown', 0)
                user_cooldown = command.get('user_cooldown', False)
                now = time()

                if user_cooldown:
                    user_id = item.author_channel_id
                    if command_name not in self.cooldowns:
                        self.cooldowns[command_name] = {}
                    user_cooldowns = self.cooldowns[command_name]

                    last_used = user_cooldowns.get(user_id, 0)
                    if now - last_used >= cooldown:
                        create_task(command['func'](item))
                        user_cooldowns[user_id] = now

                else:
                    last_used = self.cooldowns.get(command_name, 0)
                    if now - last_used >= cooldown:
                        create_task(command['func'](item))
                        self.cooldowns[command_name] = now

    async def shutdown(self):
        await self.session.close()
        self.running = False

    def event(self, func: Callable) -> Callable:
        match func.__name__:
            case "on_ready":
                self.on_ready.append(func)
            case "on_message":
                self.on_message.append(func)
            case "on_stream_end":
                self.on_stream_end.append(func)

        return func

    def command(
        self,
        name: Optional[str] = None,
        cooldown: int = 0,
        user_cooldown: bool = False,
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            command_name = name or func.__name__
            self.commands[command_name] = {
                'func': func,
                'cooldown': cooldown,
                'user_cooldown': user_cooldown,
            }

            return func

        return decorator
