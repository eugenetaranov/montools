#!/usr/bin/env python

from json import load, dumps
from urllib import urlopen
from argparse import ArgumentParser


def parseargs():
    p = ArgumentParser()
    p.add_argument('-s', '--server', metavar='RabbitMQ HTTP endpoint', required=False, default='127.0.0.1')
    p.add_argument('--user', required=False, default='guest')
    p.add_argument('--password', required=False, default='guest')
    p.add_argument('--skip', required=False, action='append', default=[])
    p.add_argument('-p', '--port', metavar='RabbitMQ HTTP port', required=False, type=int, default=15672)
    return vars(p.parse_args())


def queues_details(metrics, params):
    try:
        res = urlopen('http://{user}:{password}@{server}:{port}/api/queues'.format(**params))
    except Exception as e:
        exit(2)

    if not res.code == 200:
        print 'Error code %' % res.code
        exit(2)

    else:
        doc = load(res)

    for i in doc:
        if i['name'].startswith(tuple(params['skip'])):
            continue

        metrics['%s.messages' % i['name']] = i['messages']
        metrics['%s.published' % i['name']] = i['message_stats']['publish']
        try:
            metrics['%s.consumers' % i['name']] = i['consumers']
            metrics['%s.delivered' % i['name']] = i['message_stats']['deliver']
            metrics['%s.ack' % i['name']] = i['message_stats']['ack']
            metrics['%s.deliver_rate' % i['name']] = i['message_stats']['deliver_details']['rate']
            metrics['%s.ack_rate' % i['name']] = i['message_stats']['ack_details']['rate']
        except KeyError:
            pass
        metrics['%s.publish_rate' % i['name']] = i['message_stats']['publish_details']['rate']

    return metrics


def channel_details(metrics, params):
    try:
        res = urlopen('http://{user}:{password}@{server}:{port}/api/channels?sort=message_stats.deliver_details.rate&sort_reverse=true&columns=name,message_stats.deliver_details.rate'.format(**params))
    except Exception as e:
        exit(2)

    if not res.code == 200:
        print 'Error code %' % res.code
        exit(2)

    else:
        doc = load(res)

    for i in doc:
        try:
            if i['message_stats']['deliver_details']['rate']:
                metrics['workers_stats.%s.rate' % i['name'].split()[0].split(':')[0].replace('.', '-')] = int(i['message_stats']['deliver_details']['rate'])
        except (TypeError, KeyError):
            continue

    return metrics


def main():
    metrics = {}
    metrics = queues_details(metrics, params)
    metrics = channel_details(metrics, params)
    print dumps(metrics, indent=4)


if __name__ == '__main__':
    params = parseargs()
    main()
