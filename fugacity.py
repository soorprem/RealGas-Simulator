"""Pure-component fugacity; pressure and fugacity both in bar."""
def fugacity(state):
    return state['phi']*state['P_bar']
