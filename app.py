import re
import time
import requests
import json

from flask import Flask, render_template, session, jsonify, request

from tools import xml_parse
from etc import wx_urls

app = Flask(__name__)
app.secret_key = '1231sdfasdf'
app.config['DEBUG'] = True


@app.route('/login')
def login():  # 通过客户端扫描二维码的方式登陆页面。
    ctime = int(time.time() * 1000)  #
    qcode_url = wx_urls.qcode_img_id_url.format(ctime)
    """
    qcode_url: 是微信web首页通过ajax请求发送到微信后端，目的是获取一个二维码的标识，在页面上展示。二维码就是后端与用户绑定的”连接线“。
               只要微信客户端扫描了这个二维码就可以告诉后端，
    参数：appid是固定的是微信自己的web聊天方式appid
         _ 是时间戳，必须带上当前的，则是唯一要更改的
    """
    rep = requests.get(
        url=qcode_url
    )
    # print(rep.text) # window.QRLogin.code = 200; window.QRLogin.uuid = "gb8UuMBZyA==";
    qcode = re.findall('uuid = "(.*)";', rep.text)[0]
    session['qcode'] = qcode  # 将这个放到session中,因为后面的客户端发起的去长轮询登陆状态消息时需要每次都带上。
    # 因为后端十一这个qcode作为当前长轮询消息队列的唯一标识，当用户登陆后，这个标识会绑定认证用户信息。当用户有消息时后端才会根据绑定的用户信息找到
    # 对应的消息队列，把消息放入，长轮询才会收取到实时消息。
    return render_template('login.html', qcode=qcode)


@app.route('/check/login')
def check_login():  # 前端通过ajax长轮询视图，视图主要对实时进行同步获取，如果没有数据则hang住。除非超时返回。这种情况前端回再次轮询。
    # 设置超时和你秒数可以避免tcp连接因为过长而断开。
    qcode = session['qcode']
    ctime = int(time.time() * 1000)
    check_login_url = wx_urls.poll_check_loginprocessing_stat_url.format(qcode, ctime)

    rep = requests.get(
        url=check_login_url
    )
    result = {'code': 408}

    if 'window.code=408' in rep.text:
        # 用户未扫码
        result['code'] = 408
    elif 'window.code=201' in rep.text:
        # 用户扫码，获取头像
        result['code'] = 201
        result['avatar'] = re.findall("window.userAvatar = '(.*)';", rep.text)[0]
    elif 'window.code=200' in rep.text:
        # 用户确认登录
        redirect_uri = re.findall('window.redirect_uri="(.*)";', rep.text)[0]
        # https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=ASEHe9Kr5Hq0PITHG1dXEBS8@qrticket_0&uuid=gfbq6fFg9Q==&lang=zh_CN&scan=1529986929&fun=new&version=v2
        # https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=ATEkrWXwLgR3QjDuYsx-dpzN@qrticket_0&uuid=obFFB7YwVA==&lang=zh_CN&scan=1529986454
        redirect_uri = redirect_uri + "&fun=new&version=v2"
        ru = requests.get(url=redirect_uri)

        # <error><ret>0</ret><message></message><skey>@crypt_ac8812af_0ffde1190007c7c044bc31ae51407c45</skey><wxsid>fRwfacRtjRFpEIwt</wxsid><wxuin>1062220661</wxuin><pass_ticket>0M1plebTzNQ%2FKaSIfTfk65laCSXUWmjpxvJEerZSnBaEDjNIyOafaQLtpQBhnCDa</pass_ticket><isgrayscale>1</isgrayscale></error>
        ticket_dict = xml_parse(ru.text)
        session['ticket_dict'] = ticket_dict
        session['init_cookies'] = ru.cookies.get_dict()

        result['code'] = 200

    return jsonify(result)


