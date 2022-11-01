import datetime
import html
import math
import re

import pytz

from interactions import Channel, Guild, LibraryException, Member, User

from .emoji_convert import convert_emoji

styles = {
    "primary": "#5865F2",
    "secondary": "#4F545C",
    "success": "#2D7D46",
    "danger": "#D83C3E",
    "link": "#4F545C",
}


class Default:
    logo: str = "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-logo.svg"
    default_avatar: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-default.png"
    )
    pinned_message_icon: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-pinned.svg"
    )
    thread_channel_icon: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-thread.svg"
    )
    file_attachment_audio: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-audio.svg"
    )
    file_attachment_acrobat: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-acrobat.svg"
    )
    file_attachment_webcode: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-webcode.svg"
    )
    file_attachment_code: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-code.svg"
    )
    file_attachment_document: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-document.svg"
    )
    file_attachment_archive: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-archive.svg"
    )
    file_attachment_unknown: str = (
        "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-unknown.svg"
    )
    button_external_link: str = '<img class="chatlog__reference-icon" src="https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-external-link.svg">'
    reference_attachment_icon: str = '<img class="chatlog__reference-icon" src="https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-attachment.svg">'
    interaction_dropdown_icon: str = '<img class="chatlog__dropdown-icon" src="https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-dropdown.svg">'


class Regex:
    REGEX_ROLES = r"&lt;@&amp;([0-9]+)&gt;"
    REGEX_ROLES_2 = r"<@&([0-9]+)>"
    REGEX_MEMBERS = r"&lt;@!?([0-9]+)&gt;"
    REGEX_MEMBERS_2 = r"<@!?([0-9]+)>"
    REGEX_CHANNELS = r"&lt;#([0-9]+)&gt;"
    REGEX_CHANNELS_2 = r"<#([0-9]+)>"
    REGEX_EMOJIS = r"&lt;a?(:[^\n:]+:)[0-9]+&gt;"
    REGEX_EMOJIS_2 = r"<a?(:[^\n:]+:)[0-9]+>"
    REGEX_TIME_HOLDER = (
        [r"&lt;t:([0-9]+):t&gt;", "%H:%M"],
        [r"&lt;t:([0-9]+):T&gt;", "%T"],
        [r"&lt;t:([0-9]+):d&gt;", "%d/%m/%Y"],
        [r"&lt;t:([0-9]+):D&gt;", "%e %B %Y"],
        [r"&lt;t:([0-9]+):f&gt;", "%e %B %Y %H:%M"],
        [r"&lt;t:([0-9]+):F&gt;", "%A, %e %B %Y %H:%M"],
        [r"&lt;t:([0-9]+):R&gt;", "%e %B %Y %H:%M"],
        [r"&lt;t:([0-9]+)&gt;", "%e %B %Y %H:%M"],
    )

    ESCAPE_LT = "______lt______"
    ESCAPE_GT = "______gt______"
    ESCAPE_AMP = "______amp______"


async def escape_mention(content):
    for match in re.finditer(
        "(%s|%s|%s|%s|%s|%s|%s|%s)"
        % (
            Regex.REGEX_ROLES,
            Regex.REGEX_MEMBERS,
            Regex.REGEX_CHANNELS,
            Regex.REGEX_EMOJIS,
            Regex.REGEX_ROLES_2,
            Regex.REGEX_MEMBERS_2,
            Regex.REGEX_CHANNELS_2,
            Regex.REGEX_EMOJIS_2,
        ),
        content,
    ):
        pre_content = content[: match.start()]
        post_content = content[match.end() :]
        match_content = content[match.start() : match.end()]

        match_content = (
            match_content.replace("<", Regex.ESCAPE_LT)
            .replace(">", Regex.ESCAPE_GT)
            .replace("&", Regex.ESCAPE_AMP)
        )

        content = pre_content + match_content + post_content
    return content


async def unescape_mention(content):
    return (
        content.replace(Regex.ESCAPE_LT, "<")
        .replace(Regex.ESCAPE_GT, ">")
        .replace(Regex.ESCAPE_AMP, "&")
    )


async def channel_mention(content, c):
    for regex in [Regex.REGEX_CHANNELS, Regex.REGEX_CHANNELS_2]:
        match = re.search(regex, content)
        while match is not None:
            channel_id = int(match.group(1))
            channel = Channel(**await c._client.get_channel(channel_id))

            content = content.replace(
                content[match.start() : match.end()],
                "#deleted-channel"
                if channel is None
                else '<span class="mention" title="%s">#%s</span>' % (channel.id, channel.name),
            )

            match = re.search(regex, content)
    return content


