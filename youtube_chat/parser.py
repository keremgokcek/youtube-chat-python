from .youtube_types import (
    TextMessage,
    MembershipItem,
    PaidMessage,
    PaidSticker,
    SponsorshipsGiftPurchaseAnnouncement,
    SponsorshipsGiftRedemptionAnnouncement,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from youtube_types import BaseMessage


def parse_chat_data(data: dict) -> tuple[list['BaseMessage'], str]:
    if not data.get('continuationContents'):
        with open('error.json', 'w') as f:
            import json

            json.dump(data, f)
        raise ValueError('Live stream was finished')
    elif data['continuationContents']['liveChatContinuation'].get('actions'):
        chat_items = filter(
            None,
            list(
                map(
                    parse_action_to_chat_item,
                    data['continuationContents']['liveChatContinuation'][
                        'actions'
                    ],
                )
            ),
        )
    else:
        chat_items = []

    if continuation_data := data['continuationContents'][
        'liveChatContinuation'
    ]['continuations'][0]:
        if invalidation_continuation_data := continuation_data.get(
            'invalidationContinuationData'
        ):
            continuation = invalidation_continuation_data['continuation']
        elif timed_continuation_data := continuation_data.get(
            'timedContinuationData'
        ):
            continuation = timed_continuation_data['continuation']
        else:
            continuation = ''
    else:
        continuation = ''

    return chat_items, continuation


def parse_action_to_chat_item(action: dict) -> 'BaseMessage':
    if action.get('addChatItemAction'):
        item = action['addChatItemAction']['item']
    elif action.get('replaceChatItemAction'):
        item = action['replaceChatItemAction']['replacementItem']
    else:
        return None

    if item.get('liveChatTextMessageRenderer'):
        item = TextMessage(item['liveChatTextMessageRenderer'])
    elif item.get('liveChatMembershipItemRenderer'):
        item = MembershipItem(item['liveChatMembershipItemRenderer'])
    elif item.get('liveChatPaidMessageRenderer'):
        item = PaidMessage(item['liveChatPaidMessageRenderer'])
    elif item.get('liveChatPaidStickerRenderer'):
        item = PaidSticker(item['liveChatPaidStickerRenderer'])
    elif item.get('liveChatSponsorshipsGiftPurchaseAnnouncementRenderer'):
        item = SponsorshipsGiftPurchaseAnnouncement(
            item['liveChatSponsorshipsGiftPurchaseAnnouncementRenderer']
        )
    elif item.get('liveChatSponsorshipsGiftRedemptionAnnouncementRenderer'):
        item = SponsorshipsGiftRedemptionAnnouncement(
            item['liveChatSponsorshipsGiftRedemptionAnnouncementRenderer']
        )
    else:
        item = None

    return item
