"""
An extension library for interactions.py to create transcripts.
Copyright (C) 2022 ItsRqtl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import html
import io
import os
from datetime import datetime, timedelta

import pandas as pd
import pytz

from interactions import (
    Channel,
    ComponentType,
    Extension,
    Guild,
    Message,
    MessageType,
    Sticker,
)

from .cache import clear_cache
from .emoji_convert import convert_emoji
from .utils import (
    Default,
    get_file_icon,
    get_file_size,
    parse_embed,
    parse_emoji,
    parse_md,
    parse_msg_ref,
    styles,
)

newline = "\n"
dir_path = os.path.abspath((os.path.dirname(os.path.realpath(__file__))))


class Transcript(Extension):
    def __init__(self, client):
        self.client = client


async def get_transcript(
    channel: Channel,
    limit: int = 100,
    pytz_timezone="UTC",
    military_time: bool = False,
    fancy_time: bool = True,
    mode: str = "html",
):
    """
    :param channel: The channel to get the transcript from
    :param limit: The maximum number of messages to get
    :param pytz_timezone: The timezone to use for the transcript
    :param military_time: Whether to use military time or not
    :param fancy_time: Whether to use fancy time or not (only with html mode)
    :param mode: The mode to use for the transcript (html, json, csv, or plain)
    :return: A string of the transcript
    """

    msg = await channel.get_history(limit=limit)
    msg.reverse()

    guild = Guild(**await channel._client.get_guild(channel.guild_id))

    if mode == "plain":
        content = "==============================================================\nGuild: {}\nChannel: {}\n==============================================================\n".format(
            guild.name, channel.name
        )
        for i in msg:
            if military_time:
                time = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                    "%d-%b-%y %H:%M:%S"
                )
                edit_time = (
                    i.edited_timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                        "%d-%b-%y %H:%M:%S"
                    )
                    if i.edited_timestamp
                    else None
                )
            else:
                time = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                    "%d-%b-%y %I:%M:%S%p"
                )
                edit_time = (
                    i.edited_timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                        "%d-%b-%y %I:%M:%S%p"
                    )
                    if i.edited_timestamp
                    else None
                )
            content += "\n[{}] {} ({})\n{}".format(
                time,
                i.author.username + "#" + i.author.discriminator,
                i.author.id,
                i.content,
            )
            if i.embeds:
                content += "\n{Embed}"
                for e in i.embeds:
                    content += f"{newline}{f'{newline}{e.author.url}' if e.author and e.author.url else ''}{f'{newline}{e.author.name}' if e.author and e.author.name else ''}{f'{newline}{e.title}' if e.title else ''}{f'{newline}{e.description}' if e.description else ''}{''.join([f'{newline}{f.name}{newline}{f.value}' for f in e.fields]) if e.fields else ''}{f'{newline}{e.thumbnail.url}' if e.thumbnail else ''}{f'{newline}{e.image.url}' if e.image else ''}"
            if i.attachments:
                content += "\n{Attachments}"
                for a in i.attachments:
                    content += f"{newline}{a.url}"
            if i.sticker_items:
                content += "\n{Stickers}"
                for s in i.sticker_items:
                    if s.format_type == 3:
                        sticker = Sticker(
                            **await channel._client.get_sticker(i.sticker_items[0].id)
                        )
                        content += f"{newline}https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/stickers/{sticker.pack_id}/{sticker.id}.gif"
                    else:
                        content += f"{newline}https://media.discordapp.net/stickers/{s.id}.png"
            if i.reactions:
                content += "\n{Reactions}"
                for r in i.reactions:
                    content += f"{newline}{r.emoji} - {r.count}"
            if not content.endswith("\n\n"):
                content += "\n"
                if not content.startswith("\n"):
                    content += "\n"
        content += "==============================================================\nExported {} messages.\n==============================================================".format(
            len(msg)
        )
        return content

    elif mode == "csv" or mode == "json":
        data = []
        for i in msg:
            if military_time:
                time = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                    "%d-%b-%y %H:%M:%S"
                )
                edit_time = (
                    i.edited_timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                        "%d-%b-%y %H:%M:%S"
                    )
                    if i.edited_timestamp
                    else None
                )
            else:
                time = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                    "%d-%b-%y %I:%M:%S%p"
                )
                edit_time = (
                    i.edited_timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                        "%d-%b-%y %I:%M:%S%p"
                    )
                    if i.edited_timestamp
                    else None
                )
            data.append(
                {
                    "Guild": {"name": guild.name, "id": str(guild.id)},
                    "Channel": {"name": channel.name, "id": str(channel.id)},
                    "Metadata": {"id": str(i.id)},
                    "Author": {
                        "username": i.author.username + "#" + i.author.discriminator,
                        "id": str(i.author.id),
                    },
                    "Time": time,
                    "Edited": edit_time,
                    "Content": i.content,
                    "Embeds": [
                        {
                            "title": e.title,
                            "description": e.description,
                            "author": {
                                "name": e.author.name,
                                "url": e.author.url,
                                "icon": e.author.icon_url,
                            }
                            if e.author
                            else {},
                            "thumbnail": e.thumbnail.url if e.thumbnail else None,
                            "image": e.image.url if e.image else None,
                            "fields": [
                                {"name": f.name, "value": f.value, "inline": f.inline}
                                for f in e.fields
                            ]
                            if e.fields
                            else [],
                        }
                        for e in i.embeds
                    ]
                    if i.embeds
                    else [],
                    "Attachments": [a.url for a in i.attachments] if i.attachments else [],
                    "Stickers": [
                        {"name": s.name, "id": str(s.id), "format": s.format_type}
                        for s in i.sticker_items
                    ]
                    if i.sticker_items
                    else [],
                    "Reactions": [
                        {"name": r.emoji.name, "id": str(r.emoji.id), "count": r.count}
                        for r in i.reactions
                    ]
                    if i.reactions
                    else [],
                }
            )
        df = pd.DataFrame(data)
        if mode == "csv":
            df.to_csv(file := io.StringIO(), index=True, header=True)
            return file.getvalue()
        elif mode == "json":
            df.to_json(file := io.StringIO(), index=True, orient="records")
            return file.getvalue()

    elif mode == "html":
        time_format = "%A, %e %B %Y at %H:%M" if military_time else "%A, %e %B %Y at %I:%M %p"
        previous = None
        data = ""
        metadata = {}
        for i in msg:
            current = i
            create = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(time_format)
            edit = (
                i.edited_timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(time_format)
                if i.edited_timestamp
                else None
            )
            if i.type == MessageType.CHANNEL_PINNED_MESSAGE:
                data += "</div>" if previous is not None else ""
                with open(dir_path + "/html/messag/pin.html", "r") as f:
                    rawhtml = f.read()
                rawhtml = rawhtml.replace("{{PIN_URL}}", Default.pinned_message_icon)
                rawhtml = rawhtml.replace(
                    "{{USER_COLOUR}}",
                    await parse_md(
                        f"color: {hex(i.author.accent_color)[2:] if i.author.accent_color else '000000'}",
                        channel,
                        tz=pytz_timezone,
                    ),
                )
                rawhtml = rawhtml.replace(
                    "{{NAME}}",
                    await parse_md(str(html.escape(i.author.username)), channel, tz=pytz_timezone),
                )
                rawhtml = rawhtml.replace(
                    "{{NAME_TAG}}", f"{i.author.username}#{i.author.discriminator}"
                )
                rawhtml = rawhtml.replace("{{MESSAGE_ID}}", str(i.id))
                rawhtml = rawhtml.replace(
                    "{{REF_MESSAGE_ID}}", str(i.referenced_message.message_id)
                )
                data += rawhtml

            elif i.type == MessageType.THREAD_CREATED:
                data += "</div>" if previous is not None else ""
                with open(dir_path + "/html/message/thread.html", "r") as f:
                    rawhtml = f.read()
                rawhtml = rawhtml.replace("{{THREAD_URL}}", Default.thread_channel_icon)
                rawhtml = rawhtml.replace("{{THREAD_NAME}}", i.content)
                rawhtml = rawhtml.replace(
                    "{{USER_COLOUR}}",
                    await parse_md(
                        f"color: {hex(i.author.accent_color)[2:] if i.author.accent_color else '000000'}",
                        channel,
                        tz=pytz_timezone,
                    ),
                )
                rawhtml = rawhtml.replace(
                    "{{NAME}}",
                    await parse_md(str(html.escape(i.author.username)), channel, tz=pytz_timezone),
                )
                rawhtml = rawhtml.replace(
                    "{{NAME_TAG}}", f"{i.author.username}#{i.author.discriminator}"
                )
                rawhtml = rawhtml.replace("{{MESSAGE_ID}}", str(i.id))
                data += rawhtml

            else:
                msg_content = ""
                if i.content:
                    with open(dir_path + "/html/message/content.html", "r") as f:
                        rawhtml = f.read()
                    rawhtml = rawhtml.replace(
                        "{{MESSAGE_CONTENT}}",
                        await parse_md(str(html.escape(i.content)), channel, tz=pytz_timezone),
                    )
                    rawhtml = rawhtml.replace(
                        "{{EDIT}}",
                        f'<span class="chatlog__reference-edited-timestamp" title="{i.edited_timestamp}">(edited)</span>'
                        if edit
                        else "",
                    )
                    msg_content = rawhtml
                if not i.referenced_message:
                    referenced_message = ""
                else:
                    if not (
                        ref := await channel._client.get_message(
                            channel.id,
                            int(i.referenced_message._json["id"]),
                        )
                    ):
                        with open(dir_path + "/html/message/reference_unknown.html", "r") as f:
                            rawhtml = f.read()
                        referenced_message = rawhtml
                    else:
                        ref = Message(**ref)
                        if not ref.content:
                            ref.content = "Click to see attachment"
                        with open(dir_path + "/html/message/reference.html", "r") as f:
                            rawhtml = f.read()
                        rawhtml = rawhtml.replace("{{AVATAR_URL}}", ref.author.avatar_url)
                        rawhtml = rawhtml.replace(
                            "{{BOT_TAG}}",
                            '<span class="chatlog__bot-tag">BOT</span>' if ref.author.bot else "",
                        )
                        rawhtml = rawhtml.replace(
                            "{{NAME}}",
                            await parse_md(
                                str(html.escape(ref.author.username)), channel, tz=pytz_timezone
                            ),
                        )
                        rawhtml = rawhtml.replace(
                            "{{NAME_TAG}}",
                            f"{ref.author.username}#{ref.author.discriminator}",
                        )
                        rawhtml = rawhtml.replace(
                            "{{USER_COLOUR}}",
                            await parse_md(
                                f"color: {hex(ref.author.accent_color)[2:] if ref.author.accent_color else '000000'}",
                                channel,
                                tz=pytz_timezone,
                            ),
                        )
                        rawhtml = rawhtml.replace(
                            "{{CONTENT}}",
                            await parse_msg_ref(ref.content, channel, tz=pytz_timezone),
                        )
                        rawhtml = rawhtml.replace(
                            "{{EDIT}}",
                            f'<span class="chatlog__reference-edited-timestamp" title="{i.edited_timestamp}">(edited)</span>'
                            if edit
                            else "",
                        )
                        rawhtml = rawhtml.replace(
                            "{{ATTACHMENT_ICON}}",
                            Default.reference_attachment_icon
                            if ref.embeds or ref.attachments
                            else "",
                        )
                        rawhtml = rawhtml.replace("{{MESSAGE_ID}}", str(ref.id))
                        referenced_message = rawhtml

                if i.sticker_items:
                    if i.sticker_items[0].format_type == 3:
                        sticker = Sticker(
                            **await channel._client.get_sticker(i.sticker_items[0].id)
                        )
                        url = f"https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/stickers/{sticker.pack_id}/{sticker.id}.gif"
                    else:
                        url = f"https://media.discordapp.net/stickers/{i.sticker_items[0].id}.png"

                    with open(dir_path + "/html/attachment/image.html", "r") as f:
                        rawhtml = f.read()
                    rawhtml = rawhtml.replace("{{ATTACH_URL}}", str(url))
                    rawhtml = rawhtml.replace("{{ATTACH_URL_THUMB}}", str(url))
                    msg_content = rawhtml

                embeds = ""
                if i.embeds:
                    for e in i.embeds:
                        (r, g, b) = (
                            tuple(int(hex(e.color).lstrip("0x")[i : i + 2], 16) for i in (0, 2, 4))
                            if e.color
                            else (0x20, 0x22, 0x25)
                        )

                        title = ""
                        if e.title:
                            with open(dir_path + "/html/embed/title.html", "r") as f:
                                rawhtml = f.read()
                            rawhtml = rawhtml.replace(
                                "{{EMBED_TITLE}}",
                                await parse_md(e.title, channel, tz=pytz_timezone),
                            )
                            title = rawhtml

                        description = ""
                        if e.description:
                            with open(dir_path + "/html/embed/description.html", "r") as f:
                                rawhtml = f.read()
                            rawhtml = rawhtml.replace(
                                "{{EMBED_DESC}}",
                                await parse_embed(e.description, channel, tz=pytz_timezone),
                            )
                            description = rawhtml

                        fields = ""
                        if e.fields:
                            for field in e.fields:
                                if field.inline:
                                    with open(dir_path + "/html/embed/field-inline.html", "r") as f:
                                        rawhtml = f.read()
                                else:
                                    with open(dir_path + "/html/embed/field.html", "r") as f:
                                        rawhtml = f.read()
                                rawhtml = rawhtml.replace(
                                    "{{FIELD_NAME}}",
                                    await parse_md(field.name, channel, tz=pytz_timezone),
                                )
                                rawhtml = rawhtml.replace(
                                    "{{FIELD_VALUE}}",
                                    await parse_embed(field.value, channel, tz=pytz_timezone),
                                )
                                fields += rawhtml

                        author = ""
                        if e.author:
                            author = e.author.name if e.author.name else ""
                            author = (
                                f'<a class="chatlog__embed-author-name-link" href="{e.author.url}">{author}</a>'
                                if e.author.url
                                else author
                            )
                            author_icon = ""
                            if e.author.icon_url:
                                with open(dir_path + "/html/embed/author_icon.html", "r") as f:
                                    rawhtml = f.read()
                                rawhtml = rawhtml.replace("{{AUTHOR}}", author)
                                rawhtml = rawhtml.replace("{{AUTHOR_ICON}}", e.author.icon_url)
                                author_icon = rawhtml

                            if author_icon == "" and author != "":
                                with open(dir_path + "/html/embed/author.html", "r") as f:
                                    rawhtml = f.read()
                                rawhtml = rawhtml.replace("{{AUTHOR}}", author)
                                author = rawhtml
                            else:
                                author = author_icon

                        image = ""
                        if e.image:
                            with open(dir_path + "/html/embed/image.html", "r") as f:
                                rawhtml = f.read()
                            rawhtml = rawhtml.replace("{{EMBED_IMAGE}}", e.image.proxy_url)
                            image = rawhtml

                        thumbnail = ""
                        if e.thumbnail:
                            with open(dir_path + "/html/embed/thumbnail.html", "r") as f:
                                rawhtml = f.read()
                            rawhtml = rawhtml.replace("{{EMBED_THUMBNAIL}}", e.thumbnail.url)
                            thumbnail = rawhtml

                        footer = ""
                        if e.footer:
                            footer = e.footer.text if e.footer.text else ""
                            icon = e.footer.icon_url if e.footer.icon_url else None

                            if icon is not None:
                                with open(dir_path + "/html/embed/footer_image.html", "r") as f:
                                    rawhtml = f.read()
                                rawhtml = rawhtml.replace("{{EMBED_FOOTER}}", footer)
                                rawhtml = rawhtml.replace("{{EMBED_FOOTER_ICON}}", icon)
                            else:
                                with open(dir_path + "/html/embed/footer.html", "r") as f:
                                    rawhtml = f.read()
                                rawhtml = rawhtml.replace("{{EMBED_FOOTER}}", footer)
                            footer = rawhtml

                        with open(dir_path + "/html/embed/body.html", "r") as f:
                            rawhtml = f.read()
                        rawhtml = rawhtml.replace("{{EMBED_R}}", str(r))
                        rawhtml = rawhtml.replace("{{EMBED_G}}", str(g))
                        rawhtml = rawhtml.replace("{{EMBED_B}}", str(b))
                        rawhtml = rawhtml.replace("{{EMBED_AUTHOR}}", author)
                        rawhtml = rawhtml.replace("{{EMBED_TITLE}}", title)
                        rawhtml = rawhtml.replace("{{EMBED_IMAGE}}", image)
                        rawhtml = rawhtml.replace("{{EMBED_THUMBNAIL}}", thumbnail)
                        rawhtml = rawhtml.replace("{{EMBED_DESC}}", description)
                        rawhtml = rawhtml.replace("{{EMBED_FIELDS}}", fields)
                        rawhtml = rawhtml.replace("{{EMBED_FOOTER}}", footer)
                        embeds += rawhtml

                attachments = ""
                if i.attachments:
                    for a in i.attachments:
                        if a.content_type is None or (
                            "image" not in a.content_type
                            and "video" not in a.content_type
                            and "audio" not in a.content_type
                        ):
                            with open(dir_path + "/html/attachment/message.html", "r") as f:
                                rawhtml = f.read()
                            rawhtml = rawhtml.replace("{{ATTACH_ICON}}", get_file_icon(a.url))
                            rawhtml = rawhtml.replace("{{ATTACH_URL}}", str(a.url))
                            rawhtml = rawhtml.replace(
                                "{{ATTACH_BYTES}}", str(get_file_size(a.size))
                            )
                            rawhtml = rawhtml.replace("{{ATTACH_FILE}}", str(a.filename))

                        else:
                            if "image" in a.content_type:
                                with open(dir_path + "/html/attachment/image.html", "r") as f:
                                    rawhtml = f.read()
                                rawhtml = rawhtml.replace("{{ATTACH_URL}}", str(a.proxy_url))
                                rawhtml = rawhtml.replace("{{ATTACH_URL_THUMB}}", str(a.proxy_url))
                            elif "video" in a.content_type:
                                with open(dir_path + "/html/attachment/video.html", "r") as f:
                                    rawhtml = f.read()
                                rawhtml = rawhtml.replace("{{ATTACH_URL}}", str(a.proxy_url))
                            elif "audio" in a.content_type:
                                with open(dir_path + "/html/attachment/audio.html", "r") as f:
                                    rawhtml = f.read()
                                rawhtml = rawhtml.replace(
                                    "{{ATTACH_ICON}}", Default.file_attachment_audio
                                )
                                rawhtml = rawhtml.replace("{{ATTACH_URL}}", str(a.url))
                                rawhtml = rawhtml.replace(
                                    "{{ATTACH_BYTES}}", str(get_file_size(a.size))
                                )
                                rawhtml = rawhtml.replace("{{ATTACH_AUDIO}}", str(a.proxy_url))
                                rawhtml = rawhtml.replace("{{ATTACH_FILE}}", str(a.filename))
                        attachments += rawhtml

                components = ""
                menu_div_id = 0
                if i.components:
                    for r in i.components:
                        for c in r.components:
                            if c.type == ComponentType.BUTTON:
                                with open(
                                    dir_path + "/html/component/component_button.html",
                                    "r",
                                ) as f:
                                    rawhtml = f.read()
                                rawhtml = rawhtml.replace(
                                    "{{DISABLED}}",
                                    "chatlog__component-disabled" if c.disabled else "",
                                )
                                rawhtml = rawhtml.replace("{{URL}}", c.url if c.url else "")
                                rawhtml = rawhtml.replace(
                                    "{{LABEL}}",
                                    await parse_md(
                                        c.label if c.label else "", channel, tz=pytz_timezone
                                    ),
                                )
                                rawhtml = rawhtml.replace(
                                    "{{EMOJI}}",
                                    await parse_emoji(
                                        str(c.emoji) if c.emoji else ""
                                    ),
                                )
                                rawhtml = rawhtml.replace(
                                    "{{ICON}}",
                                    Default.button_external_link if c.url else "",
                                )
                                rawhtml = rawhtml.replace("{{STYLE}}", styles[c.style.name.lower()])
                                components += f'<div class="chatlog__components">{rawhtml}</div>'

                            elif c.type == ComponentType.SELECT:
                                option_content = ""
                                if not c.disabled:
                                    option_content = []
                                    for option in c.options:
                                        if option.emoji:
                                            with open(
                                                dir_path
                                                + "/html/component/component_menu_option.html",
                                                "r",
                                            ) as f:
                                                rawhtml = f.read()
                                            rawhtml = rawhtml.replace(
                                                "{{EMOJI}}",
                                                await parse_emoji(
                                                    str(option.emoji)
                                                ),
                                            )
                                            rawhtml = rawhtml.replace(
                                                "{{TITLE}}",
                                                await parse_md(
                                                    str(option.label), channel, tz=pytz_timezone
                                                ),
                                            )
                                            rawhtml = rawhtml.replace(
                                                "{{DESCRIPTION}}",
                                                await parse_md(
                                                    str(option.description)
                                                    if option.description
                                                    else "",
                                                    channel,
                                                    tz=pytz_timezone,
                                                ),
                                            )
                                        else:
                                            with open(
                                                dir_path
                                                + "/html/component/component_menu_option_emoji.html",
                                                "r",
                                            ) as f:
                                                rawhtml = f.read()
                                            rawhtml = rawhtml.replace(
                                                "{{TITLE}}",
                                                await parse_md(
                                                    str(option.label), channel, tz=pytz_timezone
                                                ),
                                            )
                                            rawhtml = rawhtml.replace(
                                                "{{DESCRIPTION}}",
                                                await parse_md(
                                                    str(option.description)
                                                    if option.description
                                                    else "",
                                                    channel,
                                                    tz=pytz_timezone,
                                                ),
                                            )
                                        option_content.append(rawhtml)
                                    if option_content:
                                        option_content = f'<div id="dropdownMenu{menu_div_id}" class="dropdownContent">{"".join(content)}</div>'

                                with open(
                                    dir_path + "/html/component/component_menu.html",
                                    "r",
                                ) as f:
                                    rawhtml = f.read()
                                rawhtml = rawhtml.replace(
                                    "{{DISABLED}}",
                                    "chatlog__component-disabled" if c.disabled else "",
                                )
                                rawhtml = rawhtml.replace(
                                    "{{PLACEHOLDER}}",
                                    await parse_md(
                                        c.placeholder if c.placeholder else "",
                                        channel,
                                        tz=pytz_timezone,
                                    ),
                                )
                                rawhtml = rawhtml.replace("{{ID}}", str(menu_div_id))
                                rawhtml = rawhtml.replace("{{CONTENT}}", str(option_content))
                                rawhtml = rawhtml.replace(
                                    "{{ICON}}", Default.interaction_dropdown_icon
                                )
                                components += f'<div class="chatlog__components">{rawhtml}</div>'
                                menu_div_id += 1

                reactions = ""
                if i.reactions:
                    for r in i.reactions:
                        if not r.emoji.id:
                            with open(dir_path + "/html/reaction/emoji.html", "r") as f:
                                rawhtml = f.read()
                            rawhtml = rawhtml.replace(
                                "{{EMOJI}}", await convert_emoji(str(r.emoji))
                            )
                            rawhtml = rawhtml.replace("{{EMOJI_COUNT}}", str(r.count))
                        else:
                            with open(dir_path + "/html/reaction/custom_emoji.html", "r") as f:
                                rawhtml = f.read()
                            rawhtml = rawhtml.replace("{{EMOJI}}", str(r.emoji.id))
                            rawhtml = rawhtml.replace("{{EMOJI_COUNT}}", str(r.count))
                            rawhtml = rawhtml.replace(
                                "{{EMOJI_FILE}}", "gif" if r.emoji.animated else "png"
                            )
                        reactions += rawhtml

                if reactions:
                    reactions = f'<div class="chatlog__reactions">{reactions}</div>'

                if (
                    previous is None
                    or referenced_message != ""
                    or (previous and previous.author.id != i.author.id)
                    or i.webhook_id is not None
                    or (
                        previous and i.id.timestamp > (previous.id.timestamp + timedelta(minutes=4))
                    )
                ):
                    if previous is not None:
                        data += "</div>"
                    reference_symbol = ""
                    if referenced_message != "":
                        reference_symbol = "<div class='chatlog__reference-symbol'></div>"

                    with open(dir_path + "/html/message/start.html", "r") as f:
                        rawhtml = f.read()
                    rawhtml = rawhtml.replace("{{REFERENCE_SYMBOL}}", reference_symbol)
                    rawhtml = rawhtml.replace("{{REFERENCE}}", referenced_message)
                    rawhtml = rawhtml.replace("{{AVATAR_URL}}", str(i.author.avatar_url))
                    rawhtml = rawhtml.replace(
                        "{{NAME_TAG}}", f"{i.author.username}#{i.author.discriminator}"
                    )
                    rawhtml = rawhtml.replace(
                        "{{USER_ID}}", await parse_md(str(i.author.id), channel, tz=pytz_timezone)
                    )
                    rawhtml = rawhtml.replace(
                        "{{USER_COLOUR}}",
                        await parse_md(
                            f"color: {hex(i.author.accent_color)[2:] if i.author.accent_color else '000000'}",
                            channel,
                            tz=pytz_timezone,
                        ),
                    )
                    rawhtml = rawhtml.replace("{{USER_ICON}}", "")
                    rawhtml = rawhtml.replace(
                        "{{NAME}}",
                        await parse_md(
                            str(html.escape(i.author.username)), channel, tz=pytz_timezone
                        ),
                    )
                    rawhtml = rawhtml.replace(
                        "{{BOT_TAG}}",
                        '<span class="chatlog__bot-tag">BOT</span>' if i.author.bot else "",
                    )
                    rawhtml = rawhtml.replace("{{TIMESTAMP}}", str(create))
                    rawhtml = rawhtml.replace("{{DEFAULT_TIMESTAMP}}", str(create))
                    rawhtml = rawhtml.replace(
                        "{{MESSAGE_ID}}", await parse_md(str(i.id), channel, tz=pytz_timezone)
                    )
                    rawhtml = rawhtml.replace("{{MESSAGE_CONTENT}}", msg_content)
                    rawhtml = rawhtml.replace("{{EMBEDS}}", embeds)
                    rawhtml = rawhtml.replace("{{EMOJI}}", reactions)
                    rawhtml = rawhtml.replace("{{ATTACHMENTS}}", attachments)
                    rawhtml = rawhtml.replace("{{COMPONENTS}}", components)

                else:
                    with open(dir_path + "/html/message/message.html", "r") as f:
                        rawhtml = f.read()
                    rawhtml = rawhtml.replace(
                        "{{MESSAGE_ID}}", await parse_md(str(i.id), channel, tz=pytz_timezone)
                    )
                    rawhtml = rawhtml.replace("{{MESSAGE_CONTENT}}", msg_content)
                    rawhtml = rawhtml.replace("{{EMBEDS}}", embeds)
                    rawhtml = rawhtml.replace("{{EMOJI}}", reactions)
                    rawhtml = rawhtml.replace("{{ATTACHMENTS}}", attachments)
                    rawhtml = rawhtml.replace("{{COMPONENTS}}", components)
                    rawhtml = rawhtml.replace("{{TIMESTAMP}}", str(create))
                    rawhtml = rawhtml.replace("{{TIME}}", str(create.split()[-1]))

                if str(user_id := i.author.id) in metadata:
                    metadata[str(user_id)][4] += 1
                else:
                    username = i.author.username + "#" + i.author.discriminator
                    created_at = i.author.id.timestamp
                    bot = i.author.bot
                    avatar = i.author.avatar_url
                    joined_at = i.member.joined_at if i.member and i.member.joined_at else None
                    display_name = (
                        f'<div class="meta__display-name">{i.member.name}</div>'
                        if i.member and i.member.name != i.author.username
                        else ""
                    )
                    metadata[str(user_id)] = [
                        username,
                        created_at,
                        bot,
                        avatar,
                        1,
                        joined_at,
                        display_name,
                    ]

                data += rawhtml
            previous = current

        meta_data_html: str = ""
        for md in metadata:
            creation_time = (
                metadata[str(md)][1]
                .astimezone(pytz.timezone(pytz_timezone))
                .strftime("%d/%m/%y @ %T")
            )
            joined_time = (
                metadata[str(md)][5].astimezone(pytz.timezone(pytz_timezone)).strftime("%b %d, %Y")
                if metadata[str(md)][5]
                else "Unknown"
            )
            guild_icon = guild.icon_url if guild.icon else Default.default_avatar
            with open(dir_path + "/html/message/meta.html", "r") as f:
                rawhtml = f.read()
            rawhtml = rawhtml.replace("{{USER_ID}}", str(md))
            rawhtml = rawhtml.replace("{{USERNAME}}", str(metadata[str(md)][0][:-5]))
            rawhtml = rawhtml.replace("{{DISCRIMINATOR}}", str(metadata[str(md)][0][-5:]))
            rawhtml = rawhtml.replace("{{BOT}}", str(metadata[str(md)][2]))
            rawhtml = rawhtml.replace("{{CREATED_AT}}", str(creation_time))
            rawhtml = rawhtml.replace("{{JOINED_AT}}", str(joined_time))
            rawhtml = rawhtml.replace("{{GUILD_ICON}}", str(guild_icon))
            rawhtml = rawhtml.replace("{{DISCORD_ICON}}", str(Default.logo))
            rawhtml = rawhtml.replace("{{MEMBER_ID}}", str(md))
            rawhtml = rawhtml.replace("{{USER_AVATAR}}", str(metadata[str(md)][3]))
            rawhtml = rawhtml.replace("{{DISPLAY}}", str(metadata[str(md)][6]))
            rawhtml = rawhtml.replace("{{MESSAGE_COUNT}}", str(metadata[str(md)][4]))
            meta_data_html += rawhtml

        _limit = "start"
        if limit:
            _limit = f"latest {limit} messages"

        channel_topic = (
            f'<span class="panel__channel-topic">{channel.topic}</span>' if channel.topic else ""
        )

        rawhtml = '<span class="info__subject">This is the {{LIMIT}} of the #{{CHANNEL_NAME}} channel. {{RAW_CHANNEL_TOPIC}}</span>'
        rawhtml = rawhtml.replace("{{LIMIT}}", _limit)
        rawhtml = rawhtml.replace("{{CHANNEL_NAME}}", channel.name)
        rawhtml = rawhtml.replace("{{RAW_CHANNEL_TOPIC}}", channel.topic if channel.topic else "")
        _subject = rawhtml

        _fancy_time = ""

        if fancy_time:
            with open(dir_path + "/html/script/fancy_time.html", "r") as f:
                rawhtml = f.read()
            rawhtml = rawhtml.replace("{{TIMEZONE}}", str(pytz_timezone))
            _fancy_time = rawhtml

        with open(dir_path + "/html/base.html", "r") as f:
            rawhtml = f.read()
        rawhtml = rawhtml.replace(
            "{{SERVER_NAME}}",
            await parse_md(f"{html.escape(guild.name)}", channel, tz=pytz_timezone),
        )
        rawhtml = rawhtml.replace(
            "{{SERVER_AVATAR_URL}}",
            str(guild.icon_url if guild.icon_url else Default.default_avatar),
        )
        rawhtml = rawhtml.replace(
            "{{CHANNEL_NAME}}", await parse_md(f"{channel.name}", channel, tz=pytz_timezone)
        )
        rawhtml = rawhtml.replace("{{MESSAGE_COUNT}}", str(len(msg)))
        rawhtml = rawhtml.replace("{{MESSAGES}}", data)
        rawhtml = rawhtml.replace("{{META_DATA}}", meta_data_html)
        rawhtml = rawhtml.replace("{{TIMEZONE}}", str(pytz_timezone))
        rawhtml = rawhtml.replace(
            "{{DATE_TIME}}",
            str(datetime.now(pytz.timezone(pytz_timezone)).strftime("%e %B %Y at %T (%Z)")),
        )
        rawhtml = rawhtml.replace("{{SUBJECT}}", _subject)
        rawhtml = rawhtml.replace(
            "{{CHANNEL_CREATED_AT}}",
            str(
                channel.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                    "%d/%m/%y @ %T"
                )
            ),
        )
        rawhtml = rawhtml.replace("{{CHANNEL_TOPIC}}", str(channel_topic))
        rawhtml = rawhtml.replace("{{CHANNEL_ID}}", str(channel.id))
        rawhtml = rawhtml.replace("{{MESSAGE_PARTICIPANTS}}", str(len(metadata)))
        rawhtml = rawhtml.replace("{{FANCY_TIME}}", _fancy_time)
        rawhtml = rawhtml.replace("{{SD}}", str(""))
        final = rawhtml
        clear_cache()

        return final
    else:
        raise ValueError("Invalid mode")


def setup(client):
    Channel.get_transcript = get_transcript
    return Transcript(client)
