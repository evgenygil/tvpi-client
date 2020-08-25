export const rootController = (fastify, opts, next) => {
	fastify.get('/', async (req, reply) => {
		return reply.sendFile('index.html')
	});

	next()
};
