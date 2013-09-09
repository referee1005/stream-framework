import pytest
import redis


@pytest.fixture(autouse=True)
def celery_eager():
    from celery import current_app
    current_app.conf.CELERY_ALWAYS_EAGER = True
    current_app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True


@pytest.fixture
def redis_reset():
    redis.Redis().flushall()


@pytest.fixture
def cassandra_reset():
    from feedly.feeds.cassandraCQL import CassandraCQLFeed
    from feedly.feeds.aggregated_feed.cassandraCQL import CassandraAggregatedFeed
    from cqlengine.management import create_table
    aggregated_timeline = CassandraAggregatedFeed.get_timeline_storage()
    timeline = CassandraCQLFeed.get_timeline_storage()
    create_table(aggregated_timeline.model)
    create_table(timeline.model)
