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
			'video/1_.webm',
			'video/2_.webm',
			'video/3_.webm',
			'video/4_.webm',
			'video/5_.webm',
			'video/6_.webm',
			'video/7_.webm',
			'video/8_.webm',
			'video/9_.webm',
			'video/10_.webm'
		]
	}
}
