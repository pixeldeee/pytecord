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

from typing import (
    Union,
    Optional,
    Any,
    NoReturn,
    ClassVar,
    Callable,
    final,
    List,
    Tuple,
    Literal
)
from json import dumps
from abc import ABC, abstractmethod
import aiohttp

from disspy.jsongenerators import _OptionGenerator
from disspy.ui import ActionRow

__all__: tuple = (
    "ApplicationCommandType",
    "ApplicationCommand",
    "Option",
    "OptionType",
    "SlashCommand",
    "UserCommand",
    "MessageCommand",
    "Context",
    "OptionArgs"
)


def describe(description: str):
    def wrapper(func):
        try:
            to_edit = {"description": description}
            
            for key in list(func[0].keys()):
                val = func[0][key]

                to_edit.setdefault(key, val)
            
            return (to_edit, func[1])
        except TypeError:
            return ({"description": description}, func)
    return wrapper


class _OptionsMethods:
    @staticmethod
    def describe(**kwargs):
        def wrapper(func):
            result = []

            for name in list(kwargs.keys()):
                value: Option = kwargs[name]

                result.append({
                    "name": name,
                    "type": value.option_type,
                    "description": value.description,
                    "required": value.is_required,
                    "choices": value.choices
                })
            try:
                to_edit = {"options": result}
                
                for key in list(func[0].keys()):
                    val = func[0][key]

                    to_edit.setdefault(key, val)
                
                return (to_edit, func[1])
            except TypeError:
                return ({"options": result}, func)

        return wrapper

options = _OptionsMethods()


@final
class _MessageFlags:
    """
    Flags for messages in discord API. Variables are constants.

    This use in send() method of Context class.
    """
    CROSSPOSTED: ClassVar[int] = 1 << 0
    IS_CROSSPOST: ClassVar[int] = 1 << 1
    SUPPRESS_EMBEDS: ClassVar[int] = 1 << 2
    SOURCE_MESSAGE_DELETED: ClassVar[int] = 1 << 3
    URGENT: ClassVar[int] = 1 << 4
    HAS_THREAD: ClassVar[int] = 1 << 5
    EPHEMERAL: ClassVar[int] = 1 << 6
    LOADING: ClassVar[int] = 1 << 7
    FAILED_TO_MENTION_SOME_ROLES_IN_THREAD: ClassVar[int] = 1 << 8


class _SendingRestHandler:
    @staticmethod
    async def execute(url, payload, token):
        """execute()

        Args:
            url (str): Url for post
            payload (_type_): Json payload for post
            token (_type_): Bot token for headers

        Returns:
            _type_: _description_
        """
        async with aiohttp.ClientSession(headers={'Authorization': f'Bot {token}',
                                                  'content-type': 'application/json'}) as session:
            try:
                async with session.post(url, data=dumps(payload)) as data:
                    j = await data.json()

                    return j
            except aiohttp.ContentTypeError:
                await session.post(url, data=dumps(payload))


@final
class ApplicationCommandType:
    """
    Application command types (see discord docs)
    """
    TEXT_INPUT: ClassVar[int] = 1  # Slash Command
    USER: ClassVar[int] = 2  # User Command
    MESSAGE: ClassVar[int] = 3  # Message Command


class ApplicationCommand(ABC):
    """
    (abstract)
    Application Command object.

    This use as parent for slash commands, message commands, user commands
    """

    def __init__(self, name: str, cmd: Callable, command_type: int) -> NoReturn:
        self.name: str = name
        self.cmd: Callable = cmd
        self.command_type: int = command_type

    @abstractmethod
    def json(self) -> dict:
        """json
        Return json data of command

        Returns:
            dict: Json data
        """
        return


