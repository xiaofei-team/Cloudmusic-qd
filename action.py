# -*- encoding: utf-8 -*-
"""
@FILE    :   action.py
@DSEC    :   网易云音乐签到刷歌脚本
@AUTHOR  :   Secriy
@DATE    :   2020/08/25
@VERSION :   2.6
"""

import os
import random
import time
import requests
import base64
import binascii
import argparse
import hashlib
from Crypto.Cipher import AES
import json


# Get the arguments input.
# 用于获取命令行参数并返回dict
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("phone", help="Your Phone Number.")
    parser.add_argument("password", help="The plaint text or MD5 value of the password.")
    parser.add_argument("-t", dest="tg_bot_key", nargs=2, help="The Token and Chat ID of your telegram bot.")
    args = parser.parse_args()

    return {
        "phone": args.phone,
        "password": args.password,
        "tg_bot_key": args.tg_bot_key,
    }


# Calculate the MD5 value of text
# 计算字符串的32位小写MD5值
def calc_md5(text):
    md5_text = hashlib.md5(text.encode(encoding="utf-8")).hexdigest()
    return md5_text


# AES Encrypt
# 用于进行AES加密操作
def aes_encrypt(text, sec_key):
    pad = 16 - len(text) % 16
    text = text + pad * chr(pad)
    encryptor = AES.new(sec_key.encode("utf8"), 2, b"0102030405060708")
    ciphertext = encryptor.encrypt(text.encode("utf8"))
    ciphertext = str(base64.b64encode(ciphertext), encoding="utf-8")
    return ciphertext


# RSA Encrypt
# 用于进行RSA加密
def rsa_encrypt(text, pub_key, modulus):
    text = text[::-1]
    rs = int(text.encode("utf-8").hex(), 16) ** int(pub_key, 16) % int(modulus, 16)
    return format(rs, "x").zfill(256)


# 推送类，包含所有推送函数
class Push:
    def __init__(self, text, args):
        self.text = text
        self.info = args

    # 执行指定的推送流程
    def do_push(self):
        # ServerChan
        try:
            self.server_chan_push()
        except Exception as err:
            print(err)
        # Bark
        try:
            self.bark_push()
        except Exception as err:
            print(err)
        # Telegram
        try:
            self.telegram_push()
        except Exception as err:
            print(err)
        # pushplus
        try:
            self.push_plus_push()
        except Exception as err:
            print(err)
        # 企业微信
        try:
            self.wecom_id_push()
        except Exception as err:
            print(err)
        # Qmsg
        try:
            self.qmsg_push()
        except Exception as err:
            print(err)
        # Ding
        try:
            self.ding_talk_push()
        except Exception as err:
            print(err)

    # Server Chan Turbo Push
    def server_chan_push(self):
        if not self.info["sc_key"]:
            return
        arg = self.info["sc_key"]
        url = "https://sctapi.ftqq.com/{0}.send".format(arg[0])
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        content = {"title": "网易云打卡", "desp": self.text}
        ret = requests.post(url, headers=headers, data=content)
        print("ServerChan: " + ret.text)

    # Telegram Bot Push
    def telegram_push(self):
        if not self.info["tg_bot_key"]:
            return
        arg = self.info["tg_bot_key"]
        url = "https://tg.angelxf.ml/bot{0}/sendMessage".format(arg[0])
        data = {
            "chat_id": arg[1],
            "text": self.text,
        }
        ret = requests.post(url, data=data)
        print("Telegram: " + ret.text)

    # Bark Push
    def bark_push(self):
        if not self.info["bark_key"]:
            return
        arg = self.info["bark_key"]
        data = {"title": "网易云打卡", "body": self.text}
        headers = {"Content-Type": "application/json;charset=utf-8"}
        url = "https://api.day.app/{0}/?isArchive={1}".format(arg[0], arg[1])
        ret = requests.post(url, json=data, headers=headers)
        print("Bark: " + ret.text)

    # PushPlus Push
    def push_plus_push(self):
        if not self.info["push_plus_key"]:
            return
        arg = self.info["push_plus_key"]
        url = "http://www.pushplus.plus/send?token={0}&title={1}&content={2}&template={3}".format(
            arg[0], "网易云打卡", self.text, "html"
        )
        ret = requests.get(url)
        print("pushplus: " + ret.text)

    # Wecom Push
    def wecom_id_push(self):
        if not self.info["wecom_key"]:
            return
        arg = self.info["wecom_key"]
        body = {
            "touser": "@all",
            "msgtype": "text",
            "agentid": arg[1],
            "text": {"content": self.text},
            "safe": 0,
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800,
        }
        access_token = requests.get(
            "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={0}&corpsecret={1}".format(str(arg[0]), arg[2])
        ).json()["access_token"]
        res = requests.post(
            "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={0}".format(access_token),
            data=json.dumps(body),
        )
        ret = res.json()
        if ret["errcode"] != 0:
            print("微信推送配置错误")
        else:
            print("Wecom: " + ret)

    # Qmsg Push
    def qmsg_push(self):
        if not self.info["qmsg_key"]:
            return
        arg = self.info["qmsg_key"]
        url = "https://qmsg.zendee.cn/send/{0}?msg={1}".format(arg[0], self.text)
        ret = requests.post(url)
        print("Qmsg: " + ret.text)

    # Ding Talk Push
    def ding_talk_push(self):
        if not self.info["ding_token"]:
            return
        arg = self.info["ding_token"]
        url = "https://oapi.dingtalk.com/robot/send?access_token={0}".format(arg[0])
        header = {"Content-Type": "application/json"}
        data = json.dumps({"msgtype": "text", "text": {"content": "【CMLU】\n\n" + self.text}})
        ret = requests.post(url, headers=header, data=data)
        print("Ding: " + ret.text)


