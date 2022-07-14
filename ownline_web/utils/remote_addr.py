
def get_remote_addr(request):
    if 'X-Forwarded-For' in request.headers:
        proxy_data = request.headers['X-Forwarded-For']
        ip_list = proxy_data.split(',')
        return ip_list[0]
    else:
        return request.remote_addr