class Option:
    """
    Class for using options in application commands (TEXT_INPUT)
    """

    def __init__(self, option_type: int) -> None:
        """__init__
        Create option object

        Args:
            option_type (int): Option type

        Returns:
            None
        """
        self.description: str = "No description"
        self.option_type: int = option_type
        self.choices: Union[List[dict], None] = []
        self.is_required: bool = False
    
    def required(self):
        option = Option(self.option_type)
        option.is_required = True
        option.choices = self.choices
        option.description = self.description

        return option

    def set_description(self, text: str):
        option = Option(self.option_type)
        option.is_required = self.is_required
        option.choices = self.choices
        option.description = text

        return option

    def set_choices(self, choices: List[dict]):
        option = Option(self.option_type)
        option.is_required = self.is_required
        option.choices = choices
        option.description = self.description

        return option


@final
class OptionType:
    """
    Option types (see discord docs)
    """
    SUB_COMMAND: Literal[1] = 1
    SUB_COMMAND_GROUP: Literal[2] = 2
    STRING: Literal[3] = 3
    INTEGER: Literal[4] = 4
    BOOLEAN: Literal[5] = 5
    USER: Literal[6] = 6
    CHANNEL: Literal[7] = 7
    ROLE: Literal[8] = 8
    MENTIONABLE: Literal[9] = 9
    NUMBER: Literal[10] = 10
    ATTACHMENT: Literal[11] = 11


@final
class StrOption(Option):
    def __init__(self) -> None:
        super().__init__(OptionType.STRING)


@final
class IntOption(Option):
    def __init__(self) -> None:
        super().__init__(OptionType.INTEGER)


@final
class NumOption(Option):
    def __init__(self) -> None:
        super().__init__(OptionType.NUMBER)


class BoolOption(Option):
    def __init__(self) -> None:
        super().__init__(OptionType.BOOLEAN)


@final
class UserOption(Option):
    def __init__(self) -> None:
        super().__init__(OptionType.USER)


@final
class ChannelOption(Option):
    def __init__(self) -> None:
        super().__init__(OptionType.CHANNEL)