@app.route('/index')
def index():
    pass_ticket = session['ticket_dict']['pass_ticket']
    # 利用重定向获取的身份信息去获取初始化信息.
    init_url = wx_urls.init_ui_url.format(pass_ticket)

    rep = requests.post(
        url=init_url,
        json={
            'BaseRequest': {
                'DeviceID': "e700290354098676",
                'Sid': session['ticket_dict']['wxsid'],
                'Skey': session['ticket_dict']['skey'],
                'Uin': session['ticket_dict']['wxuin'],
            }
        }
    )
    rep.encoding = 'utf-8'

    # 将cookie拿到，保存到会话中（会话再用户端和微信之间起到了”数据上下文作用“）
    print('init请求cookie有吗？', rep.cookies.get_dict())

    init_user_dict = rep.json()  # 如果响应返回的时json格式，就可以通过json（）获取
    # 将初始化的响应信息放入到session中.数据太大放不进去，所以只放入synckey吧
    session['synckey'] = init_user_dict['SyncKey']
    print(init_user_dict)
    print()
    return render_template('index.html', init_user_dict=init_user_dict)


@app.route('/contacts')
def contacts():
    pass_ticket = session['ticket_dict']['pass_ticket']
    skey = session['ticket_dict']['skey']
    ctime = int(time.time() * 1000)
    cookies = session['init_cookies']

    contact_url = wx_urls.get_contact_list_url.format(pass_ticket, ctime, skey)

    response_contacts = requests.get(url=contact_url,
                                     headers={
                                         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
                                         'Host': 'wx.qq.com'
                                     },
                                     cookies=cookies)
    print('响应的默认编码：', response_contacts.encoding)
    response_contacts.encoding = 'utf-8'

    print(response_contacts.json())

    return render_template('contacts.html', **{'data': response_contacts.json()})


@app.route('/avatar')
def avatar():
    prev = request.args.get('prev')
    username = request.args.get('username')
    skey = request.args.get('skey')

    url = wx_urls.avatar_url.format(prev, username, skey)

    res_avatar = requests.get(url=url,
                              cookies=session['init_cookies'])

    return res_avatar.content


# 轮询普通消息接口
@app.route('/sync_msg')
def syncmessage():
    result = {'code': 1000,
              'data': None}

    ctime = int(time.time() * 1000)
    pass_ticket = session['ticket_dict']['pass_ticket']
    skey = session['ticket_dict']['skey']
    sid = session['ticket_dict']['wxsid']
    uin = session['ticket_dict']['wxuin']
    cookies = session['init_cookies']
    synckey = list()
    for item in session['synckey']['List']:
        synckey.append(str(item['Key']) + '_' + str(item['Val']))

    synckey_str = '|'.join(synckey)
    print('synckey字符串是:', synckey_str)
    url = wx_urls.poll_msg_url.format(ctime=ctime, skey=skey, sid=sid, uin=uin, synckey=synckey_str)
    res_check_msg = requests.get(url=url, cookies=cookies)
    print(res_check_msg.text)

    if 'selector:"2"' in res_check_msg.text:  # 说明有消息， 则获取消息
        # 获取消息
        msg_url = wx_urls.get_msg_url.format(pass_ticket=pass_ticket, sid=sid, skey=skey)
        payload = {
            'BaseRequest': {
                'DeviceID': 'e700290354098676',
                'Sid': session['ticket_dict']['wxsid'],
                'Skey': session['ticket_dict']['skey'],
                'Uin': session['ticket_dict']['wxuin']
            },
            'SyncKey': session['synckey'],
            'rr': str(time.time())
        }
        res_msg = requests.post(url=msg_url, json=payload)
        res_msg.encoding = 'utf-8'
        msg_data = json.loads(res_msg.text)
        session['synckey'] = msg_data['SyncKey']
        msg_list = list()
        for msg in msg_data.get('AddMsgList'):
            if msg['MsgType'] == 1:
                msg_list.append(msg['Content'])

        result['data'] = '|'.join(msg_list)
    else:
        result['code'] = 1001
    return jsonify(result)


if __name__ == '__main__':
    app.run()
