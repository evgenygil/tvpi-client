import fastify from 'fastify'
import fastifyStatic from 'fastify-static';
import * as path from 'path';
import {open} from 'sqlite';
import sqlite3 from "sqlite3";

import {rootController} from './modules/root/controller';
import {playerController} from './modules/player/controller';
import {statisticsController} from './modules/statistics/controller';

import {
	SERVER_PORT,
	SERVER_ADDRESS
} from './config';

const server = fastify();

server.register(fastifyStatic, {
	root: path.join(`${__dirname}/../player`)
});

server.register(rootController, { prefix: '/' });
server.register(playerController, { prefix: '/player' });
server.register(statisticsController, { prefix: '/statistics' });

server.listen(SERVER_PORT, SERVER_ADDRESS, (err, address) => {
	if(err) {
		console.error(err);
		process.exit(1)
	}
	console.log(`Server listening at ${address}`)
});

/**
 * DB connection instance
 */
export const openDb = () => open({
	filename: `${__dirname}/../db/data.db`,
	driver: sqlite3.Database
});