@final
class SlashCommand(ApplicationCommand):
    """
    Application Command with type number 1 (TEXT_INPUT)
    """

    def __init__(self, name: str, description: str, cmd: Callable,
                 options: Optional[List[Option]] = None) -> NoReturn:
        super().__init__(name, cmd, ApplicationCommandType.TEXT_INPUT)

        self.description = description

        if options:
            _options_jsons = []

            for option in options:
                _options_jsons.append(_OptionGenerator(option))

            self.options: Union[List[Option], None] = _options_jsons
        else:
            self.options: Union[List[Option], None] = None

    def json(self) -> dict:
        """json
        Return json data of command

        Returns:
            dict: Json data
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": ApplicationCommandType.TEXT_INPUT,
            "options": self.options
        }


@final
class UserCommand(ApplicationCommand):
    """
    Application Command with type number 2 (USER)
    """

    def __init__(self, name: str, cmd: Callable) -> NoReturn:
        super().__init__(name, cmd, ApplicationCommandType.USER)

    def json(self) -> dict:
        """json
        Return json data of command

        Returns:
            dict: Json data
        """
        return {
            "name": self.name,
            "type": ApplicationCommandType.USER
        }


@final
class MessageCommand(ApplicationCommand):
    """
    Application Command with type number 3 (MESSAGE)
    """

    def __init__(self, name: str, cmd: Callable) -> NoReturn:
        super().__init__(name, cmd, ApplicationCommandType.MESSAGE)

    def json(self) -> dict:
        """json
        Return json data of command

        Returns:
            dict: Json data
        """
        return {
            "name": self.name,
            "type": ApplicationCommandType.MESSAGE
        }


@final
class _Argument:
    def __init__(self, name: str, option_type: int, value: Any) -> NoReturn:
        self.name: str = name
        self.type: int = option_type
        self.value: Any = value


@final
class OptionArgs:
    """
    Class for receiving option values in interactions

    Example
    @bot.slash_command("Test", "Wow", options=[Option("Hi", "lol", OptionType.STRING)])
    async def test(ctx: Context, args: OptionArgs):
        await ctx.send(args.getString("Hi"))
    """

    def __init__(self, values: Optional[List[_Argument]] = None) -> NoReturn:
        """
        Init object
        -----
        :param values: Option Values
        """
        if values is None:
            values = []
        self._v: List[_Argument] = values

    def isempty(self) -> bool:
        """
        Returns True or False when is empty is True or False

        :return bool: Is empty?
        """
        return len(self._v) == 0
    
    @property
    def options_args(self) -> List[_Argument]:
        return self._v

    def get(self, name: str) -> Union[Any, None]:
        """
        Get value from name

        :param name: Name of option
        :return Any: Option value
        """
        for _a in self._v:
            if _a.name == name:
                return _a.value
        return None

    def get_string(self, name: str) -> Union[str, None]:
        """
        Get string value from name

        :param name: Name of option
        :return str: Option value (always string)
        """
        for _a in self._v:
            if _a.name == name and _a.type == OptionType.STRING:
                return str(_a.value)
        return None

    def get_integer(self, name: str) -> Union[int, None]:
        """
        Get integer value from na1me

        :param name: Name of option
        :return int: Option value (always integer)
        """
        for _a in self._v:
            if _a.name == name and _a.type == OptionType.INTEGER:
                return int(_a.value)
        return None

    def get_number(self, name: str) -> Union[int, None]:
        """
        Get number value from name

        :param name: Name of option
        :return int: Option value (always integer)
        """
        for _a in self._v:
            if _a.name == name and _a.type == OptionType.NUMBER:
                return int(_a.value)
        return None

    def get_boolean(self, name: str) -> Union[bool, None]:
        """
        Get boolean value from name

        :param name: Name of option
        :return bool: Option value (always boolean)
        """
        for _a in self._v:
            if _a.name == name and _a.type == OptionType.BOOLEAN:
                return bool(_a.value)
        return None


@final
class Context:
    """
    Class for receiving interaction content and sending messages to users

    There are some methods for responding to interaction (Slash Command)
    """

    def __init__(self, interaction_info:Tuple[str, int], bot_token,
                 args: OptionArgs = None) -> NoReturn:
        self._interaction_token: str = str(list(interaction_info)[0])
        self._interaction_id: int = int(list(interaction_info)[1])

        self._t = bot_token
        self.args = args

    async def send(self, content: str, action_row: Optional[ActionRow] = None,
                   ephemeral: bool = False) -> NoReturn:
        """

        :param content: (str) Message content
        :param ephemeral: (bool) Sets message invisible for other member (not author)
        :return None:
        """
        _payload = {}

        if ephemeral:
            if action_row:
                _payload = {
                    "type": 4,
                    "data": {
                        "content": content,
                        "flags": _MessageFlags.EPHEMERAL,
                        "components": action_row.json
                    }
                }
            else:
                _payload = {
                    "type": 4,
                    "data": {
                        "content": content,
                        "flags": _MessageFlags.EPHEMERAL
                    }
                }
        else:
            if action_row:
                _payload = {
                    "type": 4,
                    "data": {
                        "content": content,
                        "components": action_row.json
                    }
                }
            else:
                _payload = {
                    "type": 4,
                    "data": {
                        "content": content
                    }
                }

        _id = self._interaction_id
        _token = self._interaction_token

        _url = f"https://discord.com/api/v10/interactions/{_id}/{_token}/callback"

        await _SendingRestHandler.execute(_url, _payload, self._t)

    async def send_modal(self, title: str, custom_id: str, action_row: ActionRow):
        """send_modal()

        Args:
            title (str): Title of modal
            custom_id (str): Custom id of modal
            action_row (ActionRow): Action row with components for modal
        """
        _payload = {
            "type": 9,
            "data": {
                "title": title,
                "custom_id": custom_id,
                "components": action_row.json
            }
        }

        _id = self._interaction_id
        _token = self._interaction_token

        _url = f"https://discord.com/api/v10/interactions/{_id}/{_token}/callback"

        await _SendingRestHandler.execute(_url, _payload, self._t)
