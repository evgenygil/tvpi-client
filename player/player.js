(async () => {
	const {data} = await axios.get('http://0.0.0.0:9090/player/list');

	const player = document.getElementById('player');
	let activeVideo = 0;

	player.addEventListener('ended', () => {
		activeVideo = (++activeVideo) % data.length;

		axios.post('http://0.0.0.0:9090/statistics/query', {media: data[activeVideo]});

		player.src = data[activeVideo];
		player.play();
	});
})();
