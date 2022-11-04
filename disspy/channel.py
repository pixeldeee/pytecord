"""
MIT License

Copyright (c) 2022 itttgg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Optional, Union, List, final, TypedDict

from json import dumps
from aiohttp import ClientSession
from requests import get
from disspy.typ import Url, SupportsStr

from disspy.embed import DisEmbed
from disspy.guild import Guild
from disspy.jsongenerators import _EmbedGenerator
from disspy.ui import ActionRow
from disspy.reaction import DisEmoji, DisOwnReaction
from disspy.payloads import message_payload


__all__: tuple = (
    "DisMessage",
    "Channel",
    "ChannelType",
    "DmMessage",
    "MessageDeleteEvent",
    "DmMessageDeleteEvent",
)


class MessagePayload(TypedDict):
    """MessagePayload
    Text message payload (typed)
    """

    content: str
    embeds: Optional[list]
    components: Optional[list]


class _SendingRestHandler:
    @staticmethod
    async def execute(
        channel_id: int, payload: MessagePayload, __session: ClientSession
    ) -> dict:
        """execute
        Send messages in channels

        Args:
            channel_id (int): Channel id
            payload (dict): Dict json
            token (str): Bot token

        Returns:
            dict: Json output
        """
        __url = f"https://discord.com/api/v9/channels/{channel_id}/messages"

        async with __session.post(__url, data=dumps(payload)) as data:
            j = await data.json()

            return j

    @staticmethod
    async def put_without_payload(url: Url, __session: ClientSession):
        """put_without_payload
        PUT method wtthout payload

        Args:
            url (Url): url for operation
            token (str): Bot token
        """
        await __session.put(url)

    @staticmethod
    async def delete(url: Url, __session: ClientSession):
        """delete
        DELETE method

        Args:
            url (Url): url for operation
            token (str): Bot token
        """
        await __session.delete(url=url)

    @staticmethod
    async def post_without_payload(url: Url, __session: ClientSession):
        """post_without_payload
        POST method wtthout payload

        Args:
            url (Url): url for operation
            token (str): Bot token
        """
        await __session.post(url=url)

    @staticmethod
    async def create_reaction(endpoint: str, __session: ClientSession):
        """create_reaction()

        Args:
            endpoint (str): Url endpoint
            token (str): Bot token
        """
        url = f"https://discord.com/api/v10{endpoint}"

        await __session.put(url)

    @staticmethod
    async def delete_message(url: Url, __session: ClientSession):
        """delete_message
        Delete message

        Args:
            url (str): Url of message
            token (str): Bot token
        """
        await __session.delete(url=url)


class _GettingChannelData:
    @staticmethod
    def execute(channel_id: int, token: str):
        """execute
        Get channel data by id

        Args:
            channel_id (int): Channel id
            token (str): Bot token

        Returns:
            dict: Json output
        """
        _u = f"https://discord.com/api/v10/channels/{channel_id}"
        _h = {"Authorization": f"Bot {token}"}

        return get(_u, headers=_h).json()

    @staticmethod
    def fetch(channel_id: int, token: str, message_id: int):
        """fetch
        Fetch message by channel id and message id

        Args:
            channel_id (int): Channel id
            token (str): Bot token
            message_id (int): Message id

        Returns:
            dict: Json output
        """
        _u = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
        _h = {"Authorization": f"Bot {token}"}

        return get(_u, headers=_h).json()


class _GettingGuildData:
    @staticmethod
    def execute(guild_id: int, token: str):
        """execute
        Get guild data

        Args:
            id (int)): Guild id
            token (str): Bot token

        Returns:
            dict: Json output
        """
        _u = f"https://discord.com/api/v10/guilds/{guild_id}"
        _h = {"Authorization": f"Bot {token}"}

        return get(_u, headers=_h).json()


@final
class Message:
    """
    Any message in channel

    ```
    @client.on_message('create')
    async def on_messagec(m: Message):
        await m.channel.send(m.content)
    ```

    ### Attributies

    `id: int` - Id of message (Snowflake)
    `type: int` - Type of message (For example, DM)
    `channel: Channel` - Message channel
    `content: str` - Message content (what's written in message)
    """
    def __init__(self, __data: dict, __token, __session) -> None:
        self._t = __token
        self._s = __session

        self.id: int = int(__data['id'])
        self.type: int = int(__data['type'])

        _channel_data = _GettingChannelData.execute(__data['channel_id'], __token)
        self.channel: Channel = Channel(_channel_data, __token, __session)

        self.content: str = __data['content']

    async def reply(
        self,
        content: Optional[SupportsStr] = None,
        *,
        embeds: Optional[List[DisEmbed]] = None,
        action_row: Optional[ActionRow] = None
    ):
        """
        Reply to message

        Args:
            content (Optional[str], optional): Message content (text)
            embeds (Optional[List[DisEmbed]], optional): Message embeds (DisEmbed objects)
            action_row (Optional[ActionRow], optional): Action row with components
        """
        _payload = message_payload(content, embeds, action_row)
        _payload.setdefault("message_reference", {"message_id": self.id})

        if _payload:
            data = await _SendingRestHandler.execute(self.channel.id, _payload, self._s)

            return Message(data, self._t, self._s)

        return None

    async def create_reaction(self, emoji: Union[DisEmoji, str]) -> DisOwnReaction:
        """
        Create reaction to message

        Args:
            emoji (Union[DisEmoji, str]): Emoji for reaction

        Returns:
            DisOwnReaction: Your reaction
        """
        if isinstance(emoji, DisEmoji):
            if emoji.type == "custom":
                emoji = f"{emoji.name}:{str(emoji.emoji_id)}"
            elif emoji.type == "normal":
                emoji = emoji.unicode

        await _SendingRestHandler.create_reaction(
            f"/channels/{self.channel.id}/messages/{self.id}/reactions/{emoji}/@me",
            self._s,
        )

        return DisOwnReaction(emoji, self.id, self.channel.id, self._t, self._s)

    async def delete(self):
        """
        Delete message
        """
        _u = (
            f"https://discord.com/api/v10/channels/{self.channel.id}/messages/{self.id}"
        )

        await _SendingRestHandler.delete_message(_u, self._s)

@final
class DisMessage:
    """
    Message in channel
    """

    def __init__(self, _data, __token, __session):

        self.json = _data

        _channel_data = _GettingChannelData.execute(_data['channel_id'], __token)
        self.channel = Channel(_channel_data, __token, __session)

        self.content: str = str(_data["content"])

        if _data["embeds"]:
            _j = _data["embeds"]

            self.embeds = []

            for i in _j:
                _e = None

                if i["footer"]["text"]:
                    _e = DisEmbed(
                        title=i["title"],
                        description=i["description"],
                        color=i["color"],
                        footer=i["footer"]["text"]
                    )
                else:
                    _e = DisEmbed(i["title"], description=i["description"], color=i["color"])

                if i["fields"]:
                    for field in i["fields"]:
                        try:
                            _e.add_field(field["name"], field["value"], inline=field["inline"])
                        except KeyError:
                            _e.add_field(field["name"], field["value"])

                self.embeds.append(_e)

        self.id: int = int(_data["id"])

        self._t = __token
        self.session = __session

    async def reply(
        self,
        content: Optional[SupportsStr] = None,
        *,
        embeds: Optional[List[DisEmbed]] = None,
        action_row: Optional[ActionRow] = None
    ):
        """reply
        Reply to message

        Args:
            content (Optional[str], optional): Message content (text). Defaults to None.
            embeds (Optional[List[DisEmbed]], optional): Message embeds (DisEmbed objects).
                                                         Defaults to None.
            action_row (Optional[ActionRow], optional): Action row with components.
                                                         Defaults to None.
        """
        _payload = message_payload(content, embeds, action_row)
        _payload.setdefault("message_reference", {"message_id": self.id})

        if _payload:
            data = await _SendingRestHandler.execute(self.channel.id, _payload, self.session)

            return DisMessage(data, self._t, self.session)

        return None

    async def create_reaction(self, emoji: Union[DisEmoji, str]) -> DisOwnReaction:
        """create_reaction
        Create reaction to message

        Args:
            emoji (Union[DisEmoji, str]): Emoji for reaction

        Returns:
            DisOwnReaction: Your reaction
        """
        if isinstance(emoji, DisEmoji):
            if emoji.type == "custom":
                emoji = f"{emoji.name}:{str(emoji.emoji_id)}"
            elif emoji.type == "normal":
                emoji = emoji.unicode

        await _SendingRestHandler.create_reaction(
            f"/channels/{self.channel.id}/messages/{self.id}/reactions/{emoji}/@me",
            self.session,
        )

        return DisOwnReaction(emoji, self.id, self.channel.id, self._t, self.session)

    async def delete(self):
        """delete
        Delete message
        """
        _u = (
            f"https://discord.com/api/v10/channels/{self.channel.id}/messages/{self.id}"
        )

        await _SendingRestHandler.delete_message(_u, self.session)


class ChannelType:
    """
    Channel types
    """
    text = 0
    dm = 1
    voice = 2  # Not working for full
    dm_group = 3  # Not working for full
    category = 4  # Not working for full
    news = 5  # Not working for full
    news_thread = 10
    public_thread = 11
    private_thread = 12
    stage_voice = 13  # Not working for full
    directory = 14  # Not working for full
    forum = 15  # Not working for full


class Channel:
    """
    Channel class
    """
    def __init__(self, __data: dict, __token, __session):
        def _try(k: str, __t: Optional[type] = None):
            try:
                if __t is not None:
                    return __t(__data[k])
                return __data[k]
            except KeyError:
                return None

        self._t = __token
        self._s = __session

        self.id: int = int(__data['id'])
        self.type: int = __data['type']

        self.guild_id: int = _try('guild_id', int)
        self.position: int = _try('position')

        self.name: str = _try('name')

    async def send(
        self,
        content: Optional[SupportsStr] = None,
        embeds: Optional[List[DisEmbed]] = None,
        action_row: Optional[ActionRow] = None,
    ):
        """
        Send message in channel

        Args:
            content (SupportsStr, optional): Message content (any object supports str() function)
            embeds (List[DisEmbed], optional): Message embeds (For one embed use `[your_embed]`)
            action_row (ActionRow, optional): Action row with components

        Returns:
            Message or None
        """
        _payload = message_payload(str(content), embeds, action_row)

        if _payload:
            data = await _SendingRestHandler.execute(self.id, _payload, self._s)

            return DisMessage(data, self._t, self._s)

        return None

    def fetch(self, message_id: int) -> DisMessage:
        """
        Fetch message in this channel by id

        Args:
            message_id (int): Id of message that is fetching

        Returns:
            Message
        """
        data = _GettingChannelData.fetch(self.id, self._t, message_id)

        return DisMessage(data, self._t, self._s)

    async def delete(self):
        """
        Delete channel
        """
        _u = f"https://discord.com/api/v10/channels/{self.id}"

        await _SendingRestHandler.delete(_u, self._s)

    async def typing(self):
        """
        Show typing indicator in channel
        """
        _u = f"https://discord.com/api/v10/channels/{self.id}/typing"

        await _SendingRestHandler.post_without_payload(_u, self._s)


@final
class DmMessage:
    """
    Message in DM channel
    """

    def __init__(self, data, token, session):
        self.json = data
        self._t = token
        self.session = session

        self.id = data["id"]

        self.content = data["content"]
        
        _channel_data = _GettingChannelData.execute(data['channel_id'], token)
        self.channel = Channel(_channel_data, token, session)

    async def reply(
        self,
        content: Optional[SupportsStr] = None,
        embeds: Optional[List[DisEmbed]] = None,
    ):
        """reply
        Reply to message

        Args:
            content (Optional[Any], optional): Message content (text). Defaults to None.
            embeds (Optional[List[DisEmbed]], optional): Message embeds (DisEmbed objects).
                                                         Defaults to None.
        """
        _d = {
            "content": None,
            "embeds": {},
            "message_reference": {"message_id": self.id},
        }

        content = str(content)

        if content:
            _d["content"] = content

        if embeds:
            embeds_jsons = []

            for i in embeds:
                embeds_jsons.append(_EmbedGenerator(i))

            _d["embeds"] = embeds_jsons

        if not embeds and not content:
            return

        await _SendingRestHandler.execute(self.channel.id, _d, self.session)

    async def create_reaction(self, emoji: Union[DisEmoji, str]) -> DisOwnReaction:
        """create_reaction
        Create reaction in message

        Args:
            emoji (Union[DisEmoji, str]): Emoji for reaction

        Returns:
            DisOwnReaction: Your reaction
        """
        if isinstance(emoji, DisEmoji):
            if emoji.type == "custom":
                emoji = f"{emoji.name}:{str(emoji.emoji_id)}"
            elif emoji.type == "normal":
                emoji = emoji.unicode

        await _SendingRestHandler.create_reaction(
            f"/channels/{self.channel.id}/messages/{self.id}/reactions/{emoji}/@me",
            self.session,
        )

        return DisOwnReaction(emoji, self.id, self.channel.id, self._t, self.session)


class MessageDeleteEvent:
    """
    MESSAGE_DELETE event class with info about event
    """

    def __init__(self, data: dict, token: str, session):
        self.message_id = data["id"]

        _channel_data = _GettingChannelData.execute(data['channel_id'], token)
        self.channel = Channel(_channel_data, token, session)


class DmMessageDeleteEvent:
    """
    MESSAGE_DELETE event class with info about event, but in DM channel
    """

    def __init__(self, data: dict, token: str, session):
        self.message_id = data["id"]

        _channel_data = _GettingChannelData.execute(data['channel_id'], token)
        self.channel = Channel(_channel_data, token, session)
