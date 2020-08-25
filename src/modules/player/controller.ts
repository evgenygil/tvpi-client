import {PlayerService} from './service';

export const playerController = (fastify, opts, next) => {
	const playlistService = PlayerService.getInstance();

	fastify.get('/list', async (req, reply) => {
		reply.send(playlistService.getList());
	});

	next()
};
