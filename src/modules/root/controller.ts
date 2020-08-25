export const rootController = (fastify, opts, next) => {
	fastify.get('/', async (req, reply) => {
		return reply.sendFile('index.html')
	});

	// fastify.get('/video/:id', (req, reply) => reply.sendFile(`video/${req.params.id}`));

	next()
};
