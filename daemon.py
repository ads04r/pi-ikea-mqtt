#!/usr/bin/python3

import paho.mqtt.client as mqtt
import json, os, sys, time, datetime, pigpio

config_path = os.path.abspath(os.path.dirname(sys.argv[0]) + '/config.json')
if not(os.path.exists(config_path)):
	sys.stderr.write("Cannot find config file " + config_path + "\n")
	sys.exit(1)

def update(config, id):

	light = config['lights'][id]
	state = config['states'][id]
	host = light['host']
	pins = light['pins']

	print(state)

	bri = float(state['bri'])
	onstate = int(state['on'])
	r = int(float(state['r']) * (bri / 255) * onstate)
	g = int(float(state['g']) * (bri / 255) * onstate)
	b = int(float(state['b']) * (bri / 255) * onstate)

	pi = pigpio.pi(host)
	pi.set_PWM_dutycycle(pins[0], r)
	pi.set_PWM_dutycycle(pins[1], g)
	pi.set_PWM_dutycycle(pins[2], b)
	pi.stop()

def callback(client, userdata, message):

	global config

	topic = message.topic
	payload = str(message.payload.decode('utf-8'))
	updates = []
	for i in range(0, len(config['states'])):
		light = config['lights'][i]
		payload_off = light['payload'][0]
		payload_on = light['payload'][1]
		for topic_id in light['topics'].keys():
			if not(topic_id.endswith('command')):
				continue
			topic_path = light['topics'][topic_id]
			if topic != topic_path:
				continue
			if topic_id == 'command':
				if payload == payload_off:
					config['states'][i]['on'] = 0
				if payload == payload_on:
					config['states'][i]['on'] = 1
			if i in updates:
				continue
			updates.append(i)

	for i in updates:
		update(config, i)

with open(config_path) as data:
	config = json.load(data)
	data.close()

config['states'] = []

client = mqtt.Client("pi-ikea-mqtt")
client.on_message = callback
client.connect(config['mqtt']['host'])
client.loop_start()
for light in config['lights']:
	for topic_id in light['topics'].keys():
		if not(topic_id.endswith('command')):
			continue
		topic = light['topics'][topic_id]
		client.subscribe(topic)
	state = {}
	state['r'] = 255
	state['g'] = 255
	state['b'] = 255
	state['on'] = 0
	state['bri'] = 255
	config['states'].append(state)

while True:
	pass
client.loop_stop()
