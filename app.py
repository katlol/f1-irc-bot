# MIT Copyright (c) 2020 jesopo for the original file
# https://github.com/jesopo/ircrobots/blob/master/examples/simple.py
import asyncio
import aiohttp
import ics
from ago import human
from arrow import Arrow
from contextlib import suppress
import re

from irctokens import build, Line
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer
from ircrobots import ConnectionParams

SERVERS = [("libera", "irc.libera.chat")]

FIB_TIMEZONE = "Europe/Rome"
FIB_ICS = "https://f1calendar.com/download/f1-calendar_p1_p2_p3_q_gp.ics"

COMMANDS = {
    "n": r"^[^:]+:[^(PRIVMSG)]+ PRIVMSG #obviyus \.n$",
    "ls": r"^[^:]+:[^(PRIVMSG)]+ PRIVMSG #obviyus \.ls$",
}


class Cal:
    async def calendar(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(FIB_ICS, timeout=5) as resp:
                    self._calendar = ics.Calendar(await resp.text())
                    return self._calendar
        except:
            return self._calendar

    async def get_events(self, num=10, page=0, more=False, weekend=False):
        lines = []
        calendar = await self.calendar()
        timeline = list(calendar.timeline.start_after(Arrow.now()))
        start = min(page * num, len(timeline) - num)

        for event in list(calendar.timeline.now()):
            lines.append(
                f"{event.name} ongoing, ending "
                + human(event.end.to(FIB_TIMEZONE).timestamp, precision=2)
            )

        for event in list(timeline)[start:]:
            local_time = event.begin.to(FIB_TIMEZONE)
            print(type(local_time))
            print(dir(local_time))
            lines.append(
                "{0} {1}, {2}".format(
                    event.name,
                    human(local_time.timestamp, precision=2),
                    local_time.strftime("%d %b @ %H:%M"),
                )
            )
            if len(lines) >= num or weekend and local_time.isoweekday() in (7, 1):
                break
        if more and len(timeline) - start - num:
            lines.append(f"...and {len(timeline) - start - num} more")
        return lines

class Commands:
    def __init__(self):
        self.cal = Cal()

    async def n(self):
        return await self.cal.get_events(num=1, page=0, more=False, weekend=True)

    async def ls(self):
        return await self.cal.get_events(num=10, page=0, more=True, weekend=True)

    async def run(self, command):
        return await getattr(self, command)()


class Server(BaseServer):
    async def line_read(self, line: Line):
        print(f"{self.name} < {line.format()}")
        if line.command == "001":
            print(f"connected to {self.isupport.network}")
            await self.send(build("JOIN", ["#obviyus"]))
        for command, regex in COMMANDS.items():
            if re.match(regex, line.format()):
                lines = await Commands().run(command)
                for line in lines:
                    await self.send(build("PRIVMSG", ["#obviyus", line]))
    async def line_send(self, line: Line):
        print(f"{self.name} > {line.format()}")


class Bot(BaseBot):
    def create_server(self, name: str):
        return Server(self, name)


async def main():
    bot = Bot()
    for name, host in SERVERS:
        params = ConnectionParams("f1test", host, 6697)
        await bot.add_server(name, params)

    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
