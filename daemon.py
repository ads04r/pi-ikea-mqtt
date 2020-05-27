#!/usr/bin/python3

import paho.mqtt.client as mqtt
import json, os, sys, time, datetime, pigpio

config_path = os.path.abspath(os.path.dirname(sys.argv[0]) + '/config.json')
if not(os.path.exists(config_path)):
	sys.stderr.write("Cannot find config file " + config_path + "\n")
	sys.exit(1)

def update(config, client, id):

	light = config['lights'][id]
	state = config['states'][id]
	host = ''
	if 'host' in light:
		host = light['host']
	pins = light['pins']

	bri = float(state['bri'])
	onstate = int(state['on'])
	r = int(float(state['r']) * (bri / 255) * onstate)
	g = int(float(state['g']) * (bri / 255) * onstate)
	b = int(float(state['b']) * (bri / 255) * onstate)

	if host == '':
		pi = pigpio.pi()
	else
		pi = pigpio.pi(host)
	pi.set_PWM_dutycycle(pins[0], r)
	pi.set_PWM_dutycycle(pins[1], g)
	pi.set_PWM_dutycycle(pins[2], b)
	pi.stop()

	for topic_id in light['topics'].keys():
		topic = light['topics'][topic_id]
		if topic_id == 'state':
			client.publish(topic, light['payload'][onstate])
		if topic_id == 'bri_state':
			client.publish(topic, state['bri'])
		if topic_id == 'rgb_state':
			rgb_string = str(state['r']) + ',' + str(state['g']) + ',' + str(state['b'])
			client.publish(topic, rgb_string)

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
			if topic_id == 'bri_command':
				config['states'][i]['bri'] = int(payload)
				config['states'][i]['on'] = 1
			if topic_id == 'rgb_command':
				col = payload.split(',')
				if len(col) == 3:
					config['states'][i]['r'] = int(col[0])
					config['states'][i]['g'] = int(col[1])
					config['states'][i]['b'] = int(col[2])
					config['states'][i]['on'] = 1
			if i in updates:
				continue
			updates.append(i)

	for i in updates:
		update(config, client, i)

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

for i in range(0, len(config['states'])):
	update(config, client, i)

while True:
	pass
client.loop_stop()