# 加密类，实现网易云音乐前端加密流程
class Encrypt:
    def __init__(self):
        self.modulus = (
            "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629"
            "ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d"
            "813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7 "
        )
        self.nonce = "0CoJUm6Qyw8W8jud"
        self.pubKey = "010001"

    def encrypt(self, text):
        # Random String Generator
        sec_key = str(binascii.hexlify(os.urandom(16))[:16], encoding="utf-8")
        enc_text = aes_encrypt(aes_encrypt(text, self.nonce), sec_key)
        enc_sec_key = rsa_encrypt(sec_key, self.pubKey, self.modulus)
        return {"params": enc_text, "encSecKey": enc_sec_key}


# 网易云音乐类，实现脚本基础流程
class CloudMusic:
    def __init__(self, phone, country_code, password):
        self.session = requests.Session()
        self.enc = Encrypt()
        self.phone = phone
        self.csrf = ""
        self.nickname = ""
        self.uid = ""
        self.login_data = self.enc.encrypt(
            json.dumps({"phone": phone, "countrycode": country_code, "password": password, "rememberLogin": "true"})
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/84.0.4147.89 "
            "Safari/537.36",
            "Referer": "http://music.163.com/",
            "Accept-Encoding": "gzip, deflate",
        }

    # 登录流程
    def login(self):
        login_url = "https://music.163.com/weapi/login/cellphone"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/84.0.4147.89 Safari/537.36",
            "Referer": "http://music.163.com/",
            "Accept-Encoding": "gzip, deflate",
            "Cookie": "os=pc; osver=Microsoft-Windows-10-Professional-build-10586-64bit; appver=2.0.3.131777; "
            "channel=netease; __remember_me=true;",
        }
        res = self.session.post(url=login_url, data=self.login_data, headers=headers)
        ret = json.loads(res.text)
        if ret["code"] == 200:
            self.csrf = requests.utils.dict_from_cookiejar(res.cookies)["__csrf"]
            self.nickname = ret["profile"]["nickname"]
            self.uid = ret["account"]["id"]
            level = self.get_level()
            text = '"{nickname}" 登录成功，当前等级：{level}\n\n距离升级还需听{count}首歌\n\n距离升级还需登录{days}天'.format(
                nickname=self.nickname,
                level=level["level"],
                count=level["nextPlayCount"] - level["nowPlayCount"],
                days=level["nextLoginCount"] - level["nowLoginCount"],
            )
        else:
            text = "账号 {0} 登录失败: ".format(self.phone) + str(ret["code"])
        return text

    # Get the level of account.
    # 获取用户的等级信息等
    def get_level(self):
        url = "https://music.163.com/weapi/user/level?csrf_token=" + self.csrf
        res = self.session.post(url=url, data=self.login_data, headers=self.headers)
        ret = json.loads(res.text)
        return ret["data"]

    # 执行用户的签到流程
    def sign(self, tp=0):
        sign_url = "https://music.163.com/weapi/point/dailyTask?{csrf}".format(csrf=self.csrf)
        res = self.session.post(url=sign_url, data=self.enc.encrypt('{{"type":{0}}}'.format(tp)), headers=self.headers)
        ret = json.loads(res.text)
        sign_type = "安卓端" if tp == 0 else "PC/Web端"
        if ret["code"] == 200:
            text = "{0}签到成功，经验+{1}".format(sign_type, str(ret["point"]))
        elif ret["code"] == -2:
            text = "{0}今天已经签到过了".format(sign_type)
        else:
            text = "签到失败 " + str(ret["code"]) + "：" + ret["message"]
        return text

    # 获取用户的推荐歌单
    def get_recommend_playlists(self):
        recommend_url = "https://music.163.com/weapi/v1/discovery/recommend/resource"
        res = self.session.post(
            url=recommend_url, data=self.enc.encrypt('{"csrf_token":"' + self.csrf + '"}'), headers=self.headers
        )
        ret = json.loads(res.text)
        playlists = []
        if ret["code"] == 200:
            playlists.extend([(d["id"]) for d in ret["recommend"]])
        else:
            print("获取推荐歌曲失败 " + str(ret["code"]) + "：" + ret["message"])
        return playlists

    # 获取用户的收藏歌单
    def get_subscribe_playlists(self):
        private_url = "https://music.163.com/weapi/user/playlist?csrf_token=" + self.csrf
        res = self.session.post(
            url=private_url,
            data=self.enc.encrypt(json.dumps({"uid": self.uid, "limit": 1001, "offset": 0, "csrf_token": self.csrf})),
            headers=self.headers,
        )
        ret = json.loads(res.text)
        subscribed_lists = []
        if ret["code"] == 200:
            for li in ret["playlist"]:
                if li["subscribed"]:
                    subscribed_lists.append(li["id"])
        else:
            print("个人订阅歌单获取失败 " + str(ret["code"]) + "：" + ret["message"])
        return subscribed_lists

    # 获取某一歌单内的所有音乐ID
    def get_list_musics(self, mlist):
        detail_url = "https://music.163.com/weapi/v6/playlist/detail?csrf_token=" + self.csrf
        musics = []
        for m in mlist:
            res = self.session.post(
                url=detail_url,
                data=self.enc.encrypt(json.dumps({"id": m, "n": 1000, "csrf_token": self.csrf})),
                headers=self.headers,
            )
            ret = json.loads(res.text)
            musics.extend([i["id"] for i in ret["playlist"]["trackIds"]])
        return musics

    # 获取任务歌单池内的所有音乐ID
    def get_task_musics(self):
        random.seed(time.time())
        musics = []
        recommend_musics = self.get_list_musics(self.get_recommend_playlists())
        subscribe_musics = self.get_list_musics(self.get_subscribe_playlists())
        musics.extend(random.sample(recommend_musics, 320) if len(recommend_musics) > 320 else recommend_musics)
        musics.extend(random.sample(subscribe_musics, 200) if len(subscribe_musics) > 200 else subscribe_musics)
        return musics

    # 任务
    def task(self):
        feedback_url = "http://music.163.com/weapi/feedback/weblog"
        post_data = json.dumps(
            {
                "logs": json.dumps(
                    list(
                        map(
                            lambda x: {
                                "action": "play",
                                "json": {
                                    "download": 0,
                                    "end": "playend",
                                    "id": x,
                                    "sourceId": "",
                                    "time": 240,
                                    "type": "song",
                                    "wifi": 0,
                                },
                            },
                            self.get_task_musics(),
                        )
                    )
                )
            }
        )
        res = self.session.post(url=feedback_url, data=self.enc.encrypt(post_data))
        ret = json.loads(res.text)
        if ret["code"] == 200:
            text = "刷听歌量成功"
        else:
            text = "刷听歌量失败 " + str(ret["code"]) + "：" + ret["message"]
        return text


