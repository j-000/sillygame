from flask import jsonify



def safe_int(v):
    try:
        return int(v)
    except Exception:
        return 1


def jinja_paginate(results, url, start, limit):
    start = safe_int(start)
    limit = safe_int(limit)
    count = len(results)

    if start > count or limit < 0 or limit > 20:
        return {'success': False, 'message':f'Invalid parameters. Try {url}?start=1&limit=20'}

    obj = {'start': start, 'limit': limit, 'count': count}

    if start == 1:
        obj['previous'] = None
    else:
        start_copy = max(1, start - limit)
        limit_copy = start - 1
        obj['previous'] = url + '?start=%d&limit=%d' % (start_copy, limit_copy)

    if start + limit > count:
        obj['next'] = None
    else:
        start_copy = start + limit
        obj['next'] = url + '?start=%d&limit=%d' % (start_copy, limit)
    obj['results'] = results[(start - 1):(start - 1 + limit)]
    return obj


def paginate(results, serializer, url, start, limit):
    start = safe_int(start)
    limit = safe_int(limit)
    count = len(results)

    if count > 0 and start > count or limit < 0 or limit > 20:
        return {'success': False, 'message':f'Invalid parameters. Try {url}?start=1&limit=20'}

    obj = {'start': start, 'limit': limit, 'count': count}

    if start == 1:
        obj['previous'] = ''
    else:
        start_copy = max(1, start - limit)
        limit_copy = start - 1
        obj['previous'] = url + '?start=%d&limit=%d' % (start_copy, limit_copy)

    if start + limit > count:
        obj['next'] = ''
    else:
        start_copy = start + limit
        obj['next'] = url + '?start=%d&limit=%d' % (start_copy, limit)
    obj['results'] = serializer.dump(results[(start - 1):(start - 1 + limit)], many=True)
    return obj