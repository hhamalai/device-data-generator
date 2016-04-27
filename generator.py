import asyncio
import aiohttp
import random
import math

def create_range(avg, width):
    return {
        'min': avg - width/2.0,
        'max': avg + width/2.0,
        'prev': avg
    }


def create_device(temp_avg, temp_range, hum_avg, hum_range, co_avg, co_range,
        co2_avg, co2_range, pressure_avg, pressure_range, motor_avg, motor_range):
    return {
        'temp': create_range(temp_avg, temp_range),
        'humidity': create_range(hum_avg, hum_range),
        'co': create_range(co_avg, co_range),
        'co2': create_range(co2_avg, co2_range),
        'pressure': create_range(pressure_avg, pressure_range),
        'motor': create_range(motor_avg, motor_range)
    }

devices = [create_device(
    20+random.random()*10, 10,
    20+random.random()*10, 10,
    20+random.random()*10, 10,
    20+random.random()*10, 10,
    20+random.random()*10, 10,
    20+random.random()*10, 10,
    ) for _ in range(10)]

def generate_measurements(devices):
    for device in devices:
        for meter in device.values():
            meter['prev'] = min(meter['max'], max(meter['min'], meter['prev'] + 2*math.ceil(0.5-random.random()) -1))
generate_measurements(devices)

host = 'localhost'
ports = [3001 for _ in range(25)]
clients = [{'port': port, 'host': host} for port in ports]

async def do_post(session, port, data):
    with aiohttp.Timeout(10):
        async with session.post('http://localhost:%s' % (port,), data={'data': data}) as response:
            return await response.read()

loop = asyncio.get_event_loop()
with aiohttp.ClientSession(loop=loop) as session:
    i = 0
    while True:
        generate_measurements(devices)
        i = i + 1
        tasks = [
            asyncio.ensure_future(do_post(session, client['port'], devices))
            for client in clients]

        loop.run_until_complete(asyncio.wait(tasks))
        import time
        time.sleep(1)
    loop.close()
