"""
import re
data = 'window.QRLogin.code = 200; window.QRLogin.uuid = "gb8UuMBZyA==";'
ret = re.findall('uuid = "(.*)";',data)[0]
print(ret)
"""

from bs4 import BeautifulSoup


def xml_parse(text):
    """
    解析重定微信重定向返回的身份凭证xml
    :param text:
    :return:
    """
    result = {}
    soup = BeautifulSoup(text, 'html.parser')
    tag_list = soup.find(name='error').find_all()  # 从包裹error标签中获取所有childrentag
    for tag in tag_list:
        result[tag.name] = tag.text
    return result


if __name__ == '__main__':
    v = "<error><ret>0</ret><message></message><skey>@crypt_ac8812af_0ffde1190007c7c044bc31ae51407c45</skey><wxsid>fRwfacRtjRFpEIwt</wxsid><wxuin>1062220661</wxuin><pass_ticket>0M1plebTzNQ%2FKaSIfTfk65laCSXUWmjpxvJEerZSnBaEDjNIyOafaQLtpQBhnCDa</pass_ticket><isgrayscale>1</isgrayscale></error>"
    res = xml_parse(v)
    print(res)