async def member_mention(content, c):
    for regex in [Regex.REGEX_MEMBERS, Regex.REGEX_MEMBERS_2]:
        match = re.search(regex, content)
        while match is not None:
            member_id = int(match.group(1))
            member = False
            try:
                member_name = (
                    Member(**await c._client.get_member(c.guild_id, member_id)).name
                    or User(**await c._client.get_user(member_id)).username
                )
                member = True
            except AttributeError:
                member_name = member

            content = content.replace(
                content[match.start() : match.end()],
                '<span class="mention" title="%s">@%s</span>' % (str(member_id), str(member_name))
                if member
                else '<span class="mention" title="%s">&lt;@%s></span>'
                % (str(member_id), str(member_id)),
            )

            match = re.search(regex, content)
    return content


async def role_mention(content, c):
    for regex in [Regex.REGEX_ROLES, Regex.REGEX_ROLES_2]:
        match = re.search(regex, content)
        while match is not None:
            role_id = int(match.group(1))
            role = None
            try:
                role = await Guild(**await c._client.get_guild(c.guild_id)).get_role(role_id)
            except LibraryException:
                pass

            if role is None:
                r = "@deleted-role"
            else:
                if role.color == 0:
                    color = "#dee0fc"
                else:
                    color = f"#{hex(role.color)[2:]}"
                r = '<span style="color: %s;">@%s</span>' % (color, role.name)
            content = content.replace(content[match.start() : match.end()], r)

            match = re.search(regex, content)
    return content


async def time_mention(content, tz):
    holder = Regex.REGEX_TIME_HOLDER
    timezone = pytz.timezone(tz)

    for p in holder:
        regex, strf = p
        match = re.search(regex, content)
        while match is not None:
            time = datetime.datetime.fromtimestamp(int(match.group(1)), timezone)
            ui_time = time.strftime(strf)
            tooltip_time = time.strftime("%A, %e %B %Y at %H:%M")
            original = match.group().replace("&lt;", "<").replace("&gt;", ">")
            replacement = (
                f'<span class="unix-timestamp" data-timestamp="{tooltip_time}" raw-content="{original}">'
                f"{ui_time}</span>"
            )

            content = content.replace(content[match.start() : match.end()], replacement)

            match = re.search(regex, content)
        return content


async def parse_mention(content, channel, tz):
    return await time_mention(
        await role_mention(
            (
                await member_mention(
                    (
                        await channel_mention(
                            await unescape_mention(
                                await escape_mention(await escape_mention(content))
                            ),
                            channel,
                        )
                    ),
                    channel,
                )
            ),
            channel,
        ),
        tz,
    )


def return_to_markdown(content):
    holders = (
        [r"<strong>(.*?)</strong>", "**%s**"],
        [r"<em>([^<>]+)</em>", "*%s*"],
        [r'<span style="text-decoration: underline">([^<>]+)</span>', "__%s__"],
        [r'<span style="text-decoration: line-through">([^<>]+)</span>', "~~%s~~"],
        [r'<div class="quote">(.*?)</div>', "> %s"],
        [
            r'<span class="spoiler spoiler--hidden" onclick="showSpoiler\(event, this\)"> <span '
            r'class="spoiler-text">(.*?)<\/span><\/span>',
            "||%s||",
        ],
        [r'<span class="unix-timestamp" data-timestamp=".*?" raw-content="(.*?)">.*?</span>', "%s"],
    )

    for x in holders:
        p, r = x

        pattern = re.compile(p)
        match = re.search(pattern, content)
        while match is not None:
            affected_text = match.group(1)
            content = content.replace(
                content[match.start() : match.end()], r % html.escape(affected_text)
            )
            match = re.search(pattern, content)

    pattern = re.compile(r'<a href="(.*?)">(.*?)</a>')
    match = re.search(pattern, content)
    while match is not None:
        affected_url = match.group(1)
        affected_text = match.group(2)
        if affected_url != affected_text:
            content = content.replace(
                content[match.start() : match.end()],
                "[%s](%s)" % (affected_text, affected_url),
            )
        else:
            content = content.replace(content[match.start() : match.end()], "%s" % affected_url)
        match = re.search(pattern, content)

    return content.lstrip().rstrip()


