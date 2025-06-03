import fastf1

# Enable caching globally (only once per session)
fastf1.Cache.enable_cache('./.cache')

def load_sessions(year: int, grand_prix: str):
    """
    Loads the qualifying and race sessions for a specific F1 event.

    Parameters:
        year (int): The year of the season.
        grand_prix (str): The Grand Prix name (e.g., "Monaco").

    Returns:
        tuple: (quali_session, race_session) FastF1 session objects.
    """

    quali = fastf1.get_session(year, grand_prix, 'Q')
    quali.load()

    race = fastf1.get_session(year, grand_prix, 'R')
    race.load()
    
    return quali, race
