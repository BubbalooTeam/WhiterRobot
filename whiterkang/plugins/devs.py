# Copiright (C) 2023 BubbalooTeam

import re
import time
import os
import signal
import asyncio 
import traceback 
import subprocess
import logging
import io
import sys
import psutil

from hydrogram import filters
from hydrogram.enums import ParseMode  
from hydrogram.errors import UserIsBlocked
from hydrogram.types import Message

from datetime import datetime
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from speedtest import Speedtest

from whiterkang import WhiterX, db, START_TIME, Config
from whiterkang.helpers import is_dev, http, input_str, aexec, time_formatter

USERS = db["USERS"]
GROUPS = db["GROUPS"]
USERS_STARTED = db["USERS_START"]
AFK = db["_AFK"]

REPO_ = "https://github.com/BubbalooTeam/WhiterRobot"
BRANCH_ = "WhiterRobot"

@WhiterX.on_message(filters.command(["status"], Config.TRIGGER))
async def status_(c: WhiterX, m: Message):
    user_id = m.from_user.id
    if not is_dev(user_id):
        return
    glist = await GROUPS.estimated_document_count()
    ulist = await USERS.estimated_document_count()
    afk_status = await AFK.estimated_document_count()
    userlist = await USERS_STARTED.estimated_document_count()
    await m.reply(f"<b>【 WhiterKang Status 】</b>\n\n<b>Users</b>: <i>{userlist}</i>\n<b>Users in AFK</b>: <i>{afk_status}</i>\n<b>Regs</b>: <i>{ulist}</i>\n<b>Groups</b>: <i>{glist}</i>")

@WhiterX.on_message(filters.command(["broadcast", "bc"], Config.TRIGGER))
async def broadcasting_(c: WhiterX, m: Message):
    user_id = m.from_user.id
    if not is_dev(user_id):
        return
    if not input_str(m):
        return await m.reply("<i>I need text to broadcasting.</i>")
    query = m.text.split(None, 1)[1]
    msg = await m.reply("<i>Broadcasting ...</i>")
    web_preview = False
    sucess_br = 0
    no_sucess = 0
    total_user = await USERS.estimated_document_count()
    ulist = USERS.find()
    if query.startswith("-d"):
        web_preview = True
        query_ = query.strip("-d")
    else:
        query_ = query
    async for users in ulist:
        try:
            await c.send_message(chat_id= users["id_"], text=query_, disable_web_page_preview=web_preview)
            sucess_br += 1
        except UserIsBlocked:
            no_sucess += 1
        except Exception:
            no_sucess += 1
    total_groups = await GROUPS.estimated_document_count()
    sucess_br_gp = 0
    no_sucess_gp = 0
    gplist = GROUPS.find()
    async for groups in gplist:
        try:
            await c.send_message(chat_id= groups["id_"], text=query_, disable_web_page_preview=web_preview)
            sucess_br_gp += 1
        except Exception:
            no_sucess_gp += 1
    await asyncio.sleep(3)
    await msg.edit(f"""
╭─❑ 「 <b>Broadcast Completed</b> 」 ❑──
│- <i>Total Users:</i> <code>{total_user}</code>
│- <i>Total Groups:</i> <code>{total_groups}</code>
│- <i>Successfully Users:</i> <code>{sucess_br}</code>
│- <i>Failed Users:</i> <code>{no_sucess}</code>
│- <i>Successfully Groups:</i> <code>{sucess_br_gp}</code>
│- <i>Failed Groups:</i> <b>{no_sucess_gp}</b>
╰❑
    """)

@WhiterX.on_message(filters.command("restart", Config.TRIGGER))
async def rr(c: WhiterX, m: Message):
    user_id = m.from_user.id
    if not is_dev(user_id):
        return
    sent = await m.reply("<i>Restarting...</i>") 
    args = [sys.executable, "-m", "whiterkang"]
    await sent.edit("<b>WhiterKang is now Restarted!</b>")
    os.execl(sys.executable, *args)

@WhiterX.on_message(filters.command("shutdown", Config.TRIGGER))
async def shutdown(c: WhiterX, m: Message):
    user_id = m.from_user.id
    if not is_dev(user_id):
        return
    await m.reply("<b>WhiterKang is now Offline!</b>")
    os.kill(os.getpid(), signal.SIGINT)

