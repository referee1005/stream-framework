from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from feedly.feeds.love_feed import LoveFeed
import bisect
import random
import unittest
from feedly.connection import get_redis_connection
from feedly.utils import get_user_model


@staff_member_required
def benchmark(request):
    return 'dangerous'
    from feedly import benchmarks
    suite = unittest.TestLoader().loadTestsFromModule(benchmarks)
    response = HttpResponse()
    test_results = unittest.TextTestRunner(
        stream=response, descriptions=True, verbosity=2).run(suite)
    # test_results = HTMLTestRunner(stream=response, verbosity=2).run(suite)
    response.status_code = test_results.wasSuccessful() and 200 or 500
    return response


@staff_member_required
def index(request, template='feedly/index.html'):
    context = RequestContext(request)
    # HACK for django <1.3 beta compatibility
    if 'STATIC_URL' not in context and 'MEDIA_URL' in context:
        context['STATIC_URL'] = context['MEDIA_URL']
    sample_size = int(request.GET.get('sample_size', 1000))
    context['sample_size'] = sample_size
    lucky_users = random.sample(xrange(10 ** 6), sample_size) + [13]
    users_dict = get_user_model().objects.get_cached_users(lucky_users)
    buckets = [0, 24, 1 * 24, 3 * 24, 10 * 24, 30 * 24, 50 * 24, 100 *
               24, 150 * 24, 1000 * 24]
    bucket_dict = dict([(b, 0) for b in buckets])
    count_dict = {}

    # retrieve all the counts in one pipelined request(s)
    with get_redis_connection().map() as redis:
        for user_id in users_dict:
            feed = LoveFeed(user_id, redis=redis)
            count = feed.count()
            count_dict[user_id] = count

    # divide into buckets using bisect left
    for user_id, count in count_dict.items():
        bucket_index = bisect.bisect_left(buckets, count)
        bucket = buckets[bucket_index]
        bucket_dict[bucket] += 1
    bucket_stats = bucket_dict.items()
    bucket_stats.sort(key=lambda x: x[0])
    context['bucket_stats'] = bucket_stats

    return render_to_response(template, context)


@staff_member_required
def monitor(request, template='feedly/monitor.html'):
    context = RequestContext(request)
    # HACK for django <1.3 beta compatibility
    if 'STATIC_URL' not in context and 'MEDIA_URL' in context:
        context['STATIC_URL'] = context['MEDIA_URL']
    sample_size = int(request.GET.get('sample_size', 2))
    lucky_users = random.sample(xrange(10 ** 6), sample_size) + [13]
    users_dict = get_user_model().objects.get_cached_users(lucky_users)

    # retrieve all the counts in one pipelined request(s)
    count_dict = {}
    with get_redis_connection().map() as redis:
        for user_id in users_dict:
            feed = LoveFeed(user_id, redis=redis)
            count = feed.count()
            count_dict[user_id] = count

    for user_id, count in count_dict.items():
        profile = users_dict[user_id].get_profile()
        redis_count = int(count_dict[user_id])
        db_max = redis_count + 10
        db_count = profile._following_loves().count()
        print profile, db_count, long(redis_count)

    return render_to_response(template, context)
