import urequest1
import urequests
import ujson
from machine import Pin
import utime
import gc
import netman
OPAID = <OPA_ID_WE_WANT_TO_CHECK>

_hextobyte_cache = None

def unquote(string):
    """unquote('abc%20def') -> b'abc def'."""
    global _hextobyte_cache

    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.
    if not string:
        return b''

    if isinstance(string, str):
        string = string.encode('utf-8')

    bits = string.split(b'%')
    if len(bits) == 1:
        return string

    res = [bits[0]]
    append = res.append

    # Build cache for hex to char mapping on-the-fly only for codes
    # that are actually used
    if _hextobyte_cache is None:
        _hextobyte_cache = {}

    for item in bits[1:]:
        try:
            code = item[:2]
            char = _hextobyte_cache.get(code)
            if char is None:
                char = _hextobyte_cache[code] = bytes([int(code, 16)])
            append(char)
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)

    return b''.join(res)

def getSignSession():
    headers = {
            'Host': ' app.workato.com',
            'User-Agent': ' Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0',
            'Accept': ' application/json, text/plain, */*',
            'Accept-Language': ' en-US,en;q=0.5',
            'Referer': ' https://app.workato.com/users/sign_in',
            'Content-Type': ' application/json',
            'Connection': ' keep-alive',
            'Sec-Fetch-Dest': ' empty',
            'Sec-Fetch-Mode': ' cors',
            'Sec-Fetch-Site': ' same-origin'
        }
    response = urequest1.get('https://app.workato.com/web_api/auth_user.json', headers=headers)
    print(response.text)
    x_csrf_token = response.cookies["XSRF-TOKEN"]
    _workato_app_session = response.cookies["_workato_app_session"]
    
    x_csrf_token = unquote(x_csrf_token).decode('utf-8').split(';')[0]
    _workato_app_session = unquote(_workato_app_session).decode('utf-8').split(';')[0]
    response.close()
    return x_csrf_token, _workato_app_session


def getSession(x_csrf_token, _workato_app_session):
    headers = {
            'Host': ' app.workato.com',
            'User-Agent': ' Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0',
            'Accept': ' application/json, text/plain, */*',
            'Accept-Language': ' en-US,en;q=0.5',
            'Referer': ' https://app.workato.com/users/sign_in',
            'X-CSRF-TOKEN': x_csrf_token,
            'X-Requested-With': ' XMLHttpRequest',
            'Content-Type': ' application/json',
            'Origin': ' https://app.workato.com',
            'Connection': ' keep-alive',
            'Cookie': '; _workato_app_session=' + _workato_app_session,
            'Sec-Fetch-Dest': ' empty',
            'Sec-Fetch-Mode': ' cors',
            'Sec-Fetch-Site': ' same-origin'
        }
    
    body = '{"user":{"email":"WORKATO_ACCOUNT,"password":"WORKATO_PASSWORD"}}'
    response = urequest1.post('https://app.workato.com/users/sign_in.json', data=body, headers=headers)
    print(response.text)
    
    x_csrf_token = response.cookies["XSRF-TOKEN"]
    _workato_app_session = response.cookies["_workato_app_session"]
    
    x_csrf_token = unquote(x_csrf_token).decode('utf-8').split(';')[0]
    _workato_app_session = unquote(_workato_app_session).decode('utf-8').split(';')[0]
    response.close()
    return x_csrf_token, _workato_app_session
 

def getOPA(xsrf_token, workato_app_session):
    headers = {
            'Host': ' app.workato.com',
            'User-Agent': ' Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0',
            'Accept': ' text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': ' en-US,en;q=0.5',
            'Connection': ' keep-alive',
            'Cookie': ' XSRF-TOKEN=' + xsrf_token + '; _workato_app_session=' + workato_app_session + '; ',
            'Upgrade-Insecure-Requests': ' 1',
            'Sec-Fetch-Dest': ' document',
            'Sec-Fetch-Mode': ' navigate',
            'Sec-Fetch-Site': ' none',
            'Sec-Fetch-User': ' ?1'
        }
    
    response = urequests.get('https://app.workato.com/on_prem_groups.json', headers=headers)
    #print(response.json())
    result = response.json()
    response.close()
    
    for key in result["result"]:
        opa_id = key["id"]
        #print(opa_id)
        if opa_id == OPAID:
            getOPADetails_res = getOPADetails(xsrf_token, workato_app_session, opa_id)
            for key_details in getOPADetails_res["result"]["agents"]:
                #print(key_details)
                opa_child_id = key_details["id"]
                opa_child_name  = key_details["name"]
                getOPA_Child_Details_res = getOPAChildDetails(xsrf_token, workato_app_session, opa_id, opa_child_id)["active"]
                #print(getOPA_Child_Details_res)
                
                if opa_id == OPAID and getOPA_Child_Details_res == True:
                    print("active")
                    ledoff()
                    
                if opa_id == OPAID and getOPA_Child_Details_res == False:
                    print("inactive")
                    ledon()
                    
    return
    
def getOPADetails(xsrf_token, workato_app_session, opa_id):
    headers = {
            'Host': ' app.workato.com',
            'User-Agent': ' Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0',
            'Accept': ' text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': ' en-US,en;q=0.5',
            'Connection': ' keep-alive',
            'Cookie': ' XSRF-TOKEN=' + xsrf_token + '; _workato_app_session=' + workato_app_session + '; ',
            'Upgrade-Insecure-Requests': ' 1',
            'Sec-Fetch-Dest': ' document',
            'Sec-Fetch-Mode': ' navigate',
            'Sec-Fetch-Site': ' none',
            'Sec-Fetch-User': ' ?1'
        }
    response = urequest1.get('https://app.workato.com/on_prem_groups/' + str(opa_id) + '.json', headers=headers)
    result = response.json()
    response.close()
    return result
    
def getOPAChildDetails(xsrf_token, workato_app_session, opa_id, opa_child_id):
    headers = {
            'Host': ' app.workato.com',
            'User-Agent': ' Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0',
            'Accept': ' text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': ' en-US,en;q=0.5',
            'Connection': ' keep-alive',
            'Cookie': ' XSRF-TOKEN=' + xsrf_token + '; _workato_app_session=' + workato_app_session + '; ',
            'Upgrade-Insecure-Requests': ' 1',
            'Sec-Fetch-Dest': ' document',
            'Sec-Fetch-Mode': ' navigate',
            'Sec-Fetch-Site': ' none',
            'Sec-Fetch-User': ' ?1'
        }
    response = urequests.get('https://app.workato.com/on_prem_groups/' + str(opa_id) + '/agents/' + str(opa_child_id) + '/status.json', headers=headers)
    result = response.json()
    response.close()
    return result

def main():
    x_csrf_token, _workato_app_session = getSignSession()
    x_csrf_token, _workato_app_session = getSession(x_csrf_token, _workato_app_session)
    getOPA(x_csrf_token, _workato_app_session)

def ledon():
    print("LEDON")
    led = Pin(28, Pin.OUT)
    led.high()
    utime.sleep(1)

def ledoff():
    print("LEDOFF")
    led = Pin(28, Pin.OUT)
    led.low()
    utime.sleep(1)
import sys

country = 'SG'
ssid = 'SSID'
password = 'SSID_PASSWORD'
wifi_connection = netman.connectWiFi(ssid,password,country)
while True:
    try: 
        main()
        print("end")
        utime.sleep(10)
    except OSError as e:
        print("error")
        sys.exit()
    
