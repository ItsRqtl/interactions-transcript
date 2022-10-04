from interactions import Channel, Extension, Guild
import pytz

newline = "\r\n"

class Transcript(Extension):
    def __init__(self, client):
        self.client = client

async def get_transcript(channel: Channel, limit: int = 100, pytz_timezone = 'UTC', military_time: bool = False, fancy_time: bool = True, mode: str = 'html'):
    msg = await channel.get_history(limit=limit)
    msg.reverse()

    guild = Guild(**await channel._client.get_guild(channel.guild_id))

    if mode == 'plain':
        content = "==============================================================\r\nGuild: {}\r\nChannel: {}\r\n==============================================================\r\n".format(guild.name, channel.name)
        for i in msg:
            if military_time:
                time = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime('%d-%b-%y %H:%M:%S')
                edit_time = i.edited_timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime('%d-%b-%y %H:%M:%S') if i.edited_timestamp else None
            else:
                time = i.id.timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime('%d-%b-%y %I:%M:%S%p')
                edit_time = i.edited_timestamp.astimezone(pytz.timezone(pytz_timezone)).strftime('%d-%b-%y %I:%M:%S%p') if i.edited_timestamp else None
            content += "\r\n [{}] {} ({})\r\n{}".format(time, i.author.username+"#"+i.author.discriminator, i.author.id, i.content)
            if i.embeds:
                content += "\r\n{Embed}"
                for e in i.embeds:
                    content += f"{newline}{f'{newline}{e.author.url}' if e.author and e.author.url else ''}{f'{newline}{e.author.name}' if e.author and e.author.name else ''}{f'{newline}{e.title}' if e.title else ''}{f'{newline}{e.description}' if e.description else ''}{''.join([f'{newline}{f.name}{newline}{f.value}' for f in e.fields]) if e.fields else ''}{f'{newline}{e.thumbnail.url}' if e.thumbnail else ''}{f'{newline}{e.image.url}' if e.image else ''}"
            if i.attachments:
                content += "\r\n{Attachments}"
                for a in i.attachments:
                    content += f"{newline}{a.url}"
            if i.reactions:
                content += "\r\n{Reactions}"
                for r in i.reactions:
                    content += f"{newline}{r.emoji} - {r.count}"
            if not content.endswith('\r\n'):
                content += "\r\n"
        return content

def setup(client):
    Channel.get_transcript = get_transcript
    return Transcript(client)