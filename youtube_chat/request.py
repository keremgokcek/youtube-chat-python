import re
from aiohttp import ClientSession
from dataclasses import dataclass
from typing import TYPE_CHECKING
from .parser import parse_chat_data

if TYPE_CHECKING:
    from youtube_types import BaseMessage


@dataclass
class RequestOptions:
    api_key: str
    client_version: str
    continuation: str


async def fetch_live_page(
    url: str, session: ClientSession
) -> tuple[RequestOptions, str, str]:
    async with session.get(url) as response:
        return get_options_from_live_page(await response.text())


def get_options_from_live_page(data: str) -> tuple[RequestOptions, str]:
    live_id_regex = re.compile(
        r'<link rel="canonical" href="https://www.youtube.com/watch\?v=(.+?)">'
    )
    if match_object := live_id_regex.search(data):
        live_id = match_object.group(1)
    else:
        raise ValueError('Live stream was not found')

    channel_id_regex = re.compile(r'"channelId":"([A-Za-z0-9_]{24})"')
    if match_object := channel_id_regex.search(data):
        channel_id = match_object.group(1)
    else:
        raise ValueError('Channel ID not found')

    replay_regex = re.compile(r'''['"]isReplay['"]:\s*(true)''')
    if replay_regex.search(data):
        raise ValueError(f'{live_id} is finished livestream')

    api_key_regex = re.compile(
        r'''['"]INNERTUBE_API_KEY['"]:\s*['"](.+?)['"]'''
    )
    if match_object := api_key_regex.search(data):
        api_key = match_object.group(1)
    else:
        raise ValueError('API key was not found')

    client_version_regex = re.compile(
        r'''['"]clientVersion['"]:\s*['"]([\d.]+?)['"]'''
    )
    if match_object := client_version_regex.search(data):
        client_version = match_object.group(1)
    else:
        raise ValueError('Client version was not found')

    continuation_regex = re.compile(
        r'''['"]continuation['"]:\s*['"](.+?)['"]'''
    )
    if match_object := continuation_regex.search(data):
        continuation = match_object.group(1)
    else:
        raise ValueError('Continuation was not found')

    return (
        RequestOptions(api_key, client_version, continuation),
        live_id,
        channel_id,
    )


async def fetch_chat(
    options: RequestOptions, session: ClientSession
) -> tuple[list['BaseMessage'], str]:
    url = f"https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key={options.api_key}"
    body = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": options.client_version,
                "hl": "tr",
            }
        },
        "continuation": options.continuation,
    }

    async with session.post(url, json=body) as response:
        return parse_chat_data(await response.json())
