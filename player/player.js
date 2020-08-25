(async () => {
	const player = document.getElementById('player');

	const {data} = await axios.get('http://0.0.0.0:9090/player/list');

	const playIndex = (index) => {
		player.src = data[index];
		player.play();

		axios.post('http://0.0.0.0:9090/statistics/query', {media: data[activeVideo]});
	};

	let activeVideo = 0;
	playIndex(activeVideo);

	player.addEventListener('ended', () => {
		activeVideo = (++activeVideo) % data.length;
		playIndex(activeVideo);
	});
})();
