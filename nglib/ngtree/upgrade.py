'Upgrade older ngtrees to newer version'
import logging

logger = logging.getLogger(__name__)

def upgrade_ngt_v2(ngt):
    'Upgrade ngt structures to version 2 for the API'

    stack = list()

    # Add dictionary to stack
    stack.append(ngt)

    # upgrade keys on all dictionaries
    for tree in stack:
        # Copy NGT and traverse
        nt = tree.copy()
        for f in nt:
            # Upgrade dictionary key
            tree.pop(f)
            tree[_new_name(f)] = nt[f]

            # Found a nested dict, add to stack
            if isinstance(nt[f], dict):
                stack.append(nt[f])

            # Found a nested list
            elif isinstance(nt[f], list):
                for en in nt[f]:
                    # nested dict in list, add to stack
                    if isinstance(en, dict):
                        stack.append(en)

    return ngt


def _new_name(old):
    'Get new name for fields (lowercase, replace spaces with _)'

    nmap = {
        'StandbyRouter': 'standby_router',
        'SecurityLevel': 'security_level',
        'mgmtgroup': 'mgmt_group'
        }

    if old in nmap:
        return nmap[old]

    old = old.replace(' ', '_')
    old = old.lower()

    if old == 'data':
        old = 'xdata'

    return old
