import datetime
import json

import discord
import markdownify
from skoleintra import Skoleintra
from asyncer import asyncify

def stringify(html):
    return markdownify.markdownify(html, heading_style="SETEXT").replace("\n\n", "\n")

config = json.load(open("config.json"))
if config["skoleintra"]["baseUrl"][-1] != "/":
    config["skoleintra"]["baseUrl"] += "/"

skoleintraClient = Skoleintra(brugernavn=config["skoleintra"]["brugernavn"], adgangskode=config["skoleintra"]["adgangskode"], url=config["skoleintra"]["baseUrl"])

client = discord.Client()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="$help | Lavet af Jonathan#0008"))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$help'):
        embed = discord.Embed(title="Help", description="**$ugeplan**: *Giver ugeplanen fra den uge du er i (Med mindre det er weekend, så er det den næste)*\n\n**$ugeplan uge-år**: *Giver ugeplanen fra en given uge. Eksempel: ``$ugeplan 10-2022``*", color=discord.Color.from_rgb(26, 144, 130))
        await message.reply(embed=embed)

    elif message.content.startswith('$ugeplan'):
        args = str(message.content).split(" ")

        if len(args) == 1:
            year, week, day_of_week = datetime.datetime.now().isocalendar()
            if day_of_week > 5:
                if week == 52:
                    week == 0
                week += 1
        elif len(args) == 2:
            week = int(args[1].split("-")[0])
            year = int(args[1].split("-")[1])

        await message.add_reaction('👍')
        print(f"Giver ugeplanen til @{message.author}")

        ugeplan = await asyncify(skoleintraClient.getWeeklyplans)(week=week, year=year)

        response = {"Klasse": ugeplan["SelectedPlan"]["ClassOrGroup"], "Uge": ugeplan["SelectedPlan"]["FormattedWeek"], "Ugeplan": {"General": []}}

        i = 0
        for lesson in ugeplan["SelectedPlan"]["GeneralPlan"]["LessonPlans"]:
            response["Ugeplan"]["General"].append(
                {"Lesson": lesson["Subject"]["Title"], "Content": stringify(lesson["Content"]),
                 "Attachments": []})
            if lesson["Attachments"] != []:
                for attachment in lesson["Attachments"]:
                    response["Ugeplan"]["General"][i]["Attachments"].append(config["skoleintra"]["baseUrl"] + attachment["Uri"])

            i += 1

        for plan in ugeplan["SelectedPlan"]["DailyPlans"]:
            response["Ugeplan"][plan["FeedbackFormattedDate"]] = []
            i = 0
            for lesson in plan["LessonPlans"]:
                response["Ugeplan"][plan["FeedbackFormattedDate"]].append(
                    {"Lesson": lesson["Subject"]["Title"], "Content": stringify(lesson["Content"]),
                     "Attachments": []})
                if lesson["Attachments"] != []:
                    j = 0
                    for attachment in lesson["Attachments"]:
                        response["Ugeplan"][plan["FeedbackFormattedDate"]][i]["Attachments"].append(f'[{attachment["FileName"]}]({config["skoleintra"]["baseUrl"] + attachment["Uri"]})')

                i += 1

        i = 0
        for day, lessons in response["Ugeplan"].items():
            description = ""
            for lesson in lessons:
                description += f"**_{lesson['Lesson']}:_**\n{lesson['Content']}\n"
                if lesson["Attachments"] != []:
                    description += "**Attachments:**"
                    for attachment in lesson["Attachments"]:
                        description += f"{attachment}"
                    description += "\n\n"
            embed = discord.Embed(title=day.title(), description=description, color=discord.Color.from_rgb(26, 144, 130))
            embed.set_author(name=f"{response['Klasse']}'s ugeplan", icon_url="https://cdn.discordapp.com/avatars/952176118713184276/e3f73d72b91c8a84c5c5ad4ae6053b53.webp?size=512")
            if i == len(response["Ugeplan"])-1:
                embed.set_footer(text=f"Opdateret: {datetime.datetime.now()}")

            await message.channel.send(embed=embed)
            i += 1

client.run(config["token"])