@WhiterX.on_message(filters.command(["up", "update"], Config.TRIGGER))
async def updater(c: WhiterX, m: Message):
    if not is_dev(m.from_user.id):
        return
    msg_ = await m.reply("<i>Updating Please Wait!</i>")
    try:
        repo = Repo()
    except GitCommandError:
        return await msg_.edit("<i>Invalid Git Command</i>")
    except InvalidGitRepositoryError:
        repo = Repo.init()
        if "upstream" in repo.remotes:
            origin = repo.remote("upstream")
        else:
            origin = repo.create_remote("upstream", REPO_)
        origin.fetch()
        repo.create_head(BRANCH_, origin.refs.master)
        repo.heads.master.set_tracking_branch(origin.refs.master)
        repo.heads.master.checkout(True)
    if repo.active_branch.name != BRANCH_:
        return await msg_.edit("<i>error in update. please try again...</i>")
    try:
        repo.create_remote("upstream", REPO_)
    except BaseException:
        pass
    ups_rem = repo.remote("upstream")
    ups_rem.fetch(BRANCH_)
    try:
        ups_rem.pull(BRANCH_)
    except GitCommandError:
        repo.git.reset("--hard", "FETCH_HEAD")
    await msg_.edit("<i>Updated Sucessfully! Give Me A min To Restart!</i>")
    args = [sys.executable, "-m", "whiterkang"]
    os.execle(sys.executable, *args, os.environ)

@WhiterX.on_message(filters.command(["ev", "eval"], Config.TRIGGER))
async def eval_(c: WhiterX, m: Message):
    user_id = m.from_user.id
    if not is_dev(user_id):
        return
    if len(m.text.split()) == 1 and not m.reply_to_message:
        await m.reply_text("Usage: <code>/eval print('Hello World')</code>")
        return
    status_message = await m.reply_text("<i>Processing code ...</i>")
    cmd = m.text[len(m.text.split()[0]) + 1:]
    reply_to_ = m
    if m.reply_to_message:
        reply_to_ = m.reply_to_message
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, c, m)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Code executed with successfully!"
    final_output = "<b>Expression</b>: "
    final_output += f"<code>{cmd}</code>\n\n"
    final_output += "<b>Result</b>:\n"
    final_output += f"<code>{evaluation.strip()}</code> \n"
    if len(final_output) > 4096:
        with io.BytesIO(str.encode(final_output)) as out_file:
            out_file.name = "eval.txt"
            await reply_to_.reply_document(
                document=out_file, caption=cmd[:1000], disable_notification=True
            )
    else:
        await reply_to_.reply_text(final_output)
    await status_message.delete()



