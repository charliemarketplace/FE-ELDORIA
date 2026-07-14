import re, functools

from app.data.database.database import DB
from app.engine import config as cf

class Parser():
    def __init__(self):
        self.equations = {}
        for equation in DB.equations.values():
            if equation.expression:
                self.equations[equation.nid] = self.tokenize(equation.expression)

        self.replacement_dict = self.create_replacement_dict()

        for nid in list(self.equations.keys()):
            expression = self.equations[nid]
            self.fix(nid, expression, self.replacement_dict)

        # Debug-mode QoL: triple player-team MOVEMENT so QA can traverse
        # maps quickly while ?debug=1 is set. No-op for every other team
        # and a no-op entirely when debug is off. See app/engine/config.py
        # SETTINGS['debug'] (set from the ?debug= URL param in main.py).
        if 'MOVEMENT' in self.equations:
            base_movement_fn = self.equations['MOVEMENT']

            def debug_movement(equations, unit, _base=base_movement_fn):
                base = _base(equations, unit)
                if cf.SETTINGS['debug'] and unit.team == 'player':
                    return base * 3
                return base
            self.equations['MOVEMENT'] = debug_movement

        # Safe-zone QoL: quintuple player-team MOVEMENT while a level has set
        # the game_var 'safe_zone' truthy (event: game_var;safe_zone;1, and
        # game_var;safe_zone;0 before set_next_chapter). Data-driven per-level
        # toggle, independent of debug mode; composes with the patch above.
        if 'MOVEMENT' in self.equations:
            base_movement_fn = self.equations['MOVEMENT']

            def safe_zone_movement(equations, unit, _base=base_movement_fn):
                base = _base(equations, unit)
                from app.engine.game_state import game
                if unit.team == 'player' and game.game_vars.get('safe_zone'):
                    return base * 5
                return base
            self.equations['MOVEMENT'] = safe_zone_movement

        # Now add these equations as local functions
        for nid in self.equations.keys():
            if not nid.startswith('__'):
                setattr(self, nid.lower(), functools.partial(self.equations[nid], self.equations))

    def tokenize(self, s: str) -> str:
        return re.split('([^a-zA-Z_])', s)

    def create_replacement_dict(self):
        dic = {}
        for stat in DB.stats:
            dic[stat.nid] = ("(unit.stats['%s'] + unit.stat_bonus('%s'))" % (stat.nid, stat.nid))
        for nid in self.equations.keys():
            dic[nid] = ("equations['%s'](equations, unit)" % nid)
        return dic

    def fix(self, lhs, rhs, dic):
        rhs = [dic.get(n, n) for n in rhs]
        rhs = ''.join(rhs)
        rhs = 'int(%s)' % rhs
        exec("def %s(equations, unit): return %s" % (lhs, rhs), self.equations)

    def get(self, lhs, unit):
        if lhs in self.equations:
            return self.equations[lhs](self.equations, unit)
        return 0

    def get_expression(self, expr, unit):
        # For one time use
        # Can't seem to be used with any sub equations
        expr = self.tokenize(expr)
        expr = [self.replacement_dict.get(n, n) for n in expr]
        expr = ''.join(expr)
        expr = 'int(%s)' % expr
        equations = self.equations
        return eval(expr)

    def get_mana(self, unit):
        if hasattr(self, 'mana'):
            return self.mana(unit)
        else:
            return 0

    def get_max_fatigue(self, unit):
        if hasattr(self, 'max_fatigue'):
            return self.max_fatigue(unit)
        else:
            return 10

    def get_initiative(self, unit):
        if hasattr(self, 'initiative'):
            return self.initiative(unit)
        else:
            return 0

    def get_max_guard(self, unit):
        if hasattr(self, 'max_guard'):
            return self.max_guard(unit)
        else:
            return 10

    def get_gauge_inc(self, unit):
        if hasattr(self, 'gauge_increase'):
            return self.gauge_increase(unit)
        else:
            return 2

    def get_guard_exp(self, unit):
        if hasattr(self, 'guard_exp'):
            return self.guard_exp(unit)
        else:
            return 10

PARSER = Parser()

def __getattr__(name):
    if name == 'parser':
        return PARSER
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def clear():
    """
    Recreate the parser. Necessary in order to update equations after the user
    updates them in the equation editor
    """
    global PARSER
    PARSER = Parser()
