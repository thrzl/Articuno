"""
Who's that Pokemon command.

(C) 2022 - Jimmy-Blue
"""

import logging
import datetime
import io
import random
import asyncio
import json
import interactions
from interactions.ext.wait_for import wait_for, wait_for_component
import requests
from PIL import Image
from interactions.ext.files import component_edit, command_send


def _pokemon_image(url: str) -> Image.Image:
    """
    Format the Pokemon image from the URL.

    :param url: The URL of the image.
    :type url: str
    :return: The formatted image.
    :rtype: Image
    """

    _resp = requests.get(url)
    if _resp.status_code == 200:
        img = Image.open(io.BytesIO(_resp.content)).convert("RGBA")
        if img.size[0] > 120 and img.size[1] > 240:
            img = img.resize((int(img.width * 2.2), int(img.height * 2.2)))
        else:
            img = img.resize((int(img.width * 3), int(img.height * 3)))

        return img


def _get_pokemon(generation: int = None) -> list:
    """
    Get a random Pokemon from the database.

    :param generation: The generation of the Pokemon.
    :type generation: int
    :return: The Pokemon list.
    :rtype: list
    """

    _pokemon_list = {}
    db = json.loads(open("./db/pokemon.json", "r", encoding="utf8").read())

    if generation is None:
        generation = [1, 905]
    else:
        if generation == "1":
            generation = [1, 151]
        elif generation == "2":
            generation = [152, 251]
        elif generation == "3":
            generation = [252, 386]
        elif generation == "4":
            generation = [387, 493]
        elif generation == "5":
            generation = [494, 649]
        elif generation == "6":
            generation = [650, 721]
        elif generation == "7":
            generation = [722, 809]
        elif generation == "8":
            generation = [810, 905]

    for i in range(4):
        _num = random.randint(generation[0] - 1, generation[1] - 1)
        _val = list(db.values())[_num]

        _pokemon_list[i] = _val

    _lists = {}
    _list_number = []
    for i in range(4):
        if len(_list_number) < 5:
            if i not in _list_number:
                _lists[i] = {
                    "num": _pokemon_list[i]["num"],
                    "name": _pokemon_list[i]["name"],
                }
                _list_number.append(i)
            else:
                continue

    return _lists