def links(content):
    def suppressed(url, raw_url=None):
        pattern = rf"`.*{raw_url}.*`"
        match = re.search(pattern, content)

        if "&lt;" in url and "&gt;" in url and not match:
            return url.replace("&lt;", "").replace("&gt;", "")
        return url

    content = re.sub("\n", "<br>", content)
    output = []
    if "http://" in content or "https://" in content and "](" not in content:
        for word in content.replace("<br>", " <br>").split():
            if "http" not in word:
                output.append(word)
                continue

            if "&lt;" in word and "&gt;" in word:
                pattern = r"&lt;https?:\/\/(.*)&gt;"
                match_url = re.search(pattern, word).group(1)
                url = f'<a href="https://{match_url}">https://{match_url}</a>'
                word = word.replace("https://" + match_url, url)
                word = word.replace("http://" + match_url, url)
                output.append(suppressed(word, match_url))
            elif "https://" in word:
                pattern = r"https://[^\s>`\"*]*"
                word_link = re.search(pattern, word).group()
                if word_link.endswith(")"):
                    output.append(word)
                    continue
                word_full = f'<a href="{word_link}">{word_link}</a>'
                word = re.sub(pattern, word_full, word)
                output.append(suppressed(word))
            elif "http://" in word:
                pattern = r"http://[^\s>`\"*]*"
                word_link = re.search(pattern, word).group()
                if word_link.endswith(")"):
                    output.append(word)
                    continue
                word_full = f'<a href="{word_link}">{word_link}</a>'
                word = re.sub(pattern, word_full, word)
                output.append(suppressed(word))
            else:
                output.append(word)
        content = " ".join(output)
        content = re.sub("<br>", "\n", content)
    return content


def normal_markdown(content):
    holder = (
        [r"__(.*?)__", '<span style="text-decoration: underline">%s</span>'],
        [r"\*\*(.*?)\*\*", "<strong>%s</strong>"],
        [r"\*(.*?)\*", "<em>%s</em>"],
        [r"~~(.*?)~~", '<span style="text-decoration: line-through">%s</span>'],
        [
            r"\|\|(.*?)\|\|",
            '<span class="spoiler spoiler--hidden" onclick="showSpoiler(event, this)"> <span '
            'class="spoiler-text">%s</span></span>',
        ],
    )

    for x in holder:
        p, r = x

        pattern = re.compile(p)
        match = re.search(pattern, content)
        while match is not None:
            affected_text = match.group(1)
            content = content.replace(content[match.start() : match.end()], r % affected_text)
            match = re.search(pattern, content)

    # > quote
    content = content.split("<br>")
    y = None
    new_content = ""
    pattern = re.compile(r"^&gt;\s(.+)")

    if len(content) == 1:
        if re.search(pattern, content[0]):
            content = f'<div class="quote">{content[0][5:]}</div>'
            return content
        content = content[0]
        return content

    for x in content:
        if re.search(pattern, x) and y:
            y = y + "<br>" + x[5:]
        elif not y:
            if re.search(pattern, x):
                y = x[5:]
            else:
                new_content = new_content + x + "<br>"
        else:
            new_content = new_content + f'<div class="quote">{y}</div>'
            new_content = new_content + x
            y = ""

    if y:
        new_content = new_content + f'<div class="quote">{y}</div>'

    return new_content


def code_block_markdown(content, reference=False):
    markdown_languages = [
        "asciidoc",
        "autohotkey",
        "bash",
        "coffeescript",
        "cpp",
        "cs",
        "css",
        "diff",
        "fix",
        "glsl",
        "ini",
        "json",
        "md",
        "ml",
        "prolog",
        "py",
        "tex",
        "xl",
        "xml",
        "js",
        "html",
    ]
    content = re.sub(r"\n", "<br>", content)

    # ```code```
    pattern = re.compile(r"```(.*?)```")
    match = re.search(pattern, content)
    while match is not None:
        language_class = "nohighlight"
        affected_text = match.group(1)

        for language in markdown_languages:
            if affected_text.lower().startswith(language):
                language_class = f"language-{language}"
                _, _, affected_text = affected_text.partition("<br>")

        affected_text = return_to_markdown(affected_text)

        second_pattern = re.compile(r"^<br>|<br>$")
        second_match = re.search(second_pattern, affected_text)
        while second_match is not None:
            affected_text = re.sub(r"^<br>|<br>$", "", affected_text)
            second_match = re.search(second_pattern, affected_text)
        affected_text = re.sub("  ", "&nbsp;&nbsp;", affected_text)

        if not reference:
            content = content.replace(
                content[match.start() : match.end()],
                '<div class="pre pre--multiline %s">%s</div>' % (language_class, affected_text),
            )
        else:
            content = content.replace(
                content[match.start() : match.end()],
                '<span class="pre pre-inline">%s</span>' % affected_text,
            )

        match = re.search(pattern, content)

    # ``code``
    pattern = re.compile(r"``(.*?)``")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        affected_text = return_to_markdown(affected_text)
        content = content.replace(
            content[match.start() : match.end()],
            '<span class="pre pre-inline">%s</span>' % affected_text,
        )
        match = re.search(pattern, content)

    # `code`
    pattern = re.compile(r"`(.*?)`")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        affected_text = return_to_markdown(affected_text)
        content = content.replace(
            content[match.start() : match.end()],
            '<span class="pre pre-inline">%s</span>' % affected_text,
        )
        match = re.search(pattern, content)

    return re.sub(r"<br>", "\n", content)


