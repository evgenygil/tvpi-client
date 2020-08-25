import {openDb} from '../../index';
import * as path from 'path';

export const statisticsController = (fastify, opts, next) => {
	fastify.post('/query', async (req, reply) => {
		const {media} = req.body;

		if (media) {
			const db = await openDb();
			db.run('INSERT INTO stat (name) VALUES (?)', path.basename(media).split('.').shift())
		}

		reply.send('ok');
	});

	next()
};
