def ipaddress(address='ip'):
    import urllib.request

    host = 'http://jisuip.market.alicloudapi.com'
    path = '/ip/location'
    method = 'GET'
    appcode = '7edd69ba18e74306b5ebcbb9dd7471fa'
    querys = f'ip={address}'
    bodys = {}
    url = host + path + '?' + querys
    request = urllib.request.Request(url)
    request.add_header('Authorization', 'APPCODE ' + appcode)
    response = urllib.request.urlopen(request)
    content = response.read()
    if content:
        obj = eval(content.decode('utf-8'))
        result = obj['result']
        return f'| {result["type"]} | {result["country"]}->{result["province"]}->{result["city"]}->{result["town"]}'
    else:
        return "404"

