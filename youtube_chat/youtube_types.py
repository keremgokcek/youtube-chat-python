class Emoji:
    def __init__(self, item: dict):
        self.id: str = item['emoji']['emojiId']
        self.shortcuts: list[str] = item['emoji'].get('shortcuts', [])
        self.search_terms: list[str] = item['emoji'].get('searchTerms', [])
        self.supports_skin_tone: bool = item['emoji'].get(
            'supportsSkinTone', False
        )
        self.is_custom_emoji: bool = item['emoji'].get('isCustomEmoji', False)
        self.image: list['Thumbnail'] = ...

    def __str__(self):
        return ', '.join(
            [f'{key}={value}' for key, value in self.__dict__.items()]
        )

    def __repr__(self):
        return self.__str__()


class Link:
    def __init__(self, item: dict):
        self.url: str = item['navigationEndpoint']['urlEndpoint']['url']
        self.text: str = item['text']


class Thumbnail:
    def __init__(self, item: dict):
        self.url: str = item['url']
        self.width: int = item['width']
        self.height: int = item['height']


class Badge:
    def __init__(self, item: dict):
        self.live_chat_badge_renderer: dict = item[
            'liveChatAuthorBadgeRenderer'
        ]
        self.tooltip: str = item['liveChatAuthorBadgeRenderer']['tooltip']
        self.icon: str = item['liveChatAuthorBadgeRenderer']['icon'][
            'iconType'
        ]
        self.thumbnail: list['Thumbnail'] = ...


class BaseMessage:
    def __init__(self, item: dict):
        try:
            self.author_name: str = item['authorName']['simpleText']
            self.author_photo: list['Thumbnail'] = ...
            self.author_badges: list['Badge'] = ...
            self.id: str = item['id']
            self.timestamp_usec: str = item['timestampUsec']
            self.author_channel_id: str = item['authorExternalChannelId']
        except KeyError:
            print('[ERROR]')
            print(item)


# Represents a regular text message.
class TextMessage(BaseMessage):
    def __init__(self, item: dict):
        super().__init__(item)

        self.message: list[str | 'Emoji' | 'Link'] = []
        for content in item['message']['runs']:
            if content.get('navigationEndpoint'):
                self.message.append(Link(content))
            elif content.get('text'):
                self.message.append(content['text'])
            elif content.get('emoji'):
                self.message.append(Emoji(content))


# Represents a membership milestone or new membership message.
class MembershipItem(BaseMessage):
    def __init__(self, item: dict):
        super().__init__(item)

        if not item.get('headerPrimaryText'):  # New membership message
            self.primary_text: str = ''.join(
                [text['text'] for text in item['headerSubtext']['runs']]
            )
            self.membership_level: str = ''
        else:  # Membership milestone message
            self.primary_text: str = ''.join(
                [text['text'] for text in item['headerPrimaryText']['runs']]
            )
            self.membership_level: str = item['headerSubtext']['simpleText']

        self.message: list[str | 'Emoji'] = []
        if not item.get('message'):
            return

        for content in item['message']['runs']:
            if content.get('text'):
                self.message.append(content['text'])
            elif content.get('emoji'):
                self.message.append(Emoji(content))


# Represents a superchat message.
class PaidMessage(BaseMessage):
    def __init__(self, item: dict):
        super().__init__(item)

        self.purchase_amount: str = item['purchaseAmountText']['simpleText']

        self.message: list[str | 'Emoji'] = []
        if not item.get('message'):
            return

        for content in item['message']['runs']:
            if content.get('text'):
                self.message.append(content['text'])
            elif content.get('emoji'):
                self.message.append(Emoji(content))


# Represents a supersticker message.
class PaidSticker(BaseMessage):
    def __init__(self, item: dict):
        super().__init__(item)

        self.purchase_amount: str = item['purchaseAmountText']['simpleText']


# Represents a sponsorships gift purchase announcement.
class SponsorshipsGiftPurchaseAnnouncement(BaseMessage):
    def __init__(self, item: dict):
        item.update(item['header']['liveChatSponsorshipsHeaderRenderer'])
        super().__init__(item)

        self.primary_text = ''.join(
            [text['text'] for text in item['primaryText']['runs']]
        )


# Represents a sponsorships gift redemption announcement.
class SponsorshipsGiftRedemptionAnnouncement(BaseMessage):
    def __init__(self, item: dict):
        super().__init__(item)

        self.message: str = ''.join(
            [text['text'] for text in item['message']['runs']]
        )