def embed_markdown(content):
    # [Message](Link)
    pattern = re.compile(r"\[(.+?)]\((.+?)\)")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        affected_url = match.group(2)
        content = content.replace(
            content[match.start() : match.end()],
            '<a href="%s">%s</a>' % (affected_url, affected_text),
        )
        match = re.search(pattern, content)

    content = content.split("\n")
    y = None
    new_content = ""
    pattern = re.compile(r"^>\s(.+)")

    if len(content) == 1:
        if re.search(pattern, content[0]):
            content = f'<div class="quote">{content[0][2:]}</div>'
            return content
        content = content[0]
        return content

    for x in content:
        if re.search(pattern, x) and y:
            y = y + "\n" + x[2:]
        elif not y:
            if re.search(pattern, x):
                y = x[2:]
            else:
                new_content = new_content + x + "\n"
        else:
            new_content = new_content + f'<div class="quote">{y}</div>'
            new_content = new_content + x
            y = ""

    if y:
        new_content = new_content + f'<div class="quote">{y}</div>'

    return new_content


async def parse_emoji(content):
    holder = (
        [
            r"&lt;:.*?:(\d*)&gt;",
            '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.png">',
        ],
        [
            r"&lt;a:.*?:(\d*)&gt;",
            '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.gif">',
        ],
        [
            r"<:.*?:(\d*)>",
            '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.png">',
        ],
        [
            r"<a:.*?:(\d*)>",
            '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.gif">',
        ],
    )

    content = await convert_emoji([word for word in content])

    for x in holder:
        p, r = x
        match = re.search(p, content)
        while match is not None:
            emoji_id = match.group(1)
            content = content.replace(content[match.start() : match.end()], r % emoji_id)
            match = re.search(p, content)
    return content


def parse_br(content):
    return content.replace("<br>", " ")


async def parse_md(content, channel, tz):
    return await parse_emoji(
        code_block_markdown(normal_markdown(links(await parse_mention(content, channel, tz)))),
    )


async def parse_embed(content, channel, tz):
    return await parse_emoji(
        code_block_markdown(
            normal_markdown(embed_markdown(links(await parse_mention(content, channel, tz))))
        ),
    )


async def parse_msg_ref(content, channel, tz):
    return parse_br(
        await parse_emoji(
            code_block_markdown(normal_markdown(links(await parse_mention(content, channel, tz)))),
        )
    )


def get_file_size(file_size):
    if file_size == 0:
        return "0 bytes"
    size_name = ("bytes", "KB", "MB")
    i = int(math.floor(math.log(file_size, 1024)))
    p = math.pow(1024, i)
    s = round(file_size / p, 2)
    return "%s %s" % (s, size_name[i])


def get_file_icon(url) -> str:
    acrobat_types = "pdf"
    webcode_types = "html", "htm", "css", "rss", "xhtml", "xml"
    code_types = "py", "cgi", "pl", "gadget", "jar", "msi", "wsf", "bat", "php", "js"
    document_types = (
        "txt",
        "doc",
        "docx",
        "rtf",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
        "odt",
        "odp",
        "ods",
        "odg",
        "odf",
        "swx",
        "sxi",
        "sxc",
        "sxd",
        "stw",
    )
    archive_types = (
        "br",
        "rpm",
        "dcm",
        "epub",
        "zip",
        "tar",
        "rar",
        "gz",
        "bz2",
        "7x",
        "deb",
        "ar",
        "Z",
        "lzo",
        "lz",
        "lz4",
        "arj",
        "pkg",
        "z",
    )
    extension = url.rsplit(".", 1)[1]
    if extension in acrobat_types:
        return Default.file_attachment_acrobat
    elif extension in webcode_types:
        return Default.file_attachment_webcode
    elif extension in code_types:
        return Default.file_attachment_code
    elif extension in document_types:
        return Default.file_attachment_document
    elif extension in archive_types:
        return Default.file_attachment_archive
    else:
        return Default.file_attachment_unknown
