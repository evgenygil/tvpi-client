export const statisticsController = (fastify, opts, next) => {
	fastify.post('/query', async (req, reply) => {
		const {media} = req.body;

		reply.send(media);
	});

	next()
};
