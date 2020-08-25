import fastify from 'fastify'
import fastifyStatic from 'fastify-static';
import * as path from 'path';

import {rootController} from './modules/root/controller';
import {playerController} from './modules/player/controller';
import {statisticsController} from './modules/statistics/controller';

import {SERVER_PORT} from './config';

const server = fastify();

server.register(fastifyStatic, {
	root: path.join(`${__dirname}/../player`)
});

server.register(rootController, { prefix: '/' });
server.register(playerController, { prefix: '/player' });
server.register(statisticsController, { prefix: '/statistics' });

server.listen(SERVER_PORT, '0.0.0.0', (err, address) => {
	if(err) {
		console.error(err);
		process.exit(1)
	}
	console.log(`Server listening at ${address}`)
});