@WhiterX.on_message(filters.command(["term", "sh"], Config.TRIGGER))
async def terminal(c: WhiterX, m: Message):
    user_id = m.from_user.id
    if not is_dev(user_id):
        return
    if len(m.text.split()) == 1:
        await m.reply_text("Usage: <code>/term echo owo</code>")
        return
    status_message = await m.reply_text("<i>Processing command in terminal ...</i>")
    args = m.text.split(None, 1)
    teks = args[1]
    if "\n" in teks:
        code = teks.split("\n")
        output = ""
        for x in code:
            shell = re.split(""" (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", x)
            try:
                process = subprocess.Popen(
                    shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            except Exception as err:
                print(err)
                await m.reply_text(
                    """
<b>Error:</b>
<code>{}</code>
""".format(
                        err
                    ),
                )
            output += "<b>{}</b>\n".format(code)
            output += process.stdout.read()[:-1].decode("utf-8")
            output += "\n"
    else:
        shell = re.split(""" (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", teks)
        for a in range(len(shell)):
            shell[a] = shell[a].replace('"', "")
        try:
            process = subprocess.Popen(
                shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            errors = traceback.format_exception(
                etype=exc_type, value=exc_obj, tb=exc_tb
            )
            await m.reply_text(
                """<b>Error:</b>\n<code>{}</code>""".format("".join(errors)),
            )
            await status_message.delete()
            return
        output = process.stdout.read()[:-1].decode("utf-8")
    if str(output) == "\n":
        output = None
    if output:
        if len(output) > 4096:
            filename = "output.txt"
            with open(filename, "w+") as file:
                file.write(output)
            await c.send_document(
                message.chat.id,
                filename,
                reply_to_message_id=message.id,
                caption="<code>Output file</code>",
            )
            os.remove(filename)
            await status_message.delete()
            return
        await m.reply_text(f"<b>Output:</b>\n<code>{output}</code>")
        await status_message.delete()
    else:
        await m.reply_text("<b>Output:<b>\n<code>No Output</code>")
        await status_message.delete()
    try:
        return await locals()["_aexec_"](client, message)
    except Exception:
        pass

@WhiterX.on_message(filters.command("speedtest", Config.TRIGGER))
async def speed_test(c: WhiterX, m: Message):
    user_id = m.from_user.id
    if not is_dev(user_id):
        return
    try:
        running = await m.reply("<code>Rodando Speedtest...</code>") 
        test = Speedtest()
        bs = test.get_best_server()
        await running.edit("<code>Fazendo teste de Download...</code>")
        dl = round(test.download() / 1024 / 1024, 2)
        await running.edit("<code>Fazendo teste de Upload...</code>")
        ul = round(test.upload() / 1024 / 1024, 2)
        await running.edit("<code>Getting some informations...</code>")
        test.results.share()
        result = test.results.dict()
        name = result["server"]["name"]
        host = bs["sponsor"]
        ping = bs["latency"]
        isp = result["client"]["isp"]   
        country = result["server"]["country"] 
        cc = result["server"]["cc"]
        path = (result["share"]) 
        response = await m.reply_photo(
            photo=path, caption=f"🌀 <b>Name:</b> <code>{name}</code>\n🌐 <b>Host:</b> <code>{host}</code>\n🏁 <b>Country:</b> <code>{country}, {cc}</code>\n\n🏓 <b>Ping:</b> <code>{ping} ms</code>\n🔽 <b>Download:</b> <code>{dl} Mbps</code>\n🔼 <b>Upload:</b> <code>{ul} Mbps</code>\n🖥  <b>ISP:</b> <code>{isp}</code>"
        )
        await running.delete()
    except Exception as e:
        await c.send_err(e)
        return
    

@WhiterX.on_message(filters.command("ping", Config.TRIGGER))
async def ping(c: WhiterX, m: Message):
    user_id = m.from_user.id
    if not is_dev(user_id):
        return
    first = datetime.now()
    sent = await m.reply_text("<b>Pong!</b>")
    second = datetime.now()
    await sent.edit_text(
        f"<b>Pong!</b> <code>{(second - first).microseconds / 1000}</code>ms"
    )

@WhiterX.on_message(filters.command("stats", Config.TRIGGER))
async def stats(c: WhiterX, m: Message):
    msg = await m.reply("<i>Getting information from task manager...</i>")

    # Getting infos from task manager
    try:
        mem = psutil.virtual_memory()
        total_mem_gb = round(mem.total / (1024 ** 3), 2)
        used_mem_gb = round(mem.used / (1024 ** 3), 2)
        mem_percent = mem.percent

        disk = psutil.disk_usage('/')
        total_disk_gb = round(disk.total / (1024 ** 3), 2)
        used_disk_gb = round(disk.used / (1024 ** 3), 2)
        
        cpu_freq = psutil.cpu_freq().current / 1000
        cpu_percent = psutil.cpu_percent()

        uptime_bot = time_formatter(time.time() - START_TIME)
        boot_machine = boot_time = psutil.boot_time()
        uptime_machine = time_formatter(time.time() - boot_machine)

        system_info = str(c.system_version)

        text = "<b>System Info:</b> <i>{}</i>\n\n<b>Bot Uptime:</b> <i>{}</i>\n<b>Machine Uptime:</b> <i>{}</i>\n<b>RAM Memory:</b> <i>{} GB/{} GB ({}%)</i>\n<b>Disk Memory:</b> <i>{} GB/{} GB</i>\n<b>Processor Usage:</b> <i>{} GHz ({}%)</i>".format(system_info, uptime_bot, uptime_machine, used_mem_gb, total_mem_gb, mem_percent, used_disk_gb, total_disk_gb, cpu_freq, cpu_percent)
    except Exception as e:
        text = "<b>⚠️ An error occurred in My Operating System:</b> <i>Unable to obtain information from:</i>\n<code>- Task Manager</code>\n\n<b>Due to:</b> {}".format(e)
    await msg.edit(text)
