from time import sleep
from flask import Flask, render_template
from multiprocessing import Process
import docker
from docker.types import ServiceMode
import redis
import os

app = Flask(__name__)
redisClient = redis.StrictRedis(port=6379, charset="utf-8", decode_responses=True)
client = docker.from_env()

MAX_RESPONSE_TIME = 5
MIN_RESPONSE_TIME = 2

def scale(change: int) -> int:
    try:
        service = client.services.list(filters=dict(name="app_name_web"))[0]
        count = service.attrs['Spec']['Mode']['Replicated']['Replicas']
        new_count = max(1, min(20, count + change))

        toggle = int(redisClient.get('toggle')) > 0
        if toggle and count != new_count:
            service.update(mode=ServiceMode("replicated", replicas=new_count))
            print(f"Scaling to {new_count} containers")
        else:
            print(f"Not scaling: currently {new_count} containers and scaling is {'enabled' if toggle else 'disabled'}")
        return new_count if toggle else count
    except:
        return -1

def loop():
    redisClient.delete('bruhtestlist', 'req_list', 'avg_list', 'replica_list')
    redisClient.set('toggle', 1)
    while True:
        num_requests = 0
        sum_response_time = 0
        
        # get all response times from redis
        response_times = redisClient.lrange('bruhtestlist', 0, -1)
        redisClient.delete('bruhtestlist')
        print(f"Response times: {response_times}")

        # average response times
        num_requests = len(response_times)
        for time in response_times:
            sum_response_time += float(time)
        avg = 0
        if num_requests > 0:
            avg = sum_response_time / num_requests
        print(f"Average response time: {avg}")

        # scale
        change = 0
        if avg > MAX_RESPONSE_TIME:
            change = 4
        elif avg < MIN_RESPONSE_TIME:
            change = -1
        containers = scale(change)
        redisClient.rpush('req_list', num_requests)
        redisClient.rpush('replica_list', containers)
        redisClient.rpush('avg_list', avg)

        sleep(20)

@app.route('/')
def chart():
    req_list = redisClient.lrange('req_list', 0, -1)
    replica_list = redisClient.lrange('replica_list', 0, -1)
    avg_list = redisClient.lrange('avg_list', 0, -1)
    
    req_values = []
    req_max = 0
    for value in req_list:
        req_values.append(int(value))
        req_max = max(int(value), req_max)

    replica_values = []
    replica_max = 0
    for value in replica_list:
        replica_values.append(int(value))
        replica_max = max(int(value), replica_max)

    avg_values = []
    avg_max = 0
    for value in avg_list:
        avg_values.append(float(value))
        avg_max = max(float(value), avg_max)

    labels = range(0, len(replica_values))
    return render_template('charts.html', labels=labels,
        req_title='# Requests vs. Autoscaler Cycle', req_max=req_max, req_values=req_values,
        replica_title='# Replicas vs. Autoscaler Cycle', replica_max=replica_max, replica_values=replica_values,
        avg_title='Avg. Response Time (s) vs. Autoscaler Cycle', avg_max=avg_max, avg_values=avg_values,
    )


@app.route('/clearlogs', methods=['GET'])
def clear():
    redisClient.delete('bruhtestlist', 'req_list', 'avg_list', 'replica_list')
    return "Cleared the graphs"

@app.route('/toggle', methods=['GET'])
def toggle():
    toggle = -1 * int(redisClient.get('toggle'))
    redisClient.set('toggle', toggle)
    if toggle > 0:
        return "Enabled scaling"
    else:
        return "Disabled scaling"


def main():
    p = Process(target=loop)
    p.start()

    # port = int(os.environ.get('PORT', 1337))
    # app.run(debug=True, host='0.0.0.0', port=port)

    app.run(port=1337)
    p.join()


if __name__ == "__main__":
    main()