class WTP(interactions.Extension):
    """Extension for /whos_that_pokemon command."""

    def __init__(self, client: interactions.Client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command(
        name="whos_that_pokemon",
        description="Who's that Pokemon game.",
        options=[
            interactions.Option(
                type=interactions.OptionType.STRING,
                name="difficulty",
                description="Difficulty of the game",
                choices=[
                    interactions.Choice(name="Easy", value="easy"),
                    interactions.Choice(name="Hard", value="hard"),
                ],
                required=True,
            ),
            interactions.Option(
                type=interactions.OptionType.STRING,
                name="generation",
                description="Generation of the Pokemon",
                choices=[
                    interactions.Choice(name=f"Gen {i}", value=f"{i}")
                    for i in range(1, 9)
                ],
                required=False,
            ),
        ],
    )
    async def whos_that_pokemon(
        self, ctx: interactions.CommandContext, difficulty: str, generation: str = None
    ):
        """Who's that Pokemon game."""

        _pokemon_list = _get_pokemon(generation)

        await ctx.defer()

        _correct_pokemon = _pokemon_list[random.randint(0, 3)]

        _image = _pokemon_image(
            f"https://www.serebii.net/art/th/{_correct_pokemon['num']}.png"
        )

        _black_image = Image.new("RGBA", _image.size, (0, 0, 0))

        bg = Image.open("./img/whos_that_pokemon.png")

        _num = (400, 230)
        text_img = Image.new("RGBA", bg.size, (255, 255, 255, 0))
        text_img.paste(bg, (0, 0))
        text_img.paste(_black_image, _num, _image)

        with io.BytesIO() as out:
            text_img.save(out, format="PNG")
            file = interactions.File(filename="image.png", fp=out.getvalue())

        _text_img = Image.new("RGBA", bg.size, (255, 255, 255, 0))
        _text_img.paste(bg, (0, 0))
        _text_img.paste(_image, _num, _image)

        with io.BytesIO() as out:
            _text_img.save(out, format="PNG")
            _file = interactions.File(filename="_image.png", fp=out.getvalue())

        if difficulty == "easy":

            _button_list = []
            for i in range(4):
                _button_list.append(
                    interactions.Button(
                        style=interactions.ButtonStyle.SECONDARY,
                        label=f"{_pokemon_list[i]['name']}",
                        custom_id=f"{_pokemon_list[i]['num']}",
                    )
                )

            msg = await command_send(
                ctx,
                content="**Who's that Pokemon?**",
                components=_button_list,
                files=file,
            )

            while True:
                try:

                    def check(_ctx: interactions.CommandContext):
                        return (
                            _ctx.data.custom_id == "_wtp"
                            and _ctx.user.id == ctx.user.id
                        )

                    res: interactions.ComponentContext = await wait_for_component(
                        self.client,
                        components=_button_list,
                        messages=int(msg.id),
                        timeout=15,
                    )
                    if int(res.user.id) == int(ctx.user.id):
                        if str(res.custom_id) == str(_correct_pokemon["num"]):

                            _button_disabled = []
                            for i in range(4):
                                _button_disabled.append(
                                    interactions.Button(
                                        style=interactions.ButtonStyle.SECONDARY
                                        if str(_pokemon_list[i]["num"])
                                        != str(_correct_pokemon["num"])
                                        else interactions.ButtonStyle.SUCCESS,
                                        label=f"{_pokemon_list[i]['name']}",
                                        custom_id=f"{_pokemon_list[i]['num']}",
                                        disabled=True,
                                    )
                                )

                            await component_edit(
                                res,
                                content=f"**Who's that Pokemon?**\n\nIt's **{_correct_pokemon['name']}**! {ctx.user.mention} had the right answer.",
                                components=_button_disabled,
                                files=_file,
                                attachments=[],
                            )
                            break

                        else:

                            _button_disabled = []
                            for i in range(4):
                                _button_disabled.append(
                                    interactions.Button(
                                        style=(
                                            interactions.ButtonStyle.SECONDARY
                                            if str(_pokemon_list[i]["num"])
                                            != str(_correct_pokemon["num"])
                                            and str(_pokemon_list[i]["num"])
                                            != str(res.custom_id)
                                            else (
                                                interactions.ButtonStyle.DANGER
                                                if str(_pokemon_list[i]["num"])
                                                == str(res.custom_id)
                                                else interactions.ButtonStyle.SUCCESS
                                            )
                                        ),
                                        label=f"{_pokemon_list[i]['name']}",
                                        custom_id=f"{_pokemon_list[i]['num']}",
                                        disabled=True,
                                    )
                                )

                            _action_rows = [
                                interactions.ActionRow(components=_button_disabled),
                                interactions.ActionRow(
                                    components=[
                                        interactions.Button(
                                            style=interactions.ButtonStyle.LINK,
                                            label=f"{_correct_pokemon['name']} (Bulbapedia)",
                                            url=f"https://bulbapedia.bulbagarden.net/wiki/{_correct_pokemon['name']}_(Pokémon)",
                                        )
                                    ]
                                ),
                            ]

                            await component_edit(
                                res,
                                content=f"**Who's that Pokemon?**\n\nIt's **{_correct_pokemon['name']}**! {ctx.user.mention} had the wrong answer.",
                                components=_button_disabled,
                                files=_file,
                                attachments=[],
                            )
                            break

                except asyncio.TimeoutError:

                    _button_disabled = []
                    for i in range(4):
                        _button_disabled.append(
                            interactions.Button(
                                style=interactions.ButtonStyle.SECONDARY,
                                label=f"{_pokemon_list[i]['name']}",
                                custom_id=f"{_pokemon_list[i]['num']}",
                                disabled=True,
                            )
                        )

                    _action_rows = [
                        interactions.ActionRow(components=_button_disabled),
                        interactions.ActionRow(
                            components=[
                                interactions.Button(
                                    style=interactions.ButtonStyle.LINK,
                                    label=f"{_correct_pokemon['name']} (Bulbapedia)",
                                    url=f"https://bulbapedia.bulbagarden.net/wiki/{_correct_pokemon['name']}_(Pokémon)",
                                )
                            ]
                        ),
                    ]

                    await msg.edit(
                        content=f"**Who's that Pokemon?**\n\nTimeout! It's **{_correct_pokemon['name']}**!",
                        components=_action_rows,
                        attachments=[],
                        files=_file,
                    )
                    break

        elif difficulty == "hard":

            button = interactions.Button(
                style=interactions.ButtonStyle.SECONDARY,
                label="Answer",
                custom_id="answer",
            )
            msg = await ctx.send(
                content="**Who's that Pokemon?**", components=[button], files=file
            )

            while True:
                try:

                    def check(_ctx: interactions.CommandContext):
                        return (
                            _ctx.data.custom_id == "answer"
                            and _ctx.user.id == ctx.user.id
                        )

                    res = await wait_for_component(
                        self.client,
                        components=[button],
                        messages=int(msg.id),
                        timeout=15,
                    )
                    if int(res.user.id) == int(ctx.user.id):

                        modal = interactions.Modal(
                            title="Who's that Pokemon?",
                            custom_id="_wtp",
                            components=[
                                interactions.TextInput(
                                    style=interactions.TextStyleType.SHORT,
                                    label="Your answer",
                                    placeholder="Ex: Pikachu ⚠ (Do not hit Cancel)",
                                    custom_id="_answer",
                                    max_length=100,
                                ),
                            ],
                        )

                        await res.popup(modal)

                        def check(_ctx: interactions.CommandContext):
                            return (
                                _ctx.data.custom_id == "_wtp"
                                and _ctx.user.id == ctx.user.id
                            )

                        _res = await wait_for(
                            self.client, "on_modal", check=check, timeout=15
                        )
                        _answer = _res.data._json["components"][0].get("components")[0][
                            "value"
                        ]

                        if _answer.lower().rstrip() == _correct_pokemon["name"].lower():

                            _button_disabled = interactions.Button(
                                style=interactions.ButtonStyle.SECONDARY,
                                label="Answer",
                                custom_id="answer",
                                disabled=True,
                            )

                            await component_edit(
                                _res,
                                content=f"**Who's that Pokemon?**\n\nIt's **{_correct_pokemon['name']}**! {ctx.user.mention} had the right answer.",
                                components=[_button_disabled],
                                files=_file,
                                attachments=[],
                            )
                            break

                        else:

                            _action_rows = [
                                interactions.ActionRow(
                                    components=[
                                        interactions.Button(
                                            style=interactions.ButtonStyle.SECONDARY,
                                            label="Answer",
                                            custom_id="answer",
                                            disabled=True,
                                        )
                                    ]
                                ),
                                interactions.ActionRow(
                                    components=[
                                        interactions.Button(
                                            style=interactions.ButtonStyle.LINK,
                                            label=f"{_correct_pokemon['name']} (Bulbapedia)",
                                            url=f"https://bulbapedia.bulbagarden.net/wiki/{_correct_pokemon['name']}_(Pokémon)",
                                        )
                                    ]
                                ),
                            ]

                            await component_edit(
                                _res,
                                content=f"**Who's that Pokemon?**\n\nIt's **{_correct_pokemon['name']}**! {ctx.user.mention} had the wrong answer.",
                                components=_action_rows,
                                files=_file,
                                attachments=[],
                            )
                            break

                except asyncio.TimeoutError:

                    _action_rows = [
                        interactions.ActionRow(
                            components=[
                                interactions.Button(
                                    style=interactions.ButtonStyle.SECONDARY,
                                    label="Answer",
                                    custom_id="answer",
                                    disabled=True,
                                )
                            ]
                        ),
                        interactions.ActionRow(
                            components=[
                                interactions.Button(
                                    style=interactions.ButtonStyle.LINK,
                                    label=f"{_correct_pokemon['name']} (Bulbapedia)",
                                    url=f"https://bulbapedia.bulbagarden.net/wiki/{_correct_pokemon['name']}_(Pokémon)",
                                )
                            ]
                        ),
                    ]

                    await msg.edit(
                        content=f"**Who's that Pokemon?**\n\nTimeout! It's **{_correct_pokemon['name']}**!",
                        components=_action_rows,
                        attachments=[],
                        files=_file,
                    )
                    break


def setup(client) -> None:
    """Setup the extension."""
    log_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime(
        "%d/%m/%Y %H:%M:%S"
    )
    WTP(client)
    logging.debug("""[%s] Loaded WTP extension.""", log_time)
