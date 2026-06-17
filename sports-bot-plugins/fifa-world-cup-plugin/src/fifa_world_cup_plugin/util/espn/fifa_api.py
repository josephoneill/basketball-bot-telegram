import os
import httpx
from diskcache import Cache
from ..common import cached

class FifaApi():
    def __init__(self):
        self.base_url = 'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world'
        self.cache = Cache('bot-api-cache')
    
    async def _call(self, endpoint, params=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.espn.com/'
        }

        default_params = {}

        if params:
            default_params.update(params)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/{endpoint}", headers=headers, params=default_params)

            response.raise_for_status()

            return response.json()
        
    @cached('teams')
    async def get_teams(self):
        return await self._call('teams', params={'limit': '50'})
        
    async def get_scoreboard(self, date=None):
        params = {}
        if date:
            params['dates'] = date
        return await self._call('scoreboard', params=params)
    
    async def get_standings(self):
        return await self._call('standings')
    
    async def get_schedule(self, team_id):
        return await self._call(f'teams/{team_id}/schedule')