import re
import time
import requests

from flask import Flask, render_template, session, jsonify

from tools import xml_parse

app = Flask(__name__)
app.secret_key = '1231sdfasdf'


@app.route('/login')
def login():  # 通过客户端扫描二维码的方式登陆页面。
    ctime = int(time.time() * 1000)  #
    qcode_url = "https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&redirect_uri=https%3A%2F%2Fwx.qq.com%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxnewloginpage&fun=new&lang=zh_CN&_={0}".format(
        ctime)
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
def check_login():
    qcode = session['qcode']
    ctime = int(time.time() * 1000)
    check_login_url = 'https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid={0}&tip=0&r=-976036168&_={1}'.format(
        qcode, ctime)

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
        print(redirect_uri)
        # https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=ASEHe9Kr5Hq0PITHG1dXEBS8@qrticket_0&uuid=gfbq6fFg9Q==&lang=zh_CN&scan=1529986929&fun=new&version=v2
        # https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=ATEkrWXwLgR3QjDuYsx-dpzN@qrticket_0&uuid=obFFB7YwVA==&lang=zh_CN&scan=1529986454
        redirect_uri = redirect_uri + "&fun=new&version=v2"
        ru = requests.get(url=redirect_uri)

        # <error><ret>0</ret><message></message><skey>@crypt_ac8812af_0ffde1190007c7c044bc31ae51407c45</skey><wxsid>fRwfacRtjRFpEIwt</wxsid><wxuin>1062220661</wxuin><pass_ticket>0M1plebTzNQ%2FKaSIfTfk65laCSXUWmjpxvJEerZSnBaEDjNIyOafaQLtpQBhnCDa</pass_ticket><isgrayscale>1</isgrayscale></error>
        ticket_dict = xml_parse(ru.text)
        session['ticket_dict'] = ticket_dict
        result['code'] = 200

    return jsonify(result)


@app.route('/index')
def index():
    pass_ticket = session['ticket_dict']['pass_ticket']
    init_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=-979112921&lang=zh_CN&pass_ticket={0}".format(
        pass_ticket)

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

    init_user_dict = rep.json()
    print(init_user_dict)

    return render_template('index.html', init_user_dict=init_user_dict)


if __name__ == '__main__':
    app.run()
