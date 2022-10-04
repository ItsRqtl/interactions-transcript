import io
from interactions import Channel, Extension, Guild
import pytz
import pandas as pd

newline = "\n"


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
    :param mode: The mode to use for the transcript (html, json, xml, csv, or plain)
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
                    i.edited_timestamp.astimezone(
                        pytz.timezone(pytz_timezone)
                    ).strftime("%d-%b-%y %H:%M:%S")
                    if i.edited_timestamp
                    else None
                )
            else:
                time = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                    "%d-%b-%y %I:%M:%S%p"
                )
                edit_time = (
                    i.edited_timestamp.astimezone(
                        pytz.timezone(pytz_timezone)
                    ).strftime("%d-%b-%y %I:%M:%S%p")
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

    elif mode == "csv" or mode == "xml" or mode == "json":
        data = []
        for i in msg:
            if military_time:
                time = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                    "%d-%b-%y %H:%M:%S"
                )
                edit_time = (
                    i.edited_timestamp.astimezone(
                        pytz.timezone(pytz_timezone)
                    ).strftime("%d-%b-%y %H:%M:%S")
                    if i.edited_timestamp
                    else None
                )
            else:
                time = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime(
                    "%d-%b-%y %I:%M:%S%p"
                )
                edit_time = (
                    i.edited_timestamp.astimezone(
                        pytz.timezone(pytz_timezone)
                    ).strftime("%d-%b-%y %I:%M:%S%p")
                    if i.edited_timestamp
                    else None
                )
            data.append(
                {
                    "Guild": {"name": guild.name, "id": str(guild.id)},
                    "Channel": {"name": channel.name, "id": str(channel.id)},
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
                    "Attachments": [a.url for a in i.attachments]
                    if i.attachments
                    else [],
                    "Reactions": [{r.emoji: r.count} for r in i.reactions]
                    if i.reactions
                    else [],
                }
            )
        df = pd.DataFrame(data)
        if mode == "csv":
            df.to_csv(file := io.StringIO(), index=True, header=True)
            return file.getvalue()
        elif mode == "xml":
            df.to_xml(
                file := io.BytesIO(),
                index=True,
                encoding="utf-8",
                root_name="transcript",
                row_name="message",
            )
            return file.getvalue().decode("utf-8")
        elif mode == "json":
            df.to_json(file := io.StringIO(), index=True, orient="records")
            return file.getvalue()

    elif mode == "html":
        raise NotImplementedError("HTML mode is not yet implemented.")

    else:
        raise ValueError("Invalid mode")


def setup(client):
    Channel.get_transcript = get_transcript
    return Transcript(client)
