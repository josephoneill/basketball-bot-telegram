import os
import httpx
from diskcache import Cache
from ..common import cached

class FifaApi():
    def __init__(self):
        self.base_url = 'https://v3.football.api-sports.io'
        self.league = '1'
        self.season = '2026'
        self.cache = Cache('bot-api-cache')
    
    async def _call(self, endpoint, params=None):
        headers = {
            'x-apisports-key': os.getenv('FOOTBALL_API_KEY')
        }

        default_params = {
            'league': self.league,
            'season': self.season
        }

        if params:
            default_params.update(params)

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/{endpoint}", headers=headers, params=default_params)
            return response.json()
        
    @cached('match_schedule')
    async def get_match_schedule(self):
        return await self._call('fixtures')

    @cached('teams')
    async def get_teams(self):
        return await self._call('teams')
    
    async def get_fixtures(self):
        return await self._call('fixtures', {'status': '1H-HT-2H-ET-P-BT-LIVE'})

    async def get_finished_fixtures(self):
        return await self._call('fixtures', {'status': 'FT'})
    
    @cached('standings', 21600)
    async def get_standings(self):
        return await self._call('standings')