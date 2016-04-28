import asyncio
import aiohttp
import random
import math
import argparse
import urllib
import time

def create_range(avg, width):
    return {
        'min': avg - width/2.0,
        'max': avg + width/2.0,
        'prev': avg
    }


def create_device(id, temp_avg, temp_range, hum_avg, hum_range, co_avg, co_range,
        co2_avg, co2_range, pressure_avg, pressure_range, motor_avg, motor_range):
    return {
        'id': id,
        'meters': {
	    'temperature': create_range(temp_avg, temp_range),
	    'humidity': create_range(hum_avg, hum_range),
	    'co': create_range(co_avg, co_range),
	    'co2': create_range(co2_avg, co2_range),
	    'pressure': create_range(pressure_avg, pressure_range),
	    'motor': create_range(motor_avg, motor_range)
        }
    }

devices = [create_device(
    i,
    20+random.random()*10, 10,
    45+random.random()*10, 45,
    1.5+random.random()*2, 2,
    500+random.random()*50, 450,
    1025+random.random()*10, 50,
    50, 100,
    ) for i in range(10)]

def generate_measurements(devices):
    for device in devices:
        for meter in device['meters'].values():
            meter['prev'] = min(meter['max'], max(meter['min'], meter['prev'] + 2*math.ceil(0.5-random.random()) -1))
generate_measurements(devices)

host = 'localhost'
ports = set([8083])
clients = [{'port': port, 'host': host} for port in ports]

async def do_get(session, port):
    with aiohttp.Timeout(5):
        async with session.get("http://%s:%s" % (host, port) + "/query?q=CREATE%20DATABASE%20gofore") as response:
            print(response.status)
            return await response.read()


def generate_message(devices, ts=None):
    rval = []
    if not ts:
        ts = time.time()*1000000000
    for device in devices:
        device_id = device['id']
        for k, v in device['meters'].items():
            rval.append('%s,device_id=%s value=%s %i' % (k, device_id, v['prev'], ts))
    return rval

async def do_post(session, port, devices):
    with aiohttp.Timeout(5):
        post_data = '\n'.join(generate_message(devices))
        print(post_data)
        async with session.post('http://%s:%s/write?db=gofore' % (host, port,),
                data=post_data) as response:
            print(response.status)
            return await response.release()


def create():
    loop = asyncio.get_event_loop()
    with aiohttp.ClientSession(loop=loop) as session:
        tasks = [
                asyncio.ensure_future(do_get(session, client['port']))
            for client in clients]

        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()


def main_loop():
    loop = asyncio.get_event_loop()
    with aiohttp.ClientSession(loop=loop) as session:
        i = 0
        while True:
            generate_measurements(devices)
            i = i + 1
            round_msg = generate_message(devices)
            tasks = [
                asyncio.ensure_future(do_post(session, client['port'], devices))
                for client in clients]

            loop.run_until_complete(asyncio.wait(tasks))
            time.sleep(1)
        loop.close()



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    if args.create:
        create()
    elif args.history:
        generate_history()
    else:
        main_loop()

if __name__ == '__main__':
    main()