# 执行任务，传递参数，推送结果
def run_task(info, phone, password):
    country_code = "86"
    if "+" in phone:
        country_code = str(phone).split("+")[0]
        phone = str(phone).split("+")[1]
    # 初始化
    app = CloudMusic(phone, country_code, password)
    # 登录
    res_login = app.login()
    print(res_login, end="\n\n")
    if "400" in res_login:
        print(res_login)
        print(30 * "=")
        return
    # PC/Web端签到
    res_sign = app.sign()
    print(res_sign, end="\n\n")
    # 安卓端签到
    res_m_sign = app.sign(1)
    print(res_m_sign, end="\n\n")
    # Music Task
    res_task = "刷听歌量失败"
    for i in range(1):
        res_task = app.task()
        print(res_task)
    print(30 * "=")
    # 推送
    message = res_login + "\n\n" + res_sign + "\n\n" + res_m_sign + "\n\n" + res_task
    Push(message, info).do_push()
    print(30 * "=")


# 执行多个任务
def tasks_pool(infos):
    phone_list = infos["phone"].split(",")
    passwd_list = infos["password"].split(",")
    # Run tasks
    for k, v in enumerate(phone_list):
        print(30 * "=")
        if not passwd_list[k]:
            break
        if len(passwd_list[k]) == 32:
            run_task(infos, phone_list[k], passwd_list[k])
        else:
            run_task(infos, phone_list[k], calc_md5(passwd_list[k]))


if __name__ == "__main__":
    # Get arguments
    tasks_pool(get_args())
