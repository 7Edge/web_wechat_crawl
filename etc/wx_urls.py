#!/usr/bin/env python
# coding=UTF-8
# author: zhangjiaqi <1399622866@qq.com>
# File: wx_urls
# Date: 5/10/2019
"""
存放要访问wx地址格式化字符串
"""

qcode_img_id_url = "https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&redirect_uri=https%3A%2F%2Fwx.qq.com%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxnewloginpage&fun=new&lang=zh_CN&_={0}"
poll_check_loginprocessing_stat_url = "https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid={0}&tip=0&r=-976036168&_={1}"
init_ui_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=-979112921&lang=zh_CN&pass_ticket={0}"
get_contact_list_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?lang=zh_CN&pass_ticket={0}&r={1}&seq=0&skey={2}"
avatar_url = "https://wx.qq.com{0}&username={1}&skey={2}"
poll_msg_url = "https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck?r={ctime}&skey={skey}&sid={sid}&uin={uin}&deviceid=e700290354098676&synckey={synckey}&_=1557456028250"
get_msg_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync?sid={sid}&skey={skey}&lang=zh_CN&pass_ticket={pass_ticket}"

if __name__ == '__main__':
    pass
