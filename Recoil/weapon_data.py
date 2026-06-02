from Recoil.games.cs2 import CS2Data

class WeaponData:
    @staticmethod
    def get_game_data(game_id):
        """Returns the weapon data class instance for the specified game."""
        try:
            if game_id == 'valorant':
                from Recoil.games.valorant import ValorantData
                return ValorantData()
            elif game_id == 'pubg':
                from Recoil.games.pubg import PUBGData
                return PUBGData()
            elif game_id == 'apex':
                from Recoil.games.apex import ApexLegendsData
                return ApexLegendsData()
            elif game_id == 'cod':
                from Recoil.games.cod import CoDData
                return CoDData()
            elif game_id == 'r6s':
                from Recoil.games.r6s import R6SData
                return R6SData()
            elif game_id == 'warzone':
                from Recoil.games.warzone import WarzoneData
                return WarzoneData()
            elif game_id == 'delta_force':
                from Recoil.games.delta_force import DeltaForceData
                return DeltaForceData()
            elif game_id == 'overwatch':
                from Recoil.games.overwatch import OverwatchData
                return OverwatchData()
            elif game_id == 'the_finals':
                from Recoil.games.the_finals import TheFinalsData
                return TheFinalsData()
            elif game_id == 'battlefield':
                from Recoil.games.battlefield import BattlefieldData
                return BattlefieldData()
            elif game_id == 'rust':
                from Recoil.games.rust import RustData
                return RustData()
        except ImportError:
            pass
        return CS2Data()