export class PlayerService {
	private static _instance: PlayerService;

	public static getInstance(): PlayerService {
		if (!PlayerService._instance) {
			PlayerService._instance = new PlayerService();
		}

		return PlayerService._instance;
	}

	public getList() {
		return [
			'video/1_.mp4',
			'video/2_.mp4',
			'video/3_.mp4',
			'video/4_.mp4',
			'video/5_.mp4',
			'video/6_.mp4',
			'video/7_.mp4',
			'video/8_.mp4',
			'video/9_.mp4',
			'video/10_.mp4'
		]
	}
}